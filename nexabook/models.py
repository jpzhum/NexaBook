from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def normalize_isbn(value: str) -> str:
    cleaned = "".join(ch for ch in value.upper() if ch.isdigit() or ch == "X")
    if len(cleaned) == 10:
        if "X" in cleaned[:-1] or sum((10 - index) * (10 if char == "X" else int(char)) for index, char in enumerate(cleaned)) % 11:
            raise ValueError("Invalid ISBN-10 checksum")
    elif len(cleaned) == 13:
        if "X" in cleaned or sum(int(char) * (1 if index % 2 == 0 else 3) for index, char in enumerate(cleaned)) % 10:
            raise ValueError("Invalid ISBN-13 checksum")
    else:
        raise ValueError("ISBN must contain 10 or 13 characters")
    return cleaned


class BookMetadata(BaseModel):
    isbn: str = ""
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    publisher: str = ""
    published_date: str = ""
    description: str = ""
    page_count: int | None = Field(default=None, ge=0)
    language: str = ""
    cover_url: str = ""
    sources: list[str] = Field(default_factory=list)

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, value: str) -> str:
        return normalize_isbn(value) if value else value

    @field_validator("title", "publisher", "published_date", "description", "language", "cover_url")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("authors", "sources")
    @classmethod
    def clean_string_lists(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]

    def merge_missing(self, other: "BookMetadata", source: str) -> None:
        for field in ("isbn", "title", "publisher", "published_date", "description", "page_count", "language", "cover_url"):
            if not getattr(self, field) and getattr(other, field):
                setattr(self, field, getattr(other, field))
        if not self.authors and other.authors:
            self.authors = list(other.authors)
        if any(getattr(other, field) for field in ("title", "authors", "publisher", "description")) and source not in self.sources:
            self.sources.append(source)
