RESUME_TEMPLATE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jayanth Kumar Pillajetti - Resume</title>
    <style>
        /* Base Styles & Typography */
        body {{
            font-family: 'Arial', 'Helvetica Neue', sans-serif;
            line-height: 1.4;
            color: #222;
            background-color: #f4f4f5;
            margin: 0;
            padding: 20px 0;
            -webkit-font-smoothing: antialiased;
        }}

        /* Page Layout simulating A4 Paper */
        .page {{
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 50px;
            background: #ffffff;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            box-sizing: border-box;
        }}

        /* Print overrides */
        @media print {{
            body {{
                background-color: #fff;
                padding: 0;
            }}
            .page {{
                box-shadow: none;
                margin: 0 auto;
                padding: 20px;
                max-width: 100%;
                min-height: auto;
            }}
        }}

        /* Header Styles */
        header {{
            text-align: center;
            margin-bottom: 20px;
        }}

        h1 {{
            margin: 0 0 5px 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}

        .subtitle {{
            font-size: 13.5px;
            margin: 5px 0;
            font-weight: 600;
        }}

        .contact-info {{
            font-size: 13px;
            margin-top: 5px;
            color: #444;
        }}

        .contact-info a, .project-link {{
            color: #0056b3;
            text-decoration: none;
        }}

        .contact-info a:hover, .project-link:hover {{
            text-decoration: underline;
        }}

        /* Section Styles */
        .section-title {{
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            border-bottom: 1.5px solid #222;
            margin-top: 18px;
            margin-bottom: 10px;
            padding-bottom: 4px;
        }}

        p {{
            margin: 6px 0;
            font-size: 13px;
            text-align: justify;
        }}

        ul {{
            margin: 6px 0 14px 0;
            padding-left: 20px;
            font-size: 13px;
        }}

        li {{
            margin-bottom: 6px;
            text-align: justify;
        }}

        /* Layout Utility Classes */
        .flex-container {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 4px;
        }}

        .bold {{
            font-weight: bold;
        }}

        .italic {{
            font-style: italic;
        }}

        .tech-stack {{
            font-size: 12.5px;
            color: #555;
            font-style: italic;
            margin-top: -3px;
            margin-bottom: 6px;
        }}

        .skills-list p {{
            margin: 4px 0;
        }}
    </style>
</head>
<body>
    <div class="page">
        <!-- HEADER -->
        <header>
            <h1>JAYANTH KUMAR PILLAJETTI</h1>
            <div class="subtitle">{subtitle}</div>
            <div class="contact-info">
                +91 9133985109 | 
                <a href="mailto:pillajettijayanth@gmail.com">pillajettijayanth@gmail.com</a> | 
                <a href="https://www.linkedin.com/in/jayanth-kumar-" target="_blank">LinkedIn</a> | 
                <a href="https://github.com/jayanthkumar10" target="_blank">GitHub</a> | 
                <a href="https://jayanthkumar10.github.io/" target="_blank">Portfolio</a>
            </div>
        </header>

        <!-- PROFESSIONAL SUMMARY -->
        <section>
            <div class="section-title">Professional Summary</div>
            <p>{professional_summary}</p>
        </section>

        <!-- TECHNICAL SKILLS -->
        <section>
            <div class="section-title">Technical Skills</div>
            <div class="skills-list">
                {technical_skills}
            </div>
        </section>

        <!-- WORK EXPERIENCE -->
        <section>
            <div class="section-title">Work Experience</div>
            
            <div class="flex-container">
                <div class="bold">Tata Consultancy Services (TCS) | {tcs_role}</div>
                <div class="bold">Apr 2024 – Present</div>
            </div>
            <ul>
                {tcs_bullets}
            </ul>
        </section>

        <!-- PROJECTS -->
        <section>
            <div class="section-title">Projects</div>

            <!-- Project 1 -->
            <div class="flex-container">
                <div class="bold">
                    Autonomous AI Job Hunter Agent - <a href="https://jayanthkumar10.github.io/project-ai-job-companion.html" class="project-link" target="_blank">[View Project]</a>
                </div>
            </div>
            <div class="tech-stack">Python, LangGraph, LangChain, RAG, FAISS, n8n, Gemini API</div>
            <ul>
                {project_1_bullets}
            </ul>

            <!-- Project 2 -->
            <div class="flex-container" style="margin-top: 15px;">
                <div class="bold">
                    Enterprise AIOps Co-Pilot (Pulseops AI) - <a href="https://jayanthkumar10.github.io/project-pulseops-ai.html" class="project-link" target="_blank">[View Project]</a>
                </div>
            </div>
            <div class="tech-stack">Python, FastAPI, Multi-Agent AI, RAG, ChromaDB, Llama</div>
            <ul>
                {project_2_bullets}
            </ul>
        </section>

        <!-- EDUCATION -->
        <section>
            <div class="section-title">Education</div>
            
            <div class="flex-container">
                <div class="bold">SRM University Andhra Pradesh</div>
                <div class="bold">Aug 2019 – May 2023</div>
            </div>
            <div class="flex-container">
                <div>B.Tech, Computer Science — AI & Machine Learning Specialisation</div>
                <div>GPA: 8.2 / 10</div>
            </div>
        </section>

        <!-- ACHIEVEMENTS -->
        <section>
            <div class="section-title">Achievements</div>
            <ul>
                {achievements_bullets}
            </ul>
        </section>

    </div>

</body>
</html>
"""

# Dynamic HTML Template Base (extracting the top header part and css from above)
DYNAMIC_RESUME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{name} - Resume</title>
    <style>
        @page {
            size: letter;
            margin: 0.5in 0.6in;
        }
        body {
            font-family: 'Inter', 'Helvetica Neue', 'Arial', sans-serif;
            color: #222;
            font-size: 13.5px;
            line-height: 1.45;
            -webkit-font-smoothing: antialiased;
        }
        @media screen {
            body {
                background-color: #e5e7eb;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
            }
            .page {
                background-color: white;
                width: 800px;
                max-width: 100%;
                min-height: 1056px;
                padding: 0.5in 0.6in;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                box-sizing: border-box;
            }
        }
        @media print {
            body {
                background-color: white;
                margin: 0;
                padding: 0;
            }
            .page {
                width: 100%;
            }
        }
        header {
            text-align: center;
            margin-bottom: 16px;
        }
        h1 {
            margin: 0;
            font-size: 24px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #000;
        }
        .subtitle {
            font-size: 14px;
            color: #555;
            margin-bottom: 4px;
            font-weight: 600;
        }
        .contact-info {
            font-size: 13px;
            color: #444;
        }
        .contact-info a {
            color: #0056b3;
            text-decoration: none;
        }
        .section-title {
            font-size: 15px;
            font-weight: bold;
            color: #000;
            text-transform: uppercase;
            border-bottom: 1.5px solid #000;
            margin-top: 12px;
            margin-bottom: 8px;
            padding-bottom: 2px;
        }
        section {
            margin-bottom: 12px;
        }
        ul {
            margin-top: 4px;
            margin-bottom: 4px;
            padding-left: 20px;
        }
        li {
            margin-bottom: 6px;
            text-align: justify;
        }
        .flex-container {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 4px;
        }
        .bold {
            font-weight: bold;
        }
        .tech-stack {
            font-size: 12.5px;
            color: #555;
            font-style: italic;
            margin-top: -3px;
            margin-bottom: 6px;
        }
        .skills-list p {
            margin: 4px 0;
        }
        .project-link {
            font-size: 12.5px;
            color: #0056b3;
            text-decoration: none;
            font-weight: normal;
        }
    </style>
</head>
<body>
    <div class="page">
        <!-- HEADER -->
        <header>
            <h1>{name}</h1>
            <div class="subtitle">{subtitle}</div>
            <div class="contact-info">
                {contact_html}
            </div>
        </header>

        <!-- PROFESSIONAL SUMMARY -->
        {professional_summary_section}

        <!-- TECHNICAL SKILLS -->
        <section>
            <div class="section-title">Technical Skills</div>
            <div class="skills-list">
                {technical_skills}
            </div>
        </section>

        <!-- WORK EXPERIENCE -->
        {work_experience_section}

        <!-- PROJECTS -->
        {projects_section}

        <!-- EDUCATION -->
        {education_section}

        <!-- ACHIEVEMENTS -->
        {achievements_section}
    </div>
</body>
</html>
"""

MASTER_SKILLS_DICT = {
    "Languages & Core Tech": ["Python", "SQL", "PL/SQL", "RESTful APIs", "Git"],
    "AI & Machine Learning": ["Generative AI", "Large Language Models (LLMs)", "Agentic AI", "AI Agents", "Multi-Agent Systems", "Prompt Engineering", "Context Engineering", "Retrieval-Augmented Generation (RAG)", "Agentic RAG", "Function Calling", "Tool Calling", "Structured Outputs", "Embeddings", "Semantic Search", "Hybrid Search", "Vector Search", "Natural Language Processing (NLP)", "Machine Learning", "Deep Learning Fundamentals", "Model Evaluation", "Tokenization", "Harness Engineering"],
    "Automation & Agentic Frameworks": ["n8n", "AI Agents", "Multi-Agent Workflows", "LangChain", "LangGraph", "Model Context Protocol (MCP)", "Prompt Templates", "Chains", "Memory Management", "Workflow Orchestration", "Prompt Flow"],
    "LLM Providers & Models": ["Azure OpenAI Service", "OpenAI GPT Models", "Anthropic Claude", "Google Gemini", "Llama", "Mistral", "Phi", "Gemma"],
    "Vector Databases & Knowledge Retrieval": ["Azure AI Search", "Pinecone", "ChromaDB", "FAISS"],
    "ML & AI Libraries": ["Pandas", "NumPy", "Scikit-learn", "Hugging Face Transformers", "Hugging Face Hub", "Sentence Transformers"],
    "Backend & Deployment": ["FastAPI", "Streamlit", "Docker", "Git", "GitHub", "GitHub Actions", "CI/CD Fundamentals", "API Integration"],
    "Cloud & Azure AI": ["Microsoft Azure", "Azure AI Foundry", "Azure OpenAI Service", "Azure AI Search", "Azure AI Studio", "Azure Functions (Fundamentals)", "Azure Storage (Fundamentals)"],
    "AI Evaluation, Observability & Responsible AI": ["LLM Evaluation", "Prompt Evaluation", "Hallucination Detection", "AI Guardrails", "AI Testing", "Tracing", "Logging", "Monitoring", "Prompt Injection Awareness", "Responsible AI Fundamentals"],
    "Development Tools": ["Visual Studio Code", "Jupyter Notebook", "Postman"],
    "Software Engineering": ["Object-Oriented Programming (OOP)", "Data Structures & Algorithms (DSA)", "Debugging", "Agile Methodologies"],
    "Certificates": ["Prompt Engineering for developers - Deeplearning.ai", "Microsoft Certified : Azure AI Engineer Associate (AI-102)"]
}

HARDCODED_ACHIEVEMENTS = """
                <li><span class="bold">Published Patent: "System and Method for Heart Disease Prediction Using Supervised Machine Learning Algorithms" — Indian Patent Journal;</span> engineered a unified dataset by merging multiple clinical data sources, improving data quality and achieving high model accuracy for reliable early-stage prediction.</li>
                <li><span class="bold">Spot Award (TCS):</span> Awarded for exceptional performance in developing AI-driven solutions, contributing to automation and improved operational efficiency.</li>
"""

