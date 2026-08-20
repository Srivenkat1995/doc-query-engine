from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import JobStatus


class JobCreate(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=128)


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str
    idempotency_key: str
    status: JobStatus
    attempt_count: int
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
