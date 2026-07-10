"""
PDF Generator — Multi-backend HTML-to-PDF conversion.

Priority:
1. xhtml2pdf   — Pure Python, no system deps, ATS-readable text PDF
2. Playwright  — Pixel-perfect, requires chromium
3. HTML fallback — Saves .html file, still downloadable

Single A4 page format with exact aspect ratio matching uploaded resume.
"""
import os
import io
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

# A4 dimensions
A4_WIDTH_PT  = 595.28
A4_HEIGHT_PT = 841.89


def _generate_pdf_xhtml2pdf(html_content: str, output_path: str) -> bool:
    """Use xhtml2pdf for ATS-readable text-selectable PDF."""
    try:
        from xhtml2pdf import pisa

        # Inject print-ready CSS for single A4 page
        pdf_css = """
<style>
@page {
  size: A4;
  margin: 0;
}
html, body {
  width: 210mm;
  height: 297mm;
  overflow: hidden;
  font-size: 10pt;
}
</style>
"""
        # Inject CSS just before </head>
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", pdf_css + "</head>", 1)
        else:
            html_content = pdf_css + html_content

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as pdf_file:
            result = pisa.CreatePDF(
                io.StringIO(html_content),
                dest=pdf_file,
                encoding="utf-8"
            )

        if result.err:
            logger.warning(f"xhtml2pdf partial errors: {result.err}")
            return False

        size = os.path.getsize(output_path)
        logger.info(f"PDF generated via xhtml2pdf: {output_path} ({size} bytes)")
        return size > 1000

    except Exception as e:
        logger.warning(f"xhtml2pdf failed: {e}")
        return False


async def _generate_pdf_playwright(html_content: str, output_path: str) -> bool:
    """Use Playwright Chromium for pixel-perfect PDF."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(html_content, wait_until="networkidle")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            await page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
            )
            await browser.close()

        size = os.path.getsize(output_path)
        logger.info(f"PDF generated via Playwright: {output_path} ({size} bytes)")
        return size > 1000

    except Exception as e:
        logger.warning(f"Playwright PDF failed: {e}")
        return False


def _save_html_fallback(html_content: str, output_path: str) -> bool:
    """Save as .html file (browsers can print-to-PDF with Ctrl+P)."""
    try:
        html_path = output_path.replace(".pdf", ".html")
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"HTML fallback saved: {html_path}")
        return True
    except Exception as e:
        logger.error(f"HTML fallback also failed: {e}")
        return False


async def generate_pdf_from_html(html_content: str, output_path: str) -> str:
    """
    Multi-backend PDF generation.
    Returns path to generated file (PDF or HTML fallback).
    """
    # 1. Try xhtml2pdf (best for ATS readability)
    if _generate_pdf_xhtml2pdf(html_content, output_path):
        return output_path

    # 2. Try Playwright (best visual quality)
    if await _generate_pdf_playwright(html_content, output_path):
        return output_path

    # 3. HTML fallback
    html_path = output_path.replace(".pdf", ".html")
    if _save_html_fallback(html_content, output_path):
        return html_path

    raise RuntimeError("All PDF generation methods failed")


async def generate_pdf_bytes(html_content: str) -> bytes:
    """Generate PDF and return as bytes (for streaming download)."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result_path = await generate_pdf_from_html(html_content, tmp_path)
        with open(result_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass
        try:
            html_path = tmp_path.replace(".pdf", ".html")
            os.unlink(html_path)
        except:
            pass
