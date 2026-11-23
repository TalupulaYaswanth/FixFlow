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
            if shape.has_text_frame:
                text_frame = shape.text_frame
                for paragraph in text_frame.paragraphs:
                    p_text = paragraph.text.strip()
                    if not p_text:
                        continue
                    if shape == slide.shapes.title and not slide_title:
                        slide_title = p_text
                    else:
                        slide_paragraphs.append(p_text)
            elif shape.has_table:
                for row in shape.table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        slide_paragraphs.append(" | ".join(row_cells))

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

    if not paragraphs:
        return "[Word Document loaded: No paragraph or table text found. Document appears to be empty.]"

    return "\n\n".join(paragraphs)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text page-by-page from a PDF document using pypdf.
    Includes fallback regex stream scanner for non-standard or compressed streams.
    """
    pages_text = []
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for idx, page in enumerate(reader.pages, start=1):
            try:
                extracted = page.extract_text()
                if extracted and extracted.strip():
                    pages_text.append(f"--- Page {idx} ---\n{extracted.strip()}")
            except Exception:
                continue
    except Exception as e:
        pages_text = []

    if pages_text:
        return "\n\n".join(pages_text)

    # Fallback 1: Scan for and decompress zlib FlateDecode streams in compressed PDFs
    import zlib
    import re
    extracted_chunks = []
    try:
        stream_chunks = re.findall(rb'stream[\r\n]+([\s\S]*?)[\r\n]+endstream', file_bytes)
        for raw_s in stream_chunks:
            decomp = None
            try:
                decomp = zlib.decompress(raw_s)
            except Exception:
                try:
                    decomp = zlib.decompress(raw_s, -15)
                except Exception:
                    pass
            if decomp:
                # Find (text) Tj
                for tj in re.findall(rb'\(((?:\\.|[^\)])*)\)\s*Tj', decomp):
                    clean = tj.decode('latin-1', errors='ignore').strip()
                    if clean and len(clean) > 1:
                        extracted_chunks.append(clean)
                # Find [(text1) -20 (text2)] TJ
                for tj in re.findall(rb'\[(.*?)\]\s*TJ', decomp):
                    parts = re.findall(rb'\(((?:\\.|[^\)])*)\)', tj)
                    joined = b" ".join(parts).decode('latin-1', errors='ignore').strip()
                    if joined and len(joined) > 1:
                        extracted_chunks.append(joined)
        if extracted_chunks:
            return "\n".join(extracted_chunks[:400])
    except Exception:
        pass

    # Fallback 2: extract continuous printable text chunks from raw stream
    try:
        for chunk in re.findall(rb'[\x20-\x7E\r\n]{5,}', file_bytes):
            decoded = chunk.decode('latin-1', errors='ignore').strip()
            if len(decoded) > 5 and not decoded.startswith(('obj', 'endobj', 'xref', 'trailer', 'startxref', 'stream', 'endstream')):
                extracted_chunks.append(decoded)
        if extracted_chunks:
            return "\n".join(extracted_chunks[:250])
    except Exception:
        pass

    return "[PDF Document loaded: No selectable text stream found. The PDF may contain scanned images rather than selectable text.]"


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

    elif lower_name.endswith((".txt", ".md", ".csv", ".json", ".py", ".html", ".xml", ".log", ".rtf", ".yaml", ".yml")):
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="replace")
        return text, "text", {"size_bytes": len(file_bytes)}

    elif lower_name.endswith(".doc"):
        # Legacy binary Word document: attempt plain text chunk extraction or advise saving as .docx
        import re
        extracted_chunks = []
        try:
            for chunk in re.findall(rb'[\x20-\x7E\r\n]{4,}', file_bytes):
                decoded = chunk.decode('latin-1', errors='ignore').strip()
                if len(decoded) > 3 and not decoded.startswith(('WordDocument', 'CompObj', 'ObjectPool')):
                    extracted_chunks.append(decoded)
            if extracted_chunks:
                return "\n\n".join(extracted_chunks[:100]), "doc", {"note": "Legacy .doc text stream. For optimal formatting, save as .docx."}
        except Exception:
            pass
        raise ValueError("Legacy .doc format detected. Please save or export your document as .docx or .pdf for structured extraction.")

    else:
        # Fallback attempt text decode
        try:
            text = file_bytes.decode("utf-8")
            return text, "text", {"size_bytes": len(file_bytes)}
        except Exception:
            raise ValueError(f"Unsupported file format for '{file_name}'. Please upload .pptx, .docx, .pdf, or .txt files.")
