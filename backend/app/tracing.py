from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from fastapi import Request

TRACE_ID_HEADER = "X-Trace-Id"


def normalize_trace_id(value: Optional[str]) -> str:
    """Return a canonical incoming trace ID or generate a UUID4."""

    if value:
        try:
            return str(UUID(value))
        except ValueError:
            pass
    return str(uuid4())


def get_trace_id(request: Request) -> str:
    """Read the trace ID assigned by the request middleware."""

    return request.state.trace_id
