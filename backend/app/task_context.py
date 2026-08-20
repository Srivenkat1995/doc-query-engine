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


@dataclass(frozen=True)
class ProcessingTaskPayload:
    """JSON-safe payload for the first invoice processing task."""

    context: TaskContext
    storage_key: str

    def to_payload(self) -> dict[str, str]:
        return {**self.context.to_payload(), "storage_key": self.storage_key}

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ProcessingTaskPayload":
        storage_key = payload.get("storage_key")
        if not isinstance(storage_key, str) or not storage_key:
            raise ValueError("Processing task requires a non-empty storage_key")
        return cls(TaskContext.from_payload(payload), storage_key)
