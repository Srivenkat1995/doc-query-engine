from typing import List, Optional

from pydantic import BaseModel


class SearchResult(BaseModel):
    invoice_id: str
    chunk_id: str
    content: str
    content_hash: str
    score: float
    vendor: Optional[str]
    total: Optional[float]
    citation_ids: List[str]


class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
