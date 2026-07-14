import json

def build_summary_agent_prompt(
    raw_resume_text: str,
    resume_context: dict,
    job,
    jd_extraction,
    gap_analysis
) -> tuple[str, str]:
    """
    Agent 2: Professional Summary Agent.
    Generates the professional summary paragraph.
    """
    system_prompt = """You are an expert Professional Summary Tailoring Agent.
Your ONLY job is to write a single paragraph (approx. 4-6 sentences) summarizing the candidate's professional background.

CRITICAL INSTRUCTION:
1. You MUST use the MOST weighted technical skills (top 2), 2 action verbs, and 1 soft skill extracted from the JD.
2. The summary must be tailored to align PERFECTLY with the JD, showing what value the candidate brings to that exact organization.
3. It must impress a human recruiter.
4. STRICT CONSTRAINT: Do NOT change the original meaning or invent experience the candidate does not have.
5. Format the output as a strict JSON object with a single key "professional_summary". Do NOT output markdown code blocks.
"""
    user_prompt = f"""
## TARGET JOB
Title: {job.title}
Company: {job.company}

## JOB DESCRIPTION INTELLIGENCE (Use Top 2 Tech Skills, 2 Action Verbs, 1 Soft Skill)
{jd_extraction.model_dump_json(indent=2)}

## RAW RESUME DATA (Source of Truth)
{raw_resume_text}

Output ONLY the raw JSON object:
{{
  "professional_summary": "..."
}}
"""
    return system_prompt, user_prompt


def build_experience_agent_prompt(
    raw_resume_text: str,
    resume_context: dict,
    job,
    jd_extraction,
    gap_analysis
) -> tuple[str, str]:
    """
    Agent 4: Experience Bullet Rewriter Agent.
    Generates exactly 3 bullets for the TCS role.
    """
    system_prompt = """You are an expert Experience Bullet Rewriter Agent.
Your ONLY job is to rewrite the Tata Consultancy Services (TCS) experience bullet points.

CRITICAL RULES:
1. Generate EXACTLY 3 bullet points.
2. Bullet 1 must be VALUE-based (align closely with the JD values).
3. Bullet 2 must focus on IMPACT and METRICS to impress a human recruiter.
4. Bullet 3 must imply SOFT SKILLS (team skills, collaboration, leadership, etc.).
5. Take action verbs and soft skills from the JD intelligence to weave into the bullets naturally.
6. STRICT CONSTRAINT: Do NOT fabricate or hallucinate the original context, scope, or facts.
7. Format as HTML <li> elements inside a strict JSON object. Do NOT output markdown code blocks.
"""
    user_prompt = f"""
## TARGET JOB
Title: {job.title}
Company: {job.company}

## JOB DESCRIPTION INTELLIGENCE
{jd_extraction.model_dump_json(indent=2)}

## RAW RESUME DATA (Source of Truth)
{raw_resume_text}

Output ONLY the raw JSON object:
{{
  "tcs_bullets": "<li>...</li><li>...</li><li>...</li>"
}}
"""
    return system_prompt, user_prompt


def build_projects_agent_prompt(
    raw_resume_text: str,
    resume_context: dict,
    job,
    jd_extraction,
    gap_analysis
) -> tuple[str, str]:
    """
    Agent 5: Project Bullet Points Agent.
    Generates 3 bullets for Project 1 and 3 bullets for Project 2.
    """
    system_prompt = """You are an expert Project Bullet Rewriter Agent.
Your ONLY job is to rewrite the bullet points for two projects: 
Project 1 (Autonomous AI Job Hunter Agent) and Project 2 (Enterprise AIOps Co-Pilot).

CRITICAL RULES:
1. Generate EXACTLY 3 bullet points for Project 1 and EXACTLY 3 bullet points for Project 2.
2. PIVOT THE DESCRIPTION: Analyze the Target Job Title. If it is a generic Software Engineering/Backend role, emphasize the Backend architectures, APIs, Data Pipelines, and CI/CD of these projects. If it is an AI/ML role, emphasize LangGraph, RAG, and Agent orchestration.
3. STRICT CONSTRAINT: Do NOT fabricate the original facts or invent new features.
4. Format as HTML <li> elements inside a strict JSON object. Do NOT output markdown code blocks.
"""
    user_prompt = f"""
## TARGET JOB
Title: {job.title}
Company: {job.company}

## JOB DESCRIPTION INTELLIGENCE
{jd_extraction.model_dump_json(indent=2)}

## RAW RESUME DATA (Source of Truth)
{raw_resume_text}

Output ONLY the raw JSON object:
{{
  "project_1_bullets": "<li>...</li><li>...</li><li>...</li>",
  "project_2_bullets": "<li>...</li><li>...</li><li>...</li>"
}}
"""
    return system_prompt, user_prompt


def build_technical_skills_agent_prompt(
    master_skills_str: str,
    jd_extraction
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
    gap_analysis
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
    gap_analysis
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

Output ONLY the raw JSON object formatted exactly like this:
{{
  "proj_0": "<li>...</li><li>...</li><li>...</li>",
  "proj_1": "<li>...</li><li>...</li><li>...</li>"
}}
"""
    return system_prompt, user_prompt
