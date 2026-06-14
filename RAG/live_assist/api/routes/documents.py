from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from live_assist.core.config import get_settings
from live_assist.core.models import DocumentListResponse, DocumentUploadResponse, JobStatusResponse
from live_assist.documents import jobs, service, storage

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    settings = get_settings()
    user_id = settings.live_feedback_user_id
    job_id, document_id, pdf_path = service.create_upload_job(file, user_id)
    background_tasks.add_task(
        asyncio.to_thread,
        service.run_ingestion_job,
        job_id=job_id,
        document_id=document_id,
        user_id=user_id,
        filename=file.filename or "document.pdf",
        pdf_path=pdf_path,
    )
    return DocumentUploadResponse(
        status="queued",
        job_id=job_id,
        document_id=document_id,
        filename=file.filename or "document.pdf",
        message="PDF ingestion started.",
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_document_job(job_id: str) -> JobStatusResponse:
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@router.get("", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    settings = get_settings()
    return DocumentListResponse(documents=storage.list_documents(settings.live_feedback_user_id))

