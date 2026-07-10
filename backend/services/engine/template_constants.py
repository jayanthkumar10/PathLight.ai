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
