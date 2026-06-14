from __future__ import annotations

from live_assist.core.config import Settings, get_settings
from live_assist.providers.rag.advanced import AdvancedRetriever
from live_assist.providers.rag.legacy_chroma import LegacyChromaRetriever


def build_rag_retriever(settings: Settings | None = None):
    settings = settings or get_settings()
    if settings.rag_provider == "advanced":
        return AdvancedRetriever(settings)
    return LegacyChromaRetriever(settings.workflow_config())

