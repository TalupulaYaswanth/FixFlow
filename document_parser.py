"""
FixFlow: Smart Text Correction Powered by Dynamic Programming & NLP
Module: document_parser.py

Handles document parsing and text extraction across:
- PowerPoint presentations (.pptx)
- Word documents (.docx)
- PDF documents (.pdf)
- Plain text / Markdown (.txt, .md, .rtf)
"""

import io
from typing import List, Dict, Any, Tuple


def extract_text_from_pptx(file_bytes: bytes) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Extracts structured text slide-by-slide from a PowerPoint presentation (.pptx).
    Returns:
      - full_text: string with slide headers
      - slides_data: list of dicts [{"slide_number": int, "title": str, "content": List[str]}]
    """
    from pptx import Presentation

    prs = Presentation(io.BytesIO(file_bytes))
    slides_data = []
    full_text_parts = []

    for idx, slide in enumerate(prs.slides, start=1):
        slide_title = ""
        slide_paragraphs = []

        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            text_frame = shape.text_frame
            for paragraph in text_frame.paragraphs:
                p_text = paragraph.text.strip()
                if not p_text:
                    continue
                # If slide has a title shape and it's not set
                if shape == slide.shapes.title and not slide_title:
                    slide_title = p_text
                else:
                    slide_paragraphs.append(p_text)

        slides_data.append({
            "slide_number": idx,
            "title": slide_title or f"Slide {idx}",
            "paragraphs": slide_paragraphs
        })

        header = f"=== Slide {idx}: {slide_title or 'Untitled'} ==="
        body = "\n".join(f"• {p}" for p in slide_paragraphs) if slide_paragraphs else "(No text content)"
        full_text_parts.append(f"{header}\n{body}")

    return "\n\n".join(full_text_parts), slides_data


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extracts text paragraphs and tables from a Word document (.docx).
    """
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    # Also capture table contents
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(f"[Table Row]: {row_text}")

    return "\n\n".join(paragraphs)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text page-by-page from a PDF document using pypdf.
    """
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    pages_text = []

    for idx, page in enumerate(reader.pages, start=1):
        extracted = page.extract_text()
        if extracted and extracted.strip():
            pages_text.append(f"--- Page {idx} ---\n{extracted.strip()}")

    return "\n\n".join(pages_text)


def parse_uploaded_file(file_name: str, file_bytes: bytes) -> Tuple[str, str, Dict[str, Any]]:
    """
    Detects file extension and extracts text.

    Returns:
      - extracted_text: str
      - file_type: str ('pptx', 'docx', 'pdf', 'text')
      - metadata: dict with page/slide counts and details
    """
    lower_name = file_name.lower()

    if lower_name.endswith(".pptx"):
        text, slides = extract_text_from_pptx(file_bytes)
        return text, "pptx", {"total_slides": len(slides), "slides": slides}

    elif lower_name.endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
        return text, "docx", {"paragraphs_count": len(text.split("\n\n"))}

    elif lower_name.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
        return text, "pdf", {"pages_count": text.count("--- Page ")}

    elif lower_name.endswith((".txt", ".md", ".csv", ".json", ".py", ".html")):
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="replace")
        return text, "text", {"size_bytes": len(file_bytes)}

    else:
        # Fallback attempt text decode
        try:
            text = file_bytes.decode("utf-8")
            return text, "text", {"size_bytes": len(file_bytes)}
        except Exception:
            raise ValueError(f"Unsupported file format for '{file_name}'. Please upload .pptx, .docx, .pdf, or .txt files.")
