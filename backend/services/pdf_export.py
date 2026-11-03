import logging
from io import BytesIO

from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

logger = logging.getLogger("ats_resume_scorer")


def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    """Render multiple HTML documents with Chromium and combine them into one PDF."""
    if not html_docs:
        raise ValueError("No HTML documents provided for PDF generation.")

    pdf_parts = []

    # This synchronous API is called from FastAPI's threadpool. On Windows this
    # avoids Playwright's async subprocess launch, which is unsupported by the
    # Proactor event loop used by Uvicorn.
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            for name, html_str in html_docs.items():
                logger.info("Rendering PDF section: %s", name)
                page.set_content(html_str, wait_until="networkidle")
                pdf_parts.append(
                    page.pdf(
                        format="A4",
                        print_background=True,
                        prefer_css_page_size=True,
                    )
                )
        finally:
            browser.close()

    writer = PdfWriter()
    for pdf_bytes in pdf_parts:
        reader = PdfReader(BytesIO(pdf_bytes))
        for pdf_page in reader.pages:
            writer.add_page(pdf_page)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()

