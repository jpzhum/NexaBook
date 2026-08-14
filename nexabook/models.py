from __future__ import annotations

from pydantic import BaseModel, Field


class BookMetadata(BaseModel):
    isbn: str = ""
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    publisher: str = ""
    published_date: str = ""
    description: str = ""
    page_count: int | None = None
    language: str = ""
    cover_url: str = ""
    sources: list[str] = Field(default_factory=list)

    def merge_missing(self, other: "BookMetadata", source: str) -> None:
        for field in ("isbn", "title", "publisher", "published_date", "description", "page_count", "language", "cover_url"):
            if not getattr(self, field) and getattr(other, field):
                setattr(self, field, getattr(other, field))
        if not self.authors and other.authors:
            self.authors = list(other.authors)
        if any(getattr(other, field) for field in ("title", "authors", "publisher", "description")) and source not in self.sources:
            self.sources.append(source)
