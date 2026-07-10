import re

SECTION_KEYWORDS = {
    "summary": ["summary", "profile", "objective", "about me"],
    "skills": ["skills", "technical skills", "technologies", "core competencies"],
    "experience": ["experience", "work experience", "employment history", "professional experience"],
    "projects": ["projects", "personal projects", "academic projects"],
    "education": ["education", "academic background"],
    "certifications": ["certifications", "licenses"],
    "achievements": ["achievements", "awards", "honors"],
    "languages": ["languages"]
}

def _determine_section(line: str) -> str:
    line_lower = line.strip().lower()
    if len(line_lower) > 35: # Titles are usually short
        return None
        
    for section, keywords in SECTION_KEYWORDS.items():
        for keyword in keywords:
            if line_lower == keyword or line_lower == keyword + ":":
                return section
    return None

def detect_sections(text: str) -> dict:
    """Parses text into major sections heuristically."""
    lines = text.split('\n')
    
    sections = {
        "summary": "",
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": [],
        "achievements": [],
        "languages": []
    }
    
    current_section = "summary"
    current_block = []
    
    for line in lines:
        detected = _determine_section(line)
        
        if detected:
            if current_section == "summary":
                sections["summary"] = "\n".join(current_block).strip()
            elif current_section in ["skills", "certifications", "achievements", "languages"]:
                if current_block:
                    items = [i.strip("- ") for i in "\n".join(current_block).split('\n') if i.strip()]
                    sections[current_section].extend(items)
            else:
                if current_block:
                    sections[current_section].append("\n".join(current_block).strip())
            
            current_section = detected
            current_block = []
        else:
            if line.strip():
                current_block.append(line)
                
    # Handle the last section
    if current_block:
        if current_section == "summary":
            sections["summary"] = "\n".join(current_block).strip()
        elif current_section in ["skills", "certifications", "achievements", "languages"]:
            items = [i.strip("- ") for i in "\n".join(current_block).split('\n') if i.strip()]
            sections[current_section].extend(items)
        else:
            sections[current_section].append("\n".join(current_block).strip())
            
    # Format objects for Experience and Projects as best effort heuristic
    formatted_exp = []
    for exp_block in sections["experience"]:
        # very rudimentary parsing for objects
        lines = exp_block.split('\n')
        if len(lines) >= 2:
            formatted_exp.append({
                "company": lines[0],
                "role": lines[1] if len(lines) > 1 else "",
                "duration": "",
                "description": "\n".join(lines[2:])
            })
        else:
             formatted_exp.append({"company": exp_block, "role": "", "duration": "", "description": ""})
    sections["experience"] = formatted_exp

    formatted_proj = []
    for proj_block in sections["projects"]:
        lines = proj_block.split('\n')
        formatted_proj.append({
            "title": lines[0] if lines else "",
            "description": "\n".join(lines[1:]) if len(lines) > 1 else "",
            "technologies": []
        })
    sections["projects"] = formatted_proj
            
    return sections
