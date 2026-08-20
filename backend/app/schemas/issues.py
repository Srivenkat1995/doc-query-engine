from typing import Dict, List

from pydantic import BaseModel


class IssueResponse(BaseModel):
    code: str
    message: str
    details: Dict[str, str]


class IssuesResponse(BaseModel):
    invoice_id: str
    issues: List[IssueResponse]
