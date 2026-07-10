import os
import uuid
import logging
from weasyprint import HTML

logger = logging.getLogger(__name__)

# Base directory for generated PDFs
OUTPUT_DIR = os.path.join(os.getcwd(), "generated_resumes")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_and_validate_pdf(html_content: str, job_title: str, company: str) -> str:
    """
    Step 11: PDF Generator.
    Converts HTML to PDF using the template's embedded CSS for pixel-perfect matching.
    """
    company_clean = "".join(x if x.isalnum() else "_" for x in (company or "resume"))
    role_clean    = "".join(x if x.isalnum() else "_" for x in (job_title or "role"))
    
    filename = f"{role_clean}_{company_clean}_jayanth_resume.pdf"
    
    output_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(output_path):
        filename = f"{role_clean}_{company_clean}_jayanth_resume_{uuid.uuid4().hex[:4]}.pdf"
        output_path = os.path.join(OUTPUT_DIR, filename)
    
    # Render using the HTML's embedded styling exactly as it appears in the browser
    pdf = HTML(string=html_content).render()
    pdf.write_pdf(output_path)
        
    return output_path
