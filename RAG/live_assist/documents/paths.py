from __future__ import annotations

from pathlib import Path

from live_assist.core.config import BACKEND_DIR, get_settings


def runtime_dir() -> Path:
    settings = get_settings()
    path = Path(settings.rag_runtime_dir)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def upload_dir() -> Path:
    path = runtime_dir() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def chunks_dir() -> Path:
    path = runtime_dir() / "chunks"
    path.mkdir(parents=True, exist_ok=True)
    return path


def bm25_dir() -> Path:
    path = runtime_dir() / "bm25"
    path.mkdir(parents=True, exist_ok=True)
    return path


def chroma_dir() -> Path:
    path = runtime_dir() / "chroma_db"
    path.mkdir(parents=True, exist_ok=True)
    return path

