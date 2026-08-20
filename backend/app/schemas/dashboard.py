from datetime import datetime
from typing import List

from pydantic import BaseModel


class InvoiceSummary(BaseModel):
    id: str
    original_filename: str
    status: str
    size_bytes: int
    flag_count: int
    issue_count: int
    created_at: datetime


class DashboardResponse(BaseModel):
    invoices: List[InvoiceSummary]
    total_count: int
    needs_review_count: int
    failed_count: int
