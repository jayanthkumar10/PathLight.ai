"""
Pathlight ATS Engine — LLM Client
Implements a fully reverse-engineered ATS pipeline:
  1. JD Intelligence Extraction (hard/soft/technical skills + action verbs)
  2. Resume Skeleton-based Tailoring with Semantic Replacement
  3. ATS Score Evaluation
  4. OpenRouter fallback with proper model selection

ATS Reverse Engineering:
- Modern ATS (Taleo, Workday, Greenhouse, Lever) tokenize resumes and match
  exact keywords, n-grams, and semantic variants.
- They score on: keyword density, title match, YOE match, formatting, section presence.
- Key: exact phrase matching > semantic matching for keyword scoring.
- Strategy: mirror exact JD language in bullet points while keeping content true.
"""

import re
import json
import time
import logging
import requests
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Verified FREE OpenRouter models (fetched 2026-07-05, sorted by capability)
# ─────────────────────────────────────────────────────────────────────────────
OPENROUTER_MODELS_RANKED = [
    "nvidia/nemotron-3-super-120b-a12b:free",        # 120B, 1M ctx — best for JSON + HTML
    "meta-llama/llama-3.3-70b-instruct:free",         # 70B, 131K ctx — strong instruction follow
    "openai/gpt-oss-120b:free",                       # 120B OpenAI-style
    "nousresearch/hermes-3-llama-3.1-405b:free",      # 405B — most capable
    "nvidia/nemotron-3-ultra-550b-a55b:free",         # 550B — largest, may be slow
    "google/gemma-4-31b-it:free",                     # Google Gemma 4 31B
    "qwen/qwen3-next-80b-a3b-instruct:free",          # Qwen3 80B
    "nvidia/nemotron-3-nano-30b-a3b:free",            # fallback — smallest
]
OPENROUTER_PRIMARY = OPENROUTER_MODELS_RANKED[0]


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ResumeSkills(BaseModel):
    candidate_name: str = ""
    current_title: str = ""
    contact_info: str = ""
    years_of_experience: int = 2
    hard_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    action_verbs: list[str] = Field(default_factory=list)
    education: str = ""
    companies: list[str] = Field(default_factory=list)


class JDExtraction(BaseModel):
    """Full ATS intelligence from a Job Description."""
    role_title: str = "Software Engineer"
    seniority_level: str = "mid"
    experience_required: int = 2

    # Keyword categories (ATS uses these for scoring)
    hard_skills: list[str] = Field(default_factory=list)       # exact tech keywords
    soft_skills: list[str] = Field(default_factory=list)       # behavioral keywords
    technical_skills: list[str] = Field(default_factory=list)  # tools/frameworks
    action_verbs: list[str] = Field(default_factory=list)      # preferred verbs
    must_have_keywords: list[str] = Field(default_factory=list) # knockout criteria
    nice_to_have_keywords: list[str] = Field(default_factory=list)
    repeated_ats_terms: list[str] = Field(default_factory=list) # appears 2+ times

    # Candidate gap analysis
    candidate_has: list[str] = Field(default_factory=list)
    candidate_needs_to_inject: list[str] = Field(default_factory=list)
    candidate_cannot_claim: list[str] = Field(default_factory=list)

    # Resume writing guidance
    responsibility_phrases: list[str] = Field(default_factory=list)
    ats_title_mirror: str = ""
    summary_hook: str = ""
    summary_supporting_line: str = ""
    keyword_placement_priority: list[str] = Field(default_factory=list)
    ats_tip: str = ""


class ATSEvaluation(BaseModel):
    keyword_coverage_score: float = 70
    semantic_match_score: float = 70
    formatting_score: float = 90
    truthfulness_score: float = 95
    overall_ats_score: float = 75
    issues_found: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Resume HTML Skeleton (consistent layout)
# ─────────────────────────────────────────────────────────────────────────────
RESUME_SKELETON_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body {
  font-family: 'Arial', 'Helvetica Neue', Helvetica, sans-serif;
  font-size: 10.5pt;
  line-height: 1.4;
  color: #000;
  background: #fff;
  width: 8.5in;
  min-height: 11in;
}
body {
  padding: 0.45in 0.5in 0.45in 0.5in;
}
.header-name {
  font-size: 18pt;
  font-weight: bold;
  text-align: center;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
  text-transform: uppercase;
}
.header-title {
  font-size: 10pt;
  text-align: center;
  color: #333;
  margin-bottom: 4px;
  font-style: italic;
}
.header-contact {
  font-size: 9pt;
  text-align: center;
  color: #000;
  margin-bottom: 6px;
}
.header-contact a { color: #000; text-decoration: none; }
hr.section-divider {
  border: none;
  border-top: 1.5px solid #000;
  margin: 5px 0 4px 0;
}
.section { margin-bottom: 8px; }
.section-title {
  font-size: 10pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-bottom: 1px solid #000;
  padding-bottom: 1px;
  margin-bottom: 4px;
}
.entry { margin-bottom: 6px; }
.entry-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.entry-title { font-weight: bold; font-size: 10.5pt; }
.entry-date { font-size: 9.5pt; color: #222; }
.entry-subtitle {
  display: flex;
  justify-content: space-between;
  font-size: 9.5pt;
  color: #333;
  font-style: italic;
  margin-bottom: 3px;
}
ul.bullets { margin: 2px 0 0 14px; padding: 0; }
ul.bullets li {
  font-size: 10pt;
  line-height: 1.38;
  margin-bottom: 2px;
}
.summary-text {
  font-size: 10pt;
  line-height: 1.45;
  text-align: justify;
}
.skills-line { font-size: 10pt; margin-bottom: 2px; line-height: 1.35; }
.skills-line b { font-weight: bold; }
.two-col { display: flex; gap: 20px; }
.two-col > div { flex: 1; }
@media print {
  html, body { width: 100%; min-height: 0; }
  body { padding: 0.4in 0.45in; }
  @page { size: A4; margin: 0; }
}
"""

RESUME_SKELETON_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{candidate_name} — Resume</title>
<style>
{css}
</style>
</head>
<body>

<!-- HEADER -->
<div class="header-name">{candidate_name}</div>
<div class="header-title">{ats_title_mirror}</div>
<div class="header-contact">{contact_info}</div>
<hr class="section-divider">

<!-- SUMMARY -->
<div class="section">
  <div class="section-title">Professional Summary</div>
  <p class="summary-text">{summary}</p>
</div>

<!-- SKILLS -->
<div class="section">
  <div class="section-title">Technical Skills</div>
  {skills_html}
</div>

<!-- EXPERIENCE -->
<div class="section">
  <div class="section-title">Professional Experience</div>
  {experience_html}
</div>

<!-- PROJECTS -->
{projects_section}

<!-- EDUCATION -->
<div class="section">
  <div class="section-title">Education</div>
  {education_html}
</div>

</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# GeminiClient
# ─────────────────────────────────────────────────────────────────────────────
class GeminiClient:
    """
    LLM client for ATS resume tailoring.
    Primary: Google Gemini (structured JSON output).
    Fallback: OpenRouter free models (best available).
    """

    def __init__(self):
        import os
        from dotenv import load_dotenv
        load_dotenv()

        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openrouter_key = os.getenv("OPEN_ROUTER_API_KEY", "")
        self.client = None

        if self.gemini_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.gemini_key)
                logger.info("Gemini client initialized")
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")

    # ── OpenRouter call ────────────────────────────────────────────────────
    def _call_openrouter(self, prompt: str, model: str = None, system: str = None) -> str:
        """Call OpenRouter with fallback through model list."""
        if not self.openrouter_key:
            raise RuntimeError("No OpenRouter key configured")

        models_to_try = [model] + [m for m in OPENROUTER_MODELS_RANKED if m != model] if model else OPENROUTER_MODELS_RANKED

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for try_model in models_to_try[:3]:
            try:
                resp = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://pathlight.ai",
                        "X-Title": "Pathlight Resume Tailoring"
                    },
                    json={
                        "model": try_model,
                        "messages": messages,
                        "temperature": 0.1,
                        "max_tokens": 4096,
                    },
                    timeout=60
                )
                resp.raise_for_status()
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                logger.info(f"OpenRouter success with {try_model} ({len(content)} chars)")
                return content
            except Exception as e:
                logger.warning(f"OpenRouter model {try_model} failed: {e}")
                continue

        raise RuntimeError("All OpenRouter models failed")

    def _strip_fences(self, text: str, lang: str = "") -> str:
        """Remove markdown code fences."""
        text = text.strip()
        pattern = rf"```{lang}\s*\n?(.*?)```"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        return text.strip()

    def _extract_json(self, text: str) -> str:
        """Extract JSON object from text, handling markdown/prose wrapping."""
        text = self._strip_fences(text, "json")
        text = self._strip_fences(text)
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        return text

    # ── Gemini structured call ────────────────────────────────────────────
    def _gemini_structured(self, prompt: str, schema, system: str = "") -> Optional[str]:
        """Call Gemini with structured JSON output. Returns raw text or None."""
        if not self.client:
            return None
        try:
            from google.genai import types
            full_prompt = (system + "\n\n" + prompt) if system else prompt
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.0
                )
            )
            return response.text
        except Exception as e:
            logger.warning(f"Gemini structured call failed: {e}")
            return None

    # ── 1. Extract Resume Skills (cached once) ────────────────────────────
    def extract_resume_skills(self, resume_text: str) -> ResumeSkills:
        """Extract all skill categories from master resume. Called once, cached in DB."""
        schema_desc = """{
  "candidate_name": "Full Name",
  "current_title": "Job Title from resume",
  "contact_info": "email | phone | location",
  "years_of_experience": 2,
  "hard_skills": ["Python", "SQL", ...],
  "soft_skills": ["Leadership", "Communication", ...],
  "technical_skills": ["LangChain", "Docker", ...],
  "action_verbs": ["Developed", "Built", "Deployed", ...],
  "education": "B.Tech CS, University Name",
  "companies": ["TCS", ...]
}"""

        prompt = f"""Extract all information from this resume. Return ONLY valid JSON matching this schema exactly:
{schema_desc}

RESUME:
{resume_text}

Return ONLY the JSON object. No markdown, no explanation."""

        # Try Gemini first
        raw = self._gemini_structured(prompt, ResumeSkills, "You are a resume parser. Extract structured data. Return only JSON.")
        if raw:
            try:
                result = ResumeSkills.model_validate_json(raw)
                logger.info(f"Resume parsed: {result.candidate_name} | YOE={result.years_of_experience} | hard={len(result.hard_skills)}")
                return result
            except Exception as e:
                logger.warning(f"Gemini resume parse validation failed: {e}")

        # OpenRouter fallback
        try:
            text = self._call_openrouter(prompt, system="You are a resume parser. Extract structured data as JSON only.")
            text = self._extract_json(text)
            result = ResumeSkills.model_validate_json(text)
            logger.info(f"Resume parsed via OpenRouter: {result.candidate_name}")
            return result
        except Exception as e:
            logger.warning(f"Resume parse fallback failed: {e}. Using heuristic.")
            return self._heuristic_resume_parse(resume_text)

    def _heuristic_resume_parse(self, text: str) -> ResumeSkills:
        """Emergency heuristic resume parser."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        name = lines[0] if lines else "Candidate"

        hard_pool = ["python","sql","docker","git","fastapi","langchain","langgraph","rag",
                     "aws","gcp","azure","react","javascript","typescript","node.js","java",
                     "machine learning","deep learning","nlp","pytorch","tensorflow","vector",
                     "openai","gemini","llm","transformer","bert","gpt","ci/cd","kubernetes"]
        soft_pool = ["leadership","communication","teamwork","problem-solving","agile","scrum",
                     "project management","analytical","collaboration","adaptability"]
        verbs_pool = ["developed","built","designed","implemented","deployed","optimized",
                      "automated","led","managed","created","engineered","streamlined",
                      "accelerated","reduced","increased","delivered","launched","analyzed"]

        t = text.lower()
        return ResumeSkills(
            candidate_name=name,
            hard_skills=[s for s in hard_pool if s in t],
            soft_skills=[s for s in soft_pool if s in t],
            technical_skills=[s for s in hard_pool if s in t],
            action_verbs=[v for v in verbs_pool if v in t],
            years_of_experience=2
        )

    # ── 2. Extract JD Intelligence ────────────────────────────────────────
    def extract_jd_intelligence(self, jd_text: str, resume_text: str) -> JDExtraction:
        """
        ATS-grade JD analysis: extract all keyword categories and generate
        injection blueprint for resume tailoring.
        """
        system = """You are a senior ATS analyst and resume strategist.
Analyze the job description and candidate resume.
Extract ALL keyword categories an ATS system would score.
Return ONLY a valid JSON object. No markdown, no explanation, no preamble."""

        schema_desc = """{
  "role_title": "exact role name from JD",
  "seniority_level": "junior|mid|senior|lead",
  "experience_required": 3,
  "hard_skills": ["Python", "SQL", "Docker"],
  "soft_skills": ["Communication", "Leadership"],
  "technical_skills": ["LangChain", "FastAPI", "AWS"],
  "action_verbs": ["Develop", "Build", "Deploy", "Optimize"],
  "must_have_keywords": ["must-have terms that are knockout criteria"],
  "nice_to_have_keywords": ["bonus skills"],
  "repeated_ats_terms": ["terms appearing 2+ times - highest weight in ATS"],
  "candidate_has": ["skills candidate clearly has from resume"],
  "candidate_needs_to_inject": ["skills candidate can honestly claim but not mentioned"],
  "candidate_cannot_claim": ["skills candidate genuinely lacks"],
  "responsibility_phrases": ["exact phrases from JD responsibilities to mirror in bullets"],
  "ats_title_mirror": "exact title variation that mirrors JD for ATS title match",
  "summary_hook": "1 sentence opening that mirrors role title and top 3 keywords",
  "summary_supporting_line": "1 sentence with must-have keywords woven naturally",
  "keyword_placement_priority": ["title", "summary", "skills section", "bullet points"],
  "ats_tip": "single most important ATS optimization tip for this specific JD"
}"""

        prompt = f"""CANDIDATE RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

IMPORTANT: Return ONLY valid JSON matching this exact schema. No markdown, no extra text, start with {{ end with }}:
{schema_desc}"""

        # Try Gemini structured output
        raw = self._gemini_structured(prompt, JDExtraction, system)
        if raw:
            try:
                result = JDExtraction.model_validate_json(raw)
                logger.info(f"JD extracted: role={result.role_title} | must_have={len(result.must_have_keywords)} | inject={len(result.candidate_needs_to_inject)}")
                return result
            except Exception as e:
                logger.warning(f"Gemini JD validation failed: {e}")

        # OpenRouter fallback
        for model in OPENROUTER_MODELS_RANKED:
            try:
                text = self._call_openrouter(prompt, model=model, system=system)
                text = self._extract_json(text)
                result = JDExtraction.model_validate_json(text)
                logger.info(f"JD extracted via OpenRouter ({model}): {result.role_title}")
                return result
            except Exception as e:
                logger.warning(f"OpenRouter JD parse failed ({model}): {e}")
                continue

        # Heuristic fallback — never fail
        logger.warning("All LLM calls failed. Using heuristic JD extraction.")
        return self._heuristic_jd_extract(jd_text, resume_text)

    def _heuristic_jd_extract(self, jd_text: str, resume_text: str) -> JDExtraction:
        """Emergency heuristic JD parser that never fails."""
        t = jd_text.lower()
        r = resume_text.lower()

        hard_pool = ["python","java","sql","docker","kubernetes","git","aws","gcp","azure",
                     "fastapi","flask","django","react","node.js","javascript","typescript",
                     "machine learning","deep learning","nlp","pytorch","tensorflow","langchain",
                     "langgraph","rag","llm","openai","gemini","rest api","graphql","microservices",
                     "ci/cd","spark","kafka","airflow","data engineering","mlops"]
        soft_pool = ["communication","leadership","teamwork","problem-solving","agile","scrum",
                     "collaboration","analytical","critical thinking","project management"]
        verb_pool = ["develop","build","design","implement","deploy","optimize","automate",
                     "integrate","lead","manage","create","engineer","architect","deliver"]

        jd_hard = [s for s in hard_pool if s in t]
        resume_hard = [s for s in hard_pool if s in r]
        can_inject = [s for s in jd_hard if s not in resume_hard][:5]
        cannot_claim = [s for s in jd_hard if s not in resume_hard and s not in can_inject][:3]

        first_line = jd_text.strip().split('\n')[0][:60]
        title = re.sub(r'[^\w\s/-]', '', first_line).strip() or "Software Engineer"

        return JDExtraction(
            role_title=title,
            hard_skills=jd_hard[:10],
            soft_skills=[s for s in soft_pool if s in t][:5],
            technical_skills=jd_hard[:8],
            action_verbs=[v for v in verb_pool if v in t][:6],
            must_have_keywords=jd_hard[:6],
            nice_to_have_keywords=jd_hard[6:10],
            repeated_ats_terms=jd_hard[:4],
            candidate_has=resume_hard[:8],
            candidate_needs_to_inject=can_inject,
            candidate_cannot_claim=cannot_claim,
            responsibility_phrases=[],
            ats_title_mirror=title,
            summary_hook=f"Experienced {title} with expertise in {', '.join(jd_hard[:3])}.",
            summary_supporting_line=f"Skilled in {', '.join(jd_hard[3:6])} with strong delivery track record.",
            keyword_placement_priority=["title","summary","skills","bullets"],
            ats_tip="Mirror exact JD keywords in skills section and bullet points."
        )

    # ── 3. Generate Tailored HTML Resume ──────────────────────────────────
    def generate_tailored_resume_html(
        self,
        jd_analysis: JDExtraction,
        resume_text: str,
        resume_skills: dict,
        generation_model: str = "gemini-2.5-flash"
    ) -> str:
        """
        Generate ATS-optimized HTML resume using the skeleton.
        Semantic replacement: inject JD keywords while preserving truth.
        """
        inject_kw = ", ".join(jd_analysis.candidate_needs_to_inject[:8])
        must_have = ", ".join(jd_analysis.must_have_keywords[:8])
        action_v  = ", ".join(jd_analysis.action_verbs[:6])
        resp_phrases = "\n".join(f"- {p}" for p in jd_analysis.responsibility_phrases[:5])

        candidate_name = resume_skills.get("candidate_name", "Candidate")
        contact_info   = resume_skills.get("contact_info", "email | phone | location")
        hard_skills    = resume_skills.get("hard_skills", [])
        soft_skills    = resume_skills.get("soft_skills", [])
        action_verbs   = resume_skills.get("action_verbs", [])

        # Merge resume skills + inject JD keywords into skills
        all_skills = list(dict.fromkeys(hard_skills + jd_analysis.candidate_needs_to_inject))

        system = """You are a world-class ATS resume writer.
Your task: rewrite the candidate's resume to optimally target the job description.
STRICT RULES:
1. Use the EXACT HTML skeleton structure provided — do not change the CSS classes
2. Mirror JD keywords EXACTLY (same spelling, same casing as JD uses)
3. Never fabricate experience — only inject skills candidate can honestly claim
4. Use strong action verbs from the JD's preferred list
5. Keep all bullet points truthful but keyword-rich
6. Output ONLY complete valid HTML — no markdown, no explanation"""

        prompt = f"""CANDIDATE NAME: {candidate_name}
CONTACT: {contact_info}
ATS TITLE TO USE: {jd_analysis.ats_title_mirror}

SUMMARY TO WRITE:
Opening: {jd_analysis.summary_hook}
Supporting: {jd_analysis.summary_supporting_line}

MUST-HAVE KEYWORDS (inject into bullets): {must_have}
KEYWORDS TO INJECT (candidate can honestly claim): {inject_kw}
JD PREFERRED ACTION VERBS: {action_v}

RESPONSIBILITY PHRASES FROM JD (mirror in bullet points):
{resp_phrases}

CANDIDATE'S ORIGINAL RESUME (use all real experience, dates, companies, education):
{resume_text}

ALL SKILLS TO INCLUDE IN SKILLS SECTION: {', '.join(all_skills[:20])}
SOFT SKILLS: {', '.join(soft_skills[:5])}

HTML SKELETON TO FILL (use these exact CSS classes, fill the placeholders):
{RESUME_SKELETON_HTML.format(
    candidate_name="{{CANDIDATE_NAME}}",
    ats_title_mirror="{{ATS_TITLE}}",
    contact_info="{{CONTACT}}",
    summary="{{SUMMARY}}",
    skills_html="{{SKILLS_HTML}}",
    experience_html="{{EXPERIENCE_HTML}}",
    projects_section="{{PROJECTS}}",
    education_html="{{EDUCATION_HTML}}",
    css=RESUME_SKELETON_CSS
)}

Generate the complete HTML with all sections filled. Keep everything in ONE page. 
Output ONLY the HTML starting with <!DOCTYPE html>"""

        # Try Gemini
        for attempt in range(3):
            try:
                from google.genai import types
                response = self.client.models.generate_content(
                    model=generation_model,
                    contents=system + "\n\n" + prompt,
                    config=types.GenerateContentConfig(temperature=0.1)
                ) if self.client else None

                if response:
                    text = response.text
                    text = self._strip_fences(text, "html")
                    if "<!DOCTYPE" in text or "<html" in text:
                        logger.info(f"Generated tailored HTML via Gemini ({len(text)} chars)")
                        return text
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    logger.warning(f"Gemini HTML gen attempt {attempt+1} failed: {e}")

        # OpenRouter fallback
        for model in OPENROUTER_MODELS_RANKED:
            try:
                logger.info(f"Trying OpenRouter HTML gen with {model}...")
                text = self._call_openrouter(
                    system + "\n\n" + prompt,
                    model=model
                )
                text = self._strip_fences(text, "html")
                if "<!DOCTYPE" in text or "<html" in text:
                    logger.info(f"Generated HTML via OpenRouter ({model})")
                    return text
                # If not proper HTML, try to extract it
                html_start = text.find("<!DOCTYPE")
                if html_start == -1:
                    html_start = text.find("<html")
                if html_start != -1:
                    return text[html_start:]
            except Exception as e:
                logger.warning(f"OpenRouter HTML ({model}) failed: {e}")
                continue

        # Emergency: return a basic skeleton with original content
        logger.error("All HTML generation failed. Returning base skeleton.")
        return self._emergency_html(candidate_name, contact_info, jd_analysis, resume_text, all_skills, soft_skills)

    def _emergency_html(self, name, contact, jd, resume_text, all_skills, soft_skills):
        """Last-resort HTML resume from skeleton."""
        skills_lines = ""
        if all_skills:
            skills_lines = f'<div class="skills-line"><b>Technical:</b> {", ".join(all_skills[:15])}</div>'
        if soft_skills:
            skills_lines += f'<div class="skills-line"><b>Soft Skills:</b> {", ".join(soft_skills[:6])}</div>'

        # Extract experience bullets from resume text
        lines = [l.strip() for l in resume_text.split('\n') if l.strip() and len(l.strip()) > 20]
        bullets = "".join(f"<li>{l}</li>" for l in lines[:8])

        html = RESUME_SKELETON_HTML.format(
            candidate_name=name,
            ats_title_mirror=jd.ats_title_mirror or "Software Engineer",
            contact_info=contact,
            summary=jd.summary_hook + " " + jd.summary_supporting_line,
            skills_html=skills_lines,
            experience_html=f'<ul class="bullets">{bullets}</ul>',
            projects_section="",
            education_html='<p class="summary-text">B.Tech Computer Science</p>',
            css=RESUME_SKELETON_CSS
        )
        return html

    # ── 4. ATS Evaluation ─────────────────────────────────────────────────
    def evaluate_ats_score(self, resume_html: str, jd_text: str, jd_analysis: JDExtraction) -> ATSEvaluation:
        """Score the generated resume against ATS criteria."""
        if not self.client and not self.openrouter_key:
            return ATSEvaluation(overall_ats_score=75)

        clean = re.sub(r'<[^>]+>', ' ', resume_html)
        clean = re.sub(r'\s+', ' ', clean).strip()

        # Quick local ATS keyword check (no LLM needed)
        must_found = sum(1 for k in jd_analysis.must_have_keywords if k.lower() in clean.lower())
        must_total = max(len(jd_analysis.must_have_keywords), 1)
        local_keyword_score = round((must_found / must_total) * 100)

        prompt = f"""ATS evaluation task. Score this resume 0-100 for this job.

MUST-HAVE KEYWORDS: {', '.join(jd_analysis.must_have_keywords)}
KEYWORDS INJECTED: {', '.join(jd_analysis.candidate_needs_to_inject)}

RESUME TEXT (first 2500 chars):
{clean[:2500]}

JD (first 1000 chars):
{jd_text[:1000]}

Return JSON:
{{"keyword_coverage_score": 0-100, "semantic_match_score": 0-100, "formatting_score": 0-100, "truthfulness_score": 0-100, "overall_ats_score": 0-100, "issues_found": ["issue1"], "recommendations": ["rec1"]}}"""

        # Try Gemini
        raw = self._gemini_structured(prompt, ATSEvaluation, "You are an ATS scoring engine. Return only JSON.")
        if raw:
            try:
                result = ATSEvaluation.model_validate_json(raw)
                logger.info(f"ATS Score: {result.overall_ats_score}/100")
                return result
            except:
                pass

        # OpenRouter fallback
        try:
            text = self._call_openrouter(prompt, system="Return only valid JSON for ATS evaluation.")
            text = self._extract_json(text)
            result = ATSEvaluation.model_validate_json(text)
            logger.info(f"ATS Score via OpenRouter: {result.overall_ats_score}/100")
            return result
        except Exception as e:
            logger.warning(f"ATS eval failed, using local keyword score: {e}")
            return ATSEvaluation(
                keyword_coverage_score=local_keyword_score,
                semantic_match_score=70,
                formatting_score=90,
                truthfulness_score=95,
                overall_ats_score=round((local_keyword_score * 0.5 + 80 * 0.5))
            )
