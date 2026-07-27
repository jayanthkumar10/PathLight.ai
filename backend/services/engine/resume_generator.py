import logging
import json
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.services.llm.mcp import LLMClient
from backend.services.engine.prompt_builder import (
    build_summary_agent_prompt,
    build_dynamic_experience_prompt,
    build_dynamic_projects_prompt
)
from backend.services.engine.template_constants import DYNAMIC_RESUME_HTML

logger = logging.getLogger(__name__)

class ResumeGenerator:
    """
    Provides specific generation methods for LangGraph nodes.
    """
    def __init__(self):
        self.llm_client = LLMClient()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_agent(self, sys_prompt: str, user_prompt: str, model_preference: str) -> dict:
        raw_output = self.llm_client.generate_text(sys_prompt, user_prompt, model_preference)
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

    def generate_summary(self, raw_resume_text, resume_context, job, jd_extraction, gap_analysis, model_pref, feedback=""):
        sys_p, usr_p = build_summary_agent_prompt(raw_resume_text, resume_context, job, jd_extraction, gap_analysis, feedback)
        result = self._call_agent(sys_p, usr_p, model_pref)
        return result, sys_p + "\n\n" + usr_p

    def generate_experience(self, master_profile_exp, job, jd_extraction, gap_analysis, model_pref, feedback=""):
        sys_p, usr_p = build_dynamic_experience_prompt(master_profile_exp, job, jd_extraction, gap_analysis, feedback)
        result = self._call_agent(sys_p, usr_p, model_pref)
        return result, sys_p + "\n\n" + usr_p

    def generate_projects(self, master_profile_proj, job, jd_extraction, gap_analysis, model_pref, feedback=""):
        sys_p, usr_p = build_dynamic_projects_prompt(master_profile_proj, job, jd_extraction, gap_analysis, feedback)
        result = self._call_agent(sys_p, usr_p, model_pref)
        return result, sys_p + "\n\n" + usr_p

    def assemble_html(self, master_profile, job, summary_data, exp_data, proj_data):
        subtitle = " &middot; ".join([t for t in master_profile.targetTitles if t]) if master_profile.targetTitles else job.title
        
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
        
        return html_content
