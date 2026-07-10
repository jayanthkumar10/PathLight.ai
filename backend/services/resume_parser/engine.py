import time
from .pdf_extractor import extract_pdf_text
from .docx_extractor import extract_docx_text
from .normalizer import normalize_text
from .section_detector import detect_sections
import hashlib

PARSER_VERSION = "1.0.0-heuristic"

def _compute_checksum(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def process_resume(file_path: str, mime_type: str) -> dict:
    """End to end pipeline for resume processing."""
    start_time = time.time()
    
    if "pdf" in mime_type.lower():
        extraction = extract_pdf_text(file_path)
    elif "document" in mime_type.lower() or "docx" in mime_type.lower():
        extraction = extract_docx_text(file_path)
    else:
        raise ValueError("Unsupported MIME type")
        
    raw_text = extraction["text"]
    page_count = extraction["page_count"]
    word_count = extraction["word_count"]
    
    normalized_text = normalize_text(raw_text)
    structured_data = detect_sections(normalized_text)
    checksum = _compute_checksum(file_path)
    
    extraction_time = time.time() - start_time
    
    return {
        "raw_text": normalized_text,
        "structured_data": structured_data,
        "metadata": {
            "checksum": checksum,
            "parser_version": PARSER_VERSION,
            "extraction_time_ms": int(extraction_time * 1000),
            "page_count": page_count,
            "word_count": word_count,
            "section_count": len([k for k, v in structured_data.items() if v])
        }
    }
