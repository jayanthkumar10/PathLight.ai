import logging
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.services.llm.mcp import LLMClient
from backend.services.engine.prompt_builder import (
    build_summary_agent_prompt,
    build_experience_agent_prompt,
    build_projects_agent_prompt,
    build_dynamic_experience_prompt,
    build_dynamic_projects_prompt
)
from backend.services.engine.template_constants import (
    RESUME_TEMPLATE_HTML,
    MASTER_SKILLS_DICT,
    HARDCODED_ACHIEVEMENTS,
    DYNAMIC_RESUME_HTML
)

logger = logging.getLogger(__name__)

class ResumeGenerator:
    """
    Step 9: Orchestrates the Multi-Agent LLM rewrite calls and JSON template injection.
    """
    def __init__(self):
        self.llm_client = LLMClient()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_agent(self, sys_prompt: str, user_prompt: str, model_preference: str) -> dict:
        raw_output = self.llm_client.generate_text(sys_prompt, user_prompt, model_preference)
        
        # Strip markdown fences if present
        clean_output = raw_output.strip()
        if clean_output.startswith("```json"):
            clean_output = clean_output[7:]
        elif clean_output.startswith("```"):
            clean_output = clean_output[3:]
        if clean_output.endswith("```"):
            clean_output = clean_output[:-3]
            
        clean_output = clean_output.strip()
        try:
            return json.loads(clean_output)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM Agent: {clean_output}")
            raise ValueError(f"LLM Agent did not return valid JSON: {e}")

    def generate_html(self, 
                      raw_resume_text: str,
                      resume_context: dict, 
                      job, 
                      jd_extraction, 
                      gap_analysis, 
                      master_profile=None,
                      model_preference="gemini-1.5-flash",
                      feedback="") -> tuple[str, str]:
        """
        Executes the Multi-Agent pipeline and returns (generated_html, combined_prompts)
        """
        combined_prompts = []
        logger.info(f"Triggering Multi-Agent Pipeline for {job.title} at {job.company}...")

        if not master_profile:
            logger.info("No Master Profile found, using legacy template flow.")
            return self._run_legacy_flow(raw_resume_text, resume_context, job, jd_extraction, gap_analysis, model_preference, combined_prompts)
        
        logger.info("Master Profile found! Using dynamic profile data...")
        return self._run_dynamic_flow(master_profile, resume_context, job, jd_extraction, gap_analysis, model_preference, combined_prompts)

    def _run_legacy_flow(self, raw_resume_text, resume_context, job, jd_extraction, gap_analysis, model_preference, combined_prompts):
        subtitle = f"{job.title} &middot; AI automation &middot; Agentic AI &middot; Conversational AI"
        
        tasks = []
        
        # Professional Summary Agent
        sys_p1, usr_p1 = build_summary_agent_prompt(raw_resume_text, resume_context, job, jd_extraction, gap_analysis)
        combined_prompts.append(sys_p1 + "\n\n" + usr_p1)
        tasks.append(("summary", sys_p1, usr_p1))

        # Technical Skills Agent
        user_skills_str = master_profile.skills.get("hard_skills", "") if master_profile.skills else ""
        sys_p_ts, usr_p_ts = build_technical_skills_agent_prompt(user_skills_str, jd_extraction)
        combined_prompts.append(sys_p_ts + "\n\n" + usr_p_ts)
        tasks.append(("skills", sys_p_ts, usr_p_ts))

        # Experience Bullet Rewriter
        sys_p2, usr_p2 = build_experience_agent_prompt(raw_resume_text, resume_context, job, jd_extraction, gap_analysis)
        combined_prompts.append(sys_p2 + "\n\n" + usr_p2)
        tasks.append(("experience", sys_p2, usr_p2))

        # Project Bullet Points
        sys_p3, usr_p3 = build_projects_agent_prompt(raw_resume_text, resume_context, job, jd_extraction, gap_analysis)
        combined_prompts.append(sys_p3 + "\n\n" + usr_p3)
        tasks.append(("projects", sys_p3, usr_p3))
        
        results = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_key = {executor.submit(self._call_agent, s, u, model_preference): k for k, s, u in tasks}
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                except Exception as exc:
                    logger.error(f"Agent {key} generated an exception: {exc}")
                    results[key] = {}
        
        summary_data = results.get("summary", {})
        ts_data = results.get("skills", {})
        exp_data = results.get("experience", {})
        proj_data = results.get("projects", {})

        technical_skills_html = ""
        for category, skill_list in ts_data.items():
            if isinstance(skill_list, list) and skill_list:
                skills_str = ", ".join(skill_list)
                technical_skills_html += f'<p><span class="bold">{category}:</span> {skills_str}</p>\n                '
            elif isinstance(skill_list, str) and skill_list:
                technical_skills_html += f'<p><span class="bold">{category}:</span> {skill_list}</p>\n                '

        achievements_bullets = HARDCODED_ACHIEVEMENTS

        try:
            html_content = RESUME_TEMPLATE_HTML.format(
                subtitle=subtitle,
                professional_summary=summary_data.get("professional_summary", ""),
                technical_skills=technical_skills_html,
                tcs_role="AI Engineer",
                tcs_bullets=exp_data.get("tcs_bullets", ""),
                project_1_bullets=proj_data.get("project_1_bullets", ""),
                project_2_bullets=proj_data.get("project_2_bullets", ""),
                achievements_bullets=achievements_bullets
            )
            return html_content, "\n\n---\n\n".join(combined_prompts)
        except KeyError as e:
            logger.error(f"Missing key in JSON for format: {e}")
            raise ValueError(f"LLM JSON missing required formatting key: {e}")

    def _run_dynamic_flow(self, master_profile, resume_context, job, jd_extraction, gap_analysis, model_preference, combined_prompts):
        raw_resume_text = f"Contact: {master_profile.contactInfo}\nTitles: {master_profile.targetTitles}\nExperience: {master_profile.workExperience}\nProjects: {master_profile.projects}\nEducation: {master_profile.education}\nAchievements: {master_profile.achievements}\nSkills: {master_profile.skills}"
        
        subtitle = " &middot; ".join([t for t in master_profile.targetTitles if t]) if master_profile.targetTitles else job.title
        
        tasks = []
        
        sys_p1, usr_p1 = build_summary_agent_prompt(raw_resume_text, resume_context, job, jd_extraction, gap_analysis)
        combined_prompts.append(sys_p1 + "\n\n" + usr_p1)
        tasks.append(("summary", sys_p1, usr_p1))
        
        sys_p2, usr_p2 = build_dynamic_experience_prompt(master_profile.workExperience, job, jd_extraction, gap_analysis)
        combined_prompts.append(sys_p2 + "\n\n" + usr_p2)
        tasks.append(("experience", sys_p2, usr_p2))
        
        sys_p3, usr_p3 = build_dynamic_projects_prompt(master_profile.projects, job, jd_extraction, gap_analysis)
        combined_prompts.append(sys_p3 + "\n\n" + usr_p3)
        tasks.append(("projects", sys_p3, usr_p3))
        
        results = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_key = {executor.submit(self._call_agent, s, u, model_preference): k for k, s, u in tasks}
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                except Exception as exc:
                    logger.error(f"Agent {key} generated an exception: {exc}")
                    results[key] = {}
        
        summary_data = results.get("summary", {})
        exp_data = results.get("experience", {})
        proj_data = results.get("projects", {})

        professional_summary_html = f'<section><div class="section-title">Professional Summary</div><p>{summary_data.get("professional_summary", master_profile.contactInfo.get("summary", ""))}</p></section>'

        technical_skills_html = ""
        user_skills_str = master_profile.skills.get("hard_skills", "") if master_profile.skills else ""
        if user_skills_str:
            for line in user_skills_str.split('\n'):
                if ":" in line:
                    category, skills_str = line.split(":", 1)
                    technical_skills_html += f'<p><span class="bold">{category.strip()}:</span> {skills_str.strip()}</p>\n                '
                elif line.strip():
                    technical_skills_html += f'<p>{line.strip()}</p>\n                '
                
        work_experience_html = ""
        if master_profile.workExperience:
            work_experience_html += '<section>\n<div class="section-title">Work Experience</div>\n'
            for idx, exp in enumerate(master_profile.workExperience):
                role_company = f"{exp.get('company', '')} | {exp.get('title', '')}"
                date = exp.get('date', '')
                bullets = exp_data.get(f"exp_{idx}", "")
                if not bullets and exp.get('bullets'):
                    bullets = "".join([f"<li>{b}</li>" for b in exp.get('bullets')])
                
                work_experience_html += f"""
                <div class="flex-container" style="{'margin-top: 15px;' if idx > 0 else ''}">
                    <div class="bold">{role_company}</div>
                    <div class="bold">{date}</div>
                </div>
                <ul>
                    {bullets}
                </ul>
                """
            work_experience_html += '</section>'

        projects_html = ""
        if master_profile.projects:
            projects_html += '<section>\n<div class="section-title">Projects</div>\n'
            for idx, proj in enumerate(master_profile.projects):
                name = proj.get('name', '')
                link = proj.get('link', '')
                tech = proj.get('tech', '')
                bullets = proj_data.get(f"proj_{idx}", "")
                if not bullets and proj.get('bullets'):
                    bullets = "".join([f"<li>{b}</li>" for b in proj.get('bullets')])
                
                link_html = f' - <a href="{link}" class="project-link" target="_blank">[View Project]</a>' if link else ''
                
                projects_html += f"""
                <div class="flex-container" style="{'margin-top: 15px;' if idx > 0 else ''}">
                    <div class="bold">{name}{link_html}</div>
                </div>
                <div class="tech-stack">{tech}</div>
                <ul>
                    {bullets}
                </ul>
                """
            projects_html += '</section>'
            
        education_html = ""
        if master_profile.education:
            education_html += '<section>\n<div class="section-title">Education</div>\n'
            for idx, edu in enumerate(master_profile.education):
                school = edu.get('school', '')
                date = edu.get('date', '')
                degree = edu.get('degree', '')
                cgpa = edu.get('cgpa', '')
                cgpa_html = f"<div>GPA: {cgpa}</div>" if cgpa else ""
                
                education_html += f"""
                <div class="flex-container" style="{'margin-top: 15px;' if idx > 0 else ''}">
                    <div class="bold">{school}</div>
                    <div class="bold">{date}</div>
                </div>
                <div class="flex-container">
                    <div>{degree}</div>
                    {cgpa_html}
                </div>
                """
            education_html += '</section>'
            
        achievements_html = ""
        if master_profile.achievements:
            achievements_html += '<section>\n<div class="section-title">Achievements</div>\n<ul>\n'
            for ach in master_profile.achievements:
                title = ach.get('title', '')
                desc = ach.get('description', '')
                achievements_html += f'<li><span class="bold">{title}:</span> {desc}</li>\n'
            achievements_html += '</ul>\n</section>'

        ci = master_profile.contactInfo
        contact_parts = []
        if ci.get('phone'): contact_parts.append(ci.get('phone'))
        if ci.get('email'): contact_parts.append(f'<a href="mailto:{ci.get("email")}">{ci.get("email")}</a>')
        if ci.get('linkedin'): contact_parts.append(f'<a href="https://{ci.get("linkedin")}" target="_blank">LinkedIn</a>')
        if ci.get('github'): contact_parts.append(f'<a href="https://{ci.get("github")}" target="_blank">GitHub</a>')
        if ci.get('portfolio'): contact_parts.append(f'<a href="https://{ci.get("portfolio")}" target="_blank">Portfolio</a>')
        contact_html = " | ".join(contact_parts)
        name = ci.get("name", "Name")

        html_content = DYNAMIC_RESUME_HTML.replace("{name}", name)\
            .replace("{subtitle}", subtitle)\
            .replace("{contact_html}", contact_html)\
            .replace("{professional_summary_section}", professional_summary_html)\
            .replace("{technical_skills}", technical_skills_html)\
            .replace("{work_experience_section}", work_experience_html)\
            .replace("{projects_section}", projects_html)\
            .replace("{education_section}", education_html)\
            .replace("{achievements_section}", achievements_html)
        
        return html_content, "\n\n---\n\n".join(combined_prompts)
