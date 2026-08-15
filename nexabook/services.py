from __future__ import annotations

import requests
from pydantic import ValidationError

from .models import BookMetadata, normalize_isbn
from .providers import MetadataProvider


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
            except (requests.RequestException, ValidationError, TypeError, KeyError, AttributeError):
                candidate = None
            if candidate:
                result.merge_missing(candidate, provider.name)
            populated = sum(bool(getattr(result, field)) for field in ("title", "authors", "publisher", "description", "page_count"))
            if populated >= self.minimum_fields:
                break
        return result
