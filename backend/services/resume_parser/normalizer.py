import re

def normalize_text(text: str) -> str:
    """Normalizes the extracted text for parsing."""
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    # Standardize line breaks
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove zero-width spaces and weird characters
    text = text.replace('\u200b', '').replace('\xa0', ' ')
    
    return text.strip()
