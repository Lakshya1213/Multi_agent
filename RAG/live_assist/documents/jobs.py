from __future__ import annotations

import time

from live_assist.core.models import JobStage, JobStatusResponse
from live_assist.documents import storage


def create_job(*, job_id: str, document_id: str, user_id: str, filename: str) -> JobStatusResponse:
    now = time.time()
    job = JobStatusResponse(
        job_id=job_id,
        document_id=document_id,
        user_id=user_id,
        filename=filename,
        status="queued",
        submitted_at=now,
        updated_at=now,
    )
    storage.save_job(job)
    return job


def append_stage(job_id: str, stage: str, message: str) -> JobStatusResponse | None:
    job = storage.get_job(job_id)
    if not job:
        return None
    stages = list(job.stages)
    stages.append(JobStage(stage=stage, message=message, ts=time.time()))
    return storage.touch_job(job, stages=stages)


def update_job(job_id: str, **updates) -> JobStatusResponse | None:
    job = storage.get_job(job_id)
    if not job:
        return None
    return storage.touch_job(job, **updates)


def get_job(job_id: str) -> JobStatusResponse | None:
    return storage.get_job(job_id)

