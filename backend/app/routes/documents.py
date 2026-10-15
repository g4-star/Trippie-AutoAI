import hashlib
import logging
import os
import re
import secrets
from datetime import datetime
from io import BytesIO
from pathlib import PurePath
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pypdf import PdfReader
from sqlalchemy.orm import Session
from vercel.blob import AsyncBlobClient

from app.database import get_db
from app.models.user import User
from app.models.user_document import UserDocument
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/documents", tags=["Documents"])
logger = logging.getLogger(__name__)

MAX_CV_BYTES = 4 * 1024 * 1024
MAX_PDF_PAGES = 100
MAX_EXTRACTED_CHARS = 200_000


def _blob_token() -> str:
    token = os.environ.get("BLOB_READ_WRITE_TOKEN", "").strip()
    if not token:
        raise HTTPException(
            status_code=503,
            detail="Private document storage is not configured.",
        )
    return token


def _metadata(document: UserDocument | None):
    if document is None:
        return None

    return {
        "id": document.id,
        "document_type": document.document_type,
        "filename": document.original_filename,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
        "text_extracted": bool(document.extracted_text.strip()),
    }


def _parse_pdf(content: bytes) -> str:
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=415, detail="The uploaded file is not a valid PDF."
        )

    try:
        reader = PdfReader(BytesIO(content), strict=True)
        if reader.is_encrypted:
            raise HTTPException(
                status_code=422,
                detail="Password-protected PDFs are not supported.",
            )
        if len(reader.pages) > MAX_PDF_PAGES:
            raise HTTPException(
                status_code=422,
                detail=f"PDFs may contain at most {MAX_PDF_PAGES} pages.",
            )

        parts = []
        total = 0
        for page in reader.pages:
            if total >= MAX_EXTRACTED_CHARS:
                break
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            remaining = MAX_EXTRACTED_CHARS - total
            text = text[:remaining]
            parts.append(text)
            total += len(text)

        # Scanned PDFs may have no embedded text. Keep the file usable;
        # OCR is not performed by this endpoint.
        return "\n".join(parts).strip()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="The PDF could not be read. Please choose a valid PDF.",
        ) from None


def _safe_filename(filename: str | None) -> str:
    name = PurePath((filename or "cv.pdf").replace("\\", "/")).name
    name = re.sub(r"[\r\n\x00]", "", name).strip()
    if not name:
        name = "cv.pdf"
    if len(name) > 180:
        name = name[-180:]
    return name


@router.get("/cv")
def get_cv(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = (
        db.query(UserDocument)
        .filter_by(user_id=user.id, document_type="cv")
        .first()
    )
    return {"document": _metadata(document)}


@router.post("/cv")
async def upload_cv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filename = _safe_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=415, detail="Please upload your CV as a PDF."
        )

    content = await file.read(MAX_CV_BYTES + 1)
    await file.close()

    if not content:
        raise HTTPException(status_code=400, detail="The selected file is empty.")
    if len(content) > MAX_CV_BYTES:
        raise HTTPException(
            status_code=413,
            detail="CV PDFs must be 4 MB or smaller.",
        )

    extracted_text = _parse_pdf(content)
    token = _blob_token()

    existing = (
        db.query(UserDocument)
        .filter_by(user_id=user.id, document_type="cv")
        .first()
    )

    # Random object names avoid storing a person's original filename in
    # the storage pathname. Never return the Blob URL to the client.
    pathname = f"private-documents/user-{user.id}/{secrets.token_hex(24)}.pdf"
    new_path = pathname

    try:
        async with AsyncBlobClient(token=token) as client:
            result = await client.put(
                pathname,
                content,
                access="private",
                content_type="application/pdf",
                add_random_suffix=False,
            )
            new_path = getattr(result, "pathname", None) or pathname
    except Exception:
        logger.error("Private CV upload failed for user_id=%s", user.id)
        raise HTTPException(
            status_code=502,
            detail="CV storage failed. Please try again later.",
        ) from None

    old_path = existing.blob_pathname if existing else None
    now = datetime.utcnow()

    try:
        if existing:
            existing.original_filename = filename
            existing.blob_pathname = new_path
            existing.mime_type = "application/pdf"
            existing.size_bytes = len(content)
            existing.sha256_hex = hashlib.sha256(content).hexdigest()
            existing.extracted_text = extracted_text
            existing.updated_at = now
            document = existing
        else:
            document = UserDocument(
                user_id=user.id,
                document_type="cv",
                original_filename=filename,
                blob_pathname=new_path,
                mime_type="application/pdf",
                size_bytes=len(content),
                sha256_hex=hashlib.sha256(content).hexdigest(),
                extracted_text=extracted_text,
            )
            db.add(document)

        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        try:
            async with AsyncBlobClient(token=token) as client:
                await client.delete(new_path, token=token)
        except Exception:
            logger.error(
                "Orphaned CV cleanup failed for user_id=%s", user.id
            )
        logger.error("CV metadata save failed for user_id=%s", user.id)
        raise HTTPException(
            status_code=500,
            detail="CV metadata could not be saved.",
        ) from None

    # The replacement is committed before attempting to remove the old
    # object. A cleanup failure must not invalidate the saved CV.
    if old_path and old_path != new_path:
        try:
            async with AsyncBlobClient(token=token) as client:
                await client.delete(old_path, token=token)
        except Exception:
            logger.error("Old CV cleanup failed for user_id=%s", user.id)

    return {"document": _metadata(document)}


@router.get("/cv/download")
async def download_cv(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = (
        db.query(UserDocument)
        .filter_by(user_id=user.id, document_type="cv")
        .first()
    )
    if document is None:
        raise HTTPException(status_code=404, detail="No CV has been uploaded.")

    token = _blob_token()
    try:
        async with AsyncBlobClient(token=token) as client:
            result = await client.get(
                document.blob_pathname,
                access="private",
                use_cache=False,
            )
        content = result.content
    except Exception:
        logger.error("Private CV download failed for user_id=%s", user.id)
        raise HTTPException(
            status_code=502,
            detail="CV download failed. Please try again later.",
        ) from None

    encoded_name = quote(document.original_filename, safe="")
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="cv.pdf"; '
                f"filename*=UTF-8''{encoded_name}"
            ),
            "Cache-Control": "private, no-store",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete("/cv", status_code=204)
async def delete_cv(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = (
        db.query(UserDocument)
        .filter_by(user_id=user.id, document_type="cv")
        .first()
    )
    if document is None:
        return Response(status_code=204)

    token = _blob_token()
    try:
        async with AsyncBlobClient(token=token) as client:
            await client.delete(document.blob_pathname, token=token)
    except Exception:
        logger.error("Private CV deletion failed for user_id=%s", user.id)
        raise HTTPException(
            status_code=502,
            detail="CV could not be deleted from storage. Please retry.",
        ) from None

    db.delete(document)
    db.commit()
    return Response(status_code=204)
