from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class InvoiceSummary(BaseModel):
    id: str
    original_filename: str
    status: str
    size_bytes: int
    vendor: Optional[str]
    total: Optional[float]
    due_date: Optional[str]
    flag_count: int
    issue_count: int
    created_at: datetime


class DashboardResponse(BaseModel):
    invoices: List[InvoiceSummary]
    total_count: int
    needs_review_count: int
    failed_count: int
