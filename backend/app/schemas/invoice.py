from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import InvoiceStatus


class InvoiceCreate(BaseModel):
    original_filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(ge=0)
    storage_key: Optional[str] = Field(default=None, max_length=512)
    vendor: Optional[str] = Field(default=None, max_length=255)
    total: Optional[float] = Field(default=None, ge=0)
    due_date: Optional[str] = Field(default=None, max_length=32)


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    mime_type: str
    size_bytes: int
    storage_key: Optional[str]
    vendor: Optional[str]
    total: Optional[float]
    due_date: Optional[str]
    status: InvoiceStatus
    failure_reason: Optional[str]
    created_at: datetime
    updated_at: datetime