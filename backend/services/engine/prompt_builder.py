import json

def build_rewrite_prompt(
    raw_resume_text: str,
    resume_context: dict, 
    job,
    jd_extraction,
    gap_analysis,
    feedback_from_previous_attempt: str = ""
) -> tuple[str, str]:
    """
    Constructs the system and user prompt for the LLM to return JSON.
    """
    system_prompt = """You are an expert ATS Resume Tailoring Engine.
Your ONLY job is to take the provided candidate context and JD gap analysis, and generate a strict JSON object containing the optimized resume content.

CRITICAL GUARDRAILS (NO HALLUCINATIONS):
- NEVER fabricate, invent, or hallucinate any skills, experiences, past job titles, project details, metrics, or ownership.
- Every bullet must be derived STRICTLY from the actual project and experience context.
- Prioritize factual correctness over ATS optimization.
- Do NOT output markdown asterisks (**) for bolding text. Do not output markdown code blocks or wrapper text.

CRITICAL INSTRUCTION: You MUST output a valid JSON object matching EXACTLY the schema below. Do not drop any keys.

JSON SCHEMA:
{
  "subtitle": "Target Job Title | Relevant Title 2 | Relevant Title 3",
  "professional_summary": "Expertly crafted summary incorporating JD keywords...",
  "technical_skills": "<p><span class=\\"bold\\">Languages & Core Tech:</span> Python...</p>...",
  "tcs_role": "AI Engineer",
  "tcs_bullets": "<li>[Action Verb] [Task] [Technology/Skill] [Business/Technical Impact]</li><li>...</li><li>...</li>",
  "project_1_bullets": "<li>...</li><li>...</li><li>...</li>",
  "project_2_bullets": "<li>...</li><li>...</li><li>...</li>",
  "achievements_bullets": "<li><span class=\\"bold\\">Published Patent: ...</span> ...</li><li><span class=\\"bold\\">Spot Award (TCS):</span> ...</li>"
}

STRICT INJECTION RULES:
1. Subtitle: Swap "AI Engineer | AI Automation..." with the TARGET JOB TITLE, and keep the next two relevant titles according to the job title.
2. Professional Summary: Extract the top 1-3 highest-weighted keywords from the JD and inject them. ONLY include them if they already exist somewhere in the resume/project data. The summary should immediately communicate years of experience, specialization, strongest technical strengths, and business impact. Keep it clean and recruiter-friendly.
3. Technical Skills: Rank all available skills by JD relevance and ATS weight. Select ONLY the most important skills required for the target role. Remove unrelated or low-value skills. Ensure it looks curated, not keyword-dumped. Output HTML <p> tags with <span class="bold">Categories:</span>.
4. Work Experience (TCS): Represents a basic RAG application. Generate EXACTLY 3 bullet points. No fabrication. No change in project scope. Rewrite each bullet to improve ATS optimization, readability, technical clarity, and action-oriented language. Format: Action Verb -> Task -> Technology/Skill -> Impact. Output as HTML <li> elements.
5. Projects (AI Job Hunt): Treat as CURRENT project. Exactly 3 bullet points. Format: Action Verb -> Task -> Technology/Skill -> Impact. Do not force metrics if none exist. Output as HTML <li> elements.
6. Projects (PulseOpsAI): Extract from context. Exactly 3 bullet points. Format: Action Verb -> Task -> Technology/Skill -> Impact. Output as HTML <li> elements.
7. Education is IMMUTABLE. Do not generate fields for it.
8. Achievements: Do not change factual content or original accomplishment. You may improve sentence structure, insert stronger action verbs, and naturally incorporate relevant hard/soft skills. Output as HTML <li> elements. YOU MUST INCLUDE THIS FIELD.

FORMATTING RULE: Do NOT use markdown asterisks (**) or underscores (__) inside the JSON values. If you need bold text, use HTML <span class="bold">text</span> or <b>text</b> instead.

Output ONLY the raw JSON object. No markdown formatting.
"""

    if feedback_from_previous_attempt:
        system_prompt += f"\nCRITICAL PREVIOUS FAILURE FEEDBACK:\n{feedback_from_previous_attempt}\nYou MUST fix these issues in this attempt."

    user_prompt = f"""
## TARGET JOB
Title: {job.title}
Company: {job.company}

## JOB DESCRIPTION INTELLIGENCE
{jd_extraction.model_dump_json(indent=2)}

## RAW RESUME DATA (Source of Truth)
{raw_resume_text}

## GAP ANALYSIS (Crucial - Inject Missing Items Smartly!)
Missing Hard Skills: {', '.join(gap_analysis.missing_hard_skills)}
Missing Soft Skills: {', '.join(gap_analysis.missing_soft_skills)}
Missing Tech Skills: {', '.join(gap_analysis.missing_technical_skills)}
Missing Action Verbs: {', '.join(gap_analysis.missing_action_verbs)}

Output the fully optimized JSON now:
"""

    return system_prompt, user_prompt
