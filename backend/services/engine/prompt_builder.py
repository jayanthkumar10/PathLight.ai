import json

def build_summary_agent_prompt(
    raw_resume_text: str,
    resume_context: dict,
    job,
    jd_extraction,
    gap_analysis,
    ats_feedback: str = ""
) -> tuple[str, str]:
    """
    Agent 2: Professional Summary Agent.
    Generates the professional summary paragraph.
    """
    system_prompt = """You are an expert Professional Summary Tailoring Agent.
Your ONLY job is to write a single paragraph (approx. 4-5 sentences) summarizing the candidate's professional background.

CRITICAL INSTRUCTIONS FOR RESUME WRITING:
1. VOICE AND TONE: Write in the implicit first person (resume style). Do NOT use first-person pronouns like "I", "me", or "my". Do NOT use third-person pronouns like "he", "his", "she", or "they". Do NOT mention the candidate's name. Example of correct tone: "Results-driven AI Engineer with 2 years of experience..."
2. FACTUAL ACCURACY: You MUST use the exact years of experience provided in the Candidate Context. NEVER hallucinate or exaggerate years of experience. Do not invent roles or companies.
3. TAILORING: You MUST use the MOST weighted technical skills (top 2), 2 action verbs, and 1 soft skill extracted from the JD to demonstrate value to the target organization.
4. Format the output as a strict JSON object with a single key "professional_summary". Do NOT output markdown code blocks.
"""
    
    yoe = resume_context.get('years_of_experience', "the candidate's actual years of experience based on the resume")
    
    user_prompt = f"""
## TARGET JOB
Title: {job.title}
Company: {job.company}

## JOB DESCRIPTION INTELLIGENCE (Use Top 2 Tech Skills, 2 Action Verbs, 1 Soft Skill)
{jd_extraction.model_dump_json(indent=2)}

## CANDIDATE CONTEXT
Candidate's exact Years of Experience: {yoe}

## RAW RESUME DATA (Source of Truth)
{raw_resume_text}

{"## CRITIQUE FROM PREVIOUS RUN (MUST FIX):" + chr(10) + ats_feedback + chr(10) if ats_feedback else ""}
Output ONLY the raw JSON object:
{{
  "professional_summary": "..."
}}
"""
    return system_prompt, user_prompt



def build_technical_skills_agent_prompt(
    master_skills_str: str,
    jd_extraction,
    ats_feedback: str = ""
) -> tuple[str, str]:
    """
    Agent X: Technical Skills Filter & Ordering Agent.
    Categorizes and reorders raw master skills based on JD relevance.
    """
    system_prompt = """You are an expert ATS Technical Skills Optimizer Agent.
Your ONLY job is to take the candidate's exact raw Master Skills text and format it into a structured dictionary of sensible categories, ordered so the skills most relevant to the target job appear FIRST.

CRITICAL RULES & STRICT CONSTRAINTS:
1. You may drop completely irrelevant skills if the list is too long.
2. YOU ARE MATHEMATICALLY FORBIDDEN FROM ADDING ANY SKILL THAT IS NOT IN THE MASTER SKILLS TEXT. If the JD asks for 'Ruby on Rails' and it's not in the candidate's raw skills, DO NOT add it.
3. Group the skills into sensible categories like "Languages", "Frameworks", "Tools", etc.
4. Format output as a strict JSON object where keys are categories and values are arrays of strings. Do NOT output markdown code blocks.
"""
    user_prompt = f"""
## JOB DESCRIPTION INTELLIGENCE (Target Skills)
{jd_extraction.model_dump_json(indent=2)}

## CANDIDATE MASTER SKILLS (Source of Truth - DO NOT ADD TO THIS)
{master_skills_str}

{"## CRITIQUE FROM PREVIOUS RUN (MUST FIX):" + chr(10) + ats_feedback + chr(10) if ats_feedback else ""}
Output ONLY the raw JSON object representing the categorized skills:
{{
  "Languages": ["..."],
  "Frameworks": ["..."]
}}
"""
    return system_prompt, user_prompt


def build_dynamic_experience_prompt(
    master_profile_exp: list,
    job,
    jd_extraction,
    gap_analysis,
    ats_feedback: str = ""
) -> tuple[str, str]:
    """
    Dynamic Experience Bullet Rewriter.
    Iterates over the MasterProfile work experience length.
    """
    system_prompt = """You are an expert Resume Bullet Rewriter Agent.
Your ONLY job is to rewrite the bullet points for ALL provided work experiences to match the target job description.

CRITICAL RULES:
1. Generate EXACTLY 3 bullet points for EACH work experience provided.
2. PIVOT THE DESCRIPTION: Analyze the Target Job Title and JD. Emphasize the aspects of the candidate's past work that align best.
3. STRICT CONSTRAINT: Do NOT fabricate facts. Keep the original context and scope.
4. Format output as a strict JSON object mapping the experience index (e.g. "exp_0", "exp_1") to a single string of HTML <li> elements. Do NOT output markdown code blocks.
"""
    user_prompt = f"""
## TARGET JOB
Title: {job.title}
Company: {job.company}

## JOB DESCRIPTION INTELLIGENCE
{jd_extraction.model_dump_json(indent=2)}

## RAW EXPERIENCES (Source of Truth)
{json.dumps(master_profile_exp, indent=2)}

{"## CRITIQUE FROM PREVIOUS RUN (MUST FIX):" + chr(10) + ats_feedback + chr(10) if ats_feedback else ""}
Output ONLY the raw JSON object formatted exactly like this:
{{
  "exp_0": "<li>...</li><li>...</li><li>...</li>",
  "exp_1": "<li>...</li><li>...</li><li>...</li>"
}}
"""
    return system_prompt, user_prompt


def build_dynamic_projects_prompt(
    master_profile_proj: list,
    job,
    jd_extraction,
    gap_analysis,
    ats_feedback: str = ""
) -> tuple[str, str]:
    """
    Dynamic Project Bullet Rewriter.
    Iterates over the MasterProfile projects length.
    """
    system_prompt = """You are an expert Project Bullet Rewriter Agent.
Your ONLY job is to rewrite the bullet points for ALL provided projects.

CRITICAL RULES:
1. Generate EXACTLY 3 bullet points for EACH project provided.
2. PIVOT THE DESCRIPTION: Emphasize the technical architecture or business value relevant to the JD.
3. STRICT CONSTRAINT: Do NOT fabricate original facts.
4. Format output as a strict JSON object mapping the project index (e.g. "proj_0", "proj_1") to a single string of HTML <li> elements. Do NOT output markdown code blocks.
"""
    user_prompt = f"""
## TARGET JOB
Title: {job.title}
Company: {job.company}

## JOB DESCRIPTION INTELLIGENCE
{jd_extraction.model_dump_json(indent=2)}

## RAW PROJECTS (Source of Truth)
{json.dumps(master_profile_proj, indent=2)}

{"## CRITIQUE FROM PREVIOUS RUN (MUST FIX):" + chr(10) + ats_feedback + chr(10) if ats_feedback else ""}
Output ONLY the raw JSON object formatted exactly like this:
{{
  "proj_0": "<li>...</li><li>...</li><li>...</li>",
  "proj_1": "<li>...</li><li>...</li><li>...</li>"
}}
"""
    return system_prompt, user_prompt
