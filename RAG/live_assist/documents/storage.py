from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from live_assist.core.models import DocumentInfo, JobStatusResponse
from live_assist.storage.sqlite import _db_path


def save_document(info: DocumentInfo) -> None:
    db_path = _db_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO documents(
                document_id, user_id, filename, status, uploaded_at,
                chunk_count, total_tokens, error, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                user_id=excluded.user_id,
                filename=excluded.filename,
                status=excluded.status,
                uploaded_at=excluded.uploaded_at,
                chunk_count=excluded.chunk_count,
                total_tokens=excluded.total_tokens,
                error=excluded.error,
                metadata_json=excluded.metadata_json
            """,
            (
                info.document_id,
                info.user_id,
                info.filename,
                info.status,
                info.uploaded_at,
                info.chunk_count,
                info.total_tokens,
                info.error,
                json.dumps(info.metadata, ensure_ascii=True),
            ),
        )
        conn.commit()


def list_documents(user_id: str) -> list[DocumentInfo]:
    db_path = _db_path()
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT document_id, user_id, filename, status, uploaded_at,
                   chunk_count, total_tokens, error, metadata_json
            FROM documents
            WHERE user_id = ?
            ORDER BY uploaded_at DESC
            """,
            (user_id,),
        ).fetchall()

    documents = []
    for row in rows:
        metadata: dict[str, Any] = {}
        if row[8]:
            try:
                metadata = json.loads(row[8])
            except json.JSONDecodeError:
                metadata = {"raw": row[8]}
        documents.append(
            DocumentInfo(
                document_id=row[0],
                user_id=row[1],
                filename=row[2],
                status=row[3],
                uploaded_at=row[4],
                chunk_count=row[5],
                total_tokens=row[6],
                error=row[7],
                metadata=metadata,
            )
        )
    return documents


def save_job(job: JobStatusResponse) -> None:
    db_path = _db_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO document_jobs(
                job_id, document_id, user_id, filename, status, submitted_at,
                updated_at, stages_json, chunk_count, total_tokens, error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                status=excluded.status,
                updated_at=excluded.updated_at,
                stages_json=excluded.stages_json,
                chunk_count=excluded.chunk_count,
                total_tokens=excluded.total_tokens,
                error=excluded.error
            """,
            (
                job.job_id,
                job.document_id,
                job.user_id,
                job.filename,
                job.status,
                job.submitted_at,
                job.updated_at,
                job.model_dump_json(),
                job.chunk_count,
                job.total_tokens,
                job.error,
            ),
        )
        conn.commit()


def get_job(job_id: str) -> JobStatusResponse | None:
    db_path = _db_path()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT stages_json FROM document_jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
    if not row:
        return None
    return JobStatusResponse.model_validate_json(row[0])


def touch_job(job: JobStatusResponse, **updates: Any) -> JobStatusResponse:
    data = job.model_dump()
    data.update(updates)
    data["updated_at"] = time.time()
    updated = JobStatusResponse(**data)
    save_job(updated)
    return updated

