import json
import logging
from time import perf_counter
from typing import Any, Optional

logger = logging.getLogger("doc_query_engine.http")


def log_request(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    trace_id: str,
    event_name: str = "http_request_completed",
    error_type: Optional[str] = None,
) -> None:
    """Emit a JSON request event without request contents or sensitive headers."""

    event: dict[str, Any] = {
        "event": event_name,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "trace_id": trace_id,
    }
    if error_type is not None:
        event["error_type"] = error_type
    logger.info(json.dumps(event, sort_keys=True))


def request_timer() -> float:
    """Return a monotonic timestamp for request duration measurement."""

    return perf_counter()
