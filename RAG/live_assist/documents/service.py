from __future__ import annotations

import shutil
import time
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from live_assist.core.config import get_settings
from live_assist.core.models import DocumentInfo
from live_assist.documents import jobs, paths, storage
from live_assist.ingestion.pipeline import ingest_pdf


def _validate_upload(file: UploadFile, user_id: str) -> None:
    settings = get_settings()
    allowed = {item.strip().lower() for item in settings.document_allowed_types.split(",")}
    suffix = Path(file.filename or "").suffix.lower().lstrip(".")
    if suffix not in allowed or suffix != "pdf":
        raise HTTPException(status_code=400, detail="Only PDF uploads are accepted.")
    if len(storage.list_documents(user_id)) >= settings.document_upload_max_count:
        raise HTTPException(status_code=400, detail="Document upload limit reached.")


def create_upload_job(file: UploadFile, user_id: str) -> tuple[str, str, Path]:
    _validate_upload(file, user_id)
    filename = Path(file.filename or "document.pdf").name
    document_id = str(uuid.uuid4())
    job_id = f"{int(time.time())}_{document_id[:8]}"
    pdf_path = paths.upload_dir() / f"{document_id}_{filename}"
    max_bytes = get_settings().document_upload_max_mb * 1024 * 1024

    bytes_written = 0
    with pdf_path.open("wb") as output:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > max_bytes:
                output.close()
                pdf_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="Uploaded PDF exceeds size limit.")
            output.write(chunk)

    now = time.time()
    storage.save_document(
        DocumentInfo(
            document_id=document_id,
            user_id=user_id,
            filename=filename,
            status="ingesting",
            uploaded_at=now,
            metadata={"job_id": job_id, "size_bytes": bytes_written},
        )
    )
    jobs.create_job(job_id=job_id, document_id=document_id, user_id=user_id, filename=filename)
    return job_id, document_id, pdf_path


def run_ingestion_job(*, job_id: str, document_id: str, user_id: str, filename: str, pdf_path: Path) -> None:
    jobs.update_job(job_id, status="running")

    def on_progress(stage: str, message: str) -> None:
        jobs.append_stage(job_id, stage, message)

    result = ingest_pdf(
        pdf_path=pdf_path,
        user_id=user_id,
        document_id=document_id,
        source_filename=filename,
        on_progress=on_progress,
    )
    status = str(result.get("status") or "error")
    error = result.get("error")
    chunk_count = int(result.get("chunk_count") or 0)
    total_tokens = int(result.get("total_tokens") or 0)
    jobs.update_job(
        job_id,
        status=status,
        chunk_count=chunk_count,
        total_tokens=total_tokens,
        error=error,
    )
    storage.save_document(
        DocumentInfo(
            document_id=document_id,
            user_id=user_id,
            filename=filename,
            status="ready" if status == "ok" else "error",
            uploaded_at=time.time(),
            chunk_count=chunk_count,
            total_tokens=total_tokens,
            error=error,
            metadata={"job_id": job_id, "ingestion": result},
        )
    )

