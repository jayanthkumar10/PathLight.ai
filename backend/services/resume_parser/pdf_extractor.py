import pypdf
import logging

logger = logging.getLogger(__name__)

def extract_pdf_text(file_path: str) -> dict:
    """Extracts text from a PDF file."""
    try:
        text = ""
        page_count = 0
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            if reader.is_encrypted:
                raise ValueError("PDF is encrypted or password protected")
            
            page_count = len(reader.pages)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
        if not text.strip():
            raise ValueError("No extractable text found in PDF (might be a scanned image)")
            
        return {
            "text": text,
            "page_count": page_count,
            "word_count": len(text.split())
        }
    except Exception as e:
        logger.error(f"Error extracting PDF: {e}")
        raise ValueError(f"Failed to extract PDF: {str(e)}")
