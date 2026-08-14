from __future__ import annotations

import json
from typing import Protocol

import requests
from openai import OpenAI

from .models import BookMetadata


class MetadataProvider(Protocol):
    name: str
    def fetch(self, isbn: str) -> BookMetadata | None: ...


class GoogleBooksProvider:
    name = "google_books"

    def __init__(self, api_key: str | None = None, session: requests.Session | None = None) -> None:
        self.api_key = api_key
        self.session = session or requests.Session()

    def fetch(self, isbn: str) -> BookMetadata | None:
        params = {"q": f"isbn:{isbn}", "maxResults": 1}
        if self.api_key:
            params["key"] = self.api_key
        response = self.session.get("https://www.googleapis.com/books/v1/volumes", params=params, timeout=8)
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return None
        info = items[0].get("volumeInfo", {})
        return BookMetadata(
            isbn=isbn, title=info.get("title", ""), authors=info.get("authors", []),
            publisher=info.get("publisher", ""), published_date=info.get("publishedDate", ""),
            description=info.get("description", ""), page_count=info.get("pageCount"),
            language=info.get("language", ""), cover_url=info.get("imageLinks", {}).get("thumbnail", ""),
        )


class OpenLibraryProvider:
    name = "open_library"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    def fetch(self, isbn: str) -> BookMetadata | None:
        response = self.session.get(f"https://openlibrary.org/isbn/{isbn}.json", timeout=8)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return BookMetadata(
            isbn=isbn, title=data.get("title", ""),
            publisher=(data.get("publishers") or [""])[0], published_date=data.get("publish_date", ""),
            page_count=data.get("number_of_pages"), cover_url=f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg",
        )


class OpenAIFallbackProvider:
    name = "openai_fallback"

    def __init__(self, api_key: str | None, model: str, client: OpenAI | None = None) -> None:
        self.client = client or (OpenAI(api_key=api_key) if api_key else None)
        self.model = model

    def fetch(self, isbn: str) -> BookMetadata | None:
        if not self.client:
            return None
        prompt = (
            "Return only JSON with keys isbn,title,authors,publisher,published_date,description,page_count,language,cover_url. "
            f"Use empty values when uncertain. Book ISBN: {isbn}"
        )
        try:
            response = self.client.responses.create(model=self.model, input=prompt)
            data = json.loads(response.output_text)
            data["isbn"] = isbn
            return BookMetadata.model_validate(data)
        except Exception:
            # The fallback is optional: SDK/network errors and invalid model output
            # must never discard metadata already obtained from deterministic APIs.
            return None
