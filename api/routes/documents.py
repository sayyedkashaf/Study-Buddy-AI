"""
Document Routes — Upload and process syllabus PDFs.

POST /documents/upload   → Upload PDF, parse, store in ChromaDB
GET  /documents/list     → List all uploaded documents
DELETE /documents/{id}   → Remove a document
"""

import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from api.services.pdf_parser import parse_pdf
from api.services.vector_store import VectorStore
from api.services.cache_service import CacheService
from api.core.config import UPLOADS_DIR

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    subject_name: str = Query(default="General", description="Subject this PDF belongs to"),
):
    """
    Upload a syllabus PDF → parse text → generate embeddings → store in ChromaDB.

    Returns:
        Document metadata including extracted topics count.
    """
    # ── 1. Validate ───────────────────────────────────────────
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    if file.size and file.size > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="File too large. Maximum 20MB.")

    # ── 2. Save file ──────────────────────────────────────────
    file_path = UPLOADS_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # ── 3. Parse PDF ──────────────────────────────────────────
    try:
        logger.info(f"Starting PDF parsing for: {file.filename}")
        result = parse_pdf(str(file_path))
        logger.info(f"Successfully parsed PDF: {file.filename} ({result.get('page_count', 0)} pages)")
    except Exception as e:
        logger.error(f"PDF parsing failed for {file.filename}: {e}", exc_info=True)
        # Clean up the file if parsing fails
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {e}")

    # ── 4. Store in vector database ───────────────────────────
    try:
        logger.info(f"Starting embedding/indexing for: {file.filename}")
        vector_store = VectorStore()
        vector_store.add_document(
            text=result["full_text"],
            doc_id=file.filename,
            metadata={
                "type": "syllabus",
                "filename": file.filename,
                "subject": subject_name,
                "page_count": result["page_count"],
            },
        )
        logger.info(f"Successfully indexed {file.filename} into vector store")
    except Exception as e:
        logger.error(f"Vector store insertion failed for {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to index document: {e}")

    # ── 5. Cache summary ─────────────────────────────────────
    cache = CacheService()
    cache.set(
        f"doc_summary:{file.filename}",
        {
            "filename": file.filename,
            "subject": subject_name,
            "topics": result["topics"][:20],
            "page_count": result["page_count"],
            "chunk_count": len(result["chunks"]),
        },
        ttl=7200,  # 2 hours
    )

    logger.info(f"Uploaded and indexed: {file.filename} ({result['page_count']} pages, {len(result['topics'])} topics)")

    return {
        "message": "Document uploaded and indexed successfully! 🎉",
        "filename": file.filename,
        "subject": subject_name,
        "topics_found": len(result["topics"]),
        "topics": result["topics"][:15],  # Return first 15 topics
        "page_count": result["page_count"],
        "chunks_created": len(result["chunks"]),
    }


@router.get("/list")
async def list_documents():
    """List all uploaded PDF documents."""
    uploads_dir = Path(UPLOADS_DIR)
    files = []

    for f in uploads_dir.glob("*.pdf"):
        files.append({
            "filename": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
        })

    vector_store = VectorStore()

    return {
        "documents": files,
        "total_files": len(files),
        "total_chunks_indexed": vector_store.get_document_count(),
    }


@router.delete("/{filename}")
async def delete_document(filename: str):
    """Delete a document from uploads and vector store."""
    file_path = UPLOADS_DIR / filename

    # Remove file
    if file_path.exists():
        file_path.unlink()

    # Remove from vector store
    try:
        vector_store = VectorStore()
        vector_store.delete_document(filename)
    except Exception as e:
        logger.warning(f"Failed to remove from vector store: {e}")

    # Clear cache
    cache = CacheService()
    cache.delete(f"doc_summary:{filename}")

    return {"message": f"Deleted {filename}", "filename": filename}
