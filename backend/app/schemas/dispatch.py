from pydantic import BaseModel


class DispatchResponse(BaseModel):
    job_id: str
    invoice_id: str
    accepted: bool
    trace_id: str
