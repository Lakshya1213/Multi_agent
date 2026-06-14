from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, TypeVar

from live_assist.core.config import get_settings

F = TypeVar("F", bound=Callable[..., Any])


def observe(name: str) -> Callable[[F], F]:
    """Return a Langfuse observe decorator when configured, otherwise no-op."""

    settings = get_settings()
    if not settings.langfuse_enabled:
        return lambda fn: fn
    try:
        if settings.langfuse_public_key:
            os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        if settings.langfuse_secret_key:
            os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        if settings.langfuse_base_url:
            os.environ["LANGFUSE_HOST"] = settings.langfuse_base_url
        from langfuse import observe as langfuse_observe

        return langfuse_observe(name=name)
    except Exception:
        return lambda fn: fn
