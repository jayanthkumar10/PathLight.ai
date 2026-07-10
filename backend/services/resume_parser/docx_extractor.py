import docx
import logging

logger = logging.getLogger(__name__)

def extract_docx_text(file_path: str) -> dict:
    """Extracts text from a DOCX file."""
    try:
        text = ""
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
                
        if not text.strip():
            raise ValueError("No extractable text found in DOCX")
            
        return {
            "text": text,
            "page_count": 1, # DOCX doesn't expose physical pages easily
            "word_count": len(text.split())
        }
    except Exception as e:
        logger.error(f"Error extracting DOCX: {e}")
        raise ValueError(f"Failed to extract DOCX: {str(e)}")
