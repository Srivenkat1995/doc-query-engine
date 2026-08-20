from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class TaskContext:
    """Correlation data that travels with every background task."""

    trace_id: str
    invoice_id: str
    job_id: str

    def to_payload(self) -> dict[str, str]:
        """Return a JSON-serializable Celery payload."""

        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "TaskContext":
        """Validate and reconstruct context received by a worker."""

        values = {
            name: payload.get(name)
            for name in ("trace_id", "invoice_id", "job_id")
        }
        if not all(isinstance(value, str) and value for value in values.values()):
            raise ValueError(
                "Task context requires non-empty trace_id, invoice_id, and job_id"
            )
        return cls(**values)
