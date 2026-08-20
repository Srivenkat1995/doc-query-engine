from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class SearchChunk:
    position: int
    content: str
    content_hash: str


def chunk_text(text: str, *, max_chars: int = 500) -> List[SearchChunk]:
    """Split source text into stable, non-empty line-aware chunks."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chunks: List[SearchChunk] = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if current and len(candidate) > max_chars:
            chunks.append(_make_chunk(len(chunks), current))
            current = line
        else:
            current = candidate
    if current:
        chunks.append(_make_chunk(len(chunks), current))
    return chunks


def _make_chunk(position: int, content: str) -> SearchChunk:
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return SearchChunk(position=position, content=content, content_hash=content_hash)
