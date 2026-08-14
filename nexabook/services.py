from __future__ import annotations

from .models import BookMetadata
from .providers import MetadataProvider


def normalize_isbn(value: str) -> str:
    cleaned = "".join(ch for ch in value if ch.isdigit() or ch.upper() == "X")
    if len(cleaned) not in {10, 13}:
        raise ValueError("ISBN must contain 10 or 13 characters")
    return cleaned


class EnrichmentService:
    def __init__(self, providers: list[MetadataProvider], minimum_fields: int = 3) -> None:
        self.providers = providers
        self.minimum_fields = minimum_fields

    def enrich(self, raw_isbn: str) -> BookMetadata:
        isbn = normalize_isbn(raw_isbn)
        result = BookMetadata(isbn=isbn)
        for provider in self.providers:
            try:
                candidate = provider.fetch(isbn)
            except requests.RequestException:
                candidate = None
            if candidate:
                result.merge_missing(candidate, provider.name)
            populated = sum(bool(getattr(result, field)) for field in ("title", "authors", "publisher", "description", "page_count"))
            if populated >= self.minimum_fields:
                break
        return result


import requests  # kept below domain declarations to make the handled integration failure explicit
