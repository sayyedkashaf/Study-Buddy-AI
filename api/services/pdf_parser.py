"""
PDF Parser — Extract text and structure from uploaded syllabus PDFs.

Uses PyMuPDF (fitz) for robust PDF text extraction.
"""

import logging
import re
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> dict:
    """
    Extract text, topics, and metadata from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Dictionary with:
        - full_text: Complete extracted text
        - topics: List of detected topic/section headers
        - page_count: Number of pages
        - chunks: Pre-chunked text segments for embedding
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    try:
        doc = fitz.open(file_path)
        full_text = ""
        pages = []

        for page_num, page in enumerate(doc):
            try:
                text = page.get_text()
                full_text += text + "\n"
                pages.append({"page": page_num + 1, "text": text})
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
                pages.append({"page": page_num + 1, "text": ""})

        doc.close()
    except Exception as e:
        logger.error(f"Failed to open or read PDF {file_path}: {e}", exc_info=True)
        raise

    try:
        # Detect topic headers (lines that look like section titles)
        topics = _extract_topics(full_text)

        # Create smart chunks for embedding
        chunks = _smart_chunk(full_text, chunk_size=500, overlap=50)

        logger.info(f"Parsed PDF: {path.name} | {len(pages)} pages | {len(topics)} topics | {len(chunks)} chunks")

        return {
            "full_text": full_text.strip(),
            "topics": topics,
            "page_count": len(pages),
            "pages": pages,
            "chunks": chunks,
        }
    except Exception as e:
        logger.error(f"Error processing extracted PDF text: {e}", exc_info=True)
        raise


def _extract_topics(text: str) -> list[str]:
    """
    Heuristically detect section/topic headers from PDF text.

    Looks for:
    - Lines in ALL CAPS (likely headers)
    - Lines starting with "Unit", "Chapter", "Module"
    - Numbered sections like "1.1 Topic Name"
    """
    topics = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue

        # All-caps lines (likely headers) — at least 5 chars
        if line.isupper() and len(line) >= 5 and len(line) <= 200:
            topics.append(line)
            continue

        # Lines starting with Unit/Chapter/Module
        if re.match(r"^(Unit|Chapter|Module|Section|Topic|Lesson)\s+\d", line, re.IGNORECASE):
            topics.append(line)
            continue

        # Numbered sections: "1.", "1.1", "1.1.1" followed by text
        if re.match(r"^\d+(\.\d+)*\s+[A-Z]", line):
            topics.append(line)
            continue

    # Deduplicate while preserving order
    seen = set()
    unique_topics = []
    for t in topics:
        normalized = t.strip().lower()
        if normalized not in seen:
            seen.add(normalized)
            unique_topics.append(t.strip())

    return unique_topics


def _smart_chunk(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks, trying to break at sentence boundaries.

    Args:
        text: Full text to chunk.
        chunk_size: Target characters per chunk.
        overlap: Characters of overlap between consecutive chunks.

    Returns:
        List of text chunks.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # If adding this sentence stays within limit, append it
        if len(current_chunk) + len(sentence) + 1 < chunk_size:
            current_chunk += sentence + " "
        else:
            # Save current chunk if non-empty
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # Start new chunk with overlap from the end of previous
            if overlap > 0 and current_chunk:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text + sentence + " "
            else:
                current_chunk = sentence + " "

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
