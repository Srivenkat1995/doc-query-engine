from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models import InvoiceStatus, JobStatus


class ProcessingStatusResponse(BaseModel):
    invoice_id: str
    job_id: str
    invoice_status: InvoiceStatus
    job_status: JobStatus
    attempt_count: int
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
