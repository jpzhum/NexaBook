from __future__ import annotations

from types import SimpleNamespace

from nexabook.providers import GoogleBooksProvider, OpenAIFallbackProvider, OpenLibraryProvider


class Response:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
    def json(self): return self.payload
    def raise_for_status(self):
        if self.status_code >= 400: raise RuntimeError("http error")


class Session:
    def __init__(self, response): self.response = response; self.calls = []
    def get(self, url, **kwargs): self.calls.append((url, kwargs)); return self.response


def test_google_books_maps_public_payload():
    session = Session(Response({"items": [{"volumeInfo": {"title": "Synthetic Book", "authors": ["Jordan Example"], "pageCount": 144}}]}))
    book = GoogleBooksProvider(session=session).fetch("9780000000002")
    assert book and book.title == "Synthetic Book"
    assert session.calls[0][1]["timeout"] == 8


def test_open_library_maps_public_payload():
    session = Session(Response({"title": "Open Example", "publishers": ["Aurora Press"]}))
    book = OpenLibraryProvider(session=session).fetch("9780000000002")
    assert book and book.publisher == "Aurora Press"


class Responses:
    def __init__(self, output): self.output = output
    def create(self, **kwargs): return SimpleNamespace(output_text=self.output)


def test_openai_fallback_validates_structured_json():
    client = SimpleNamespace(responses=Responses('{"title":"LLM Example","authors":["Casey Demo"]}'))
    book = OpenAIFallbackProvider(None, "test-model", client=client).fetch("9780000000002")
    assert book and book.isbn == "9780000000002" and book.title == "LLM Example"


def test_openai_fallback_fails_closed_on_invalid_output():
    client = SimpleNamespace(responses=Responses("not-json"))
    assert OpenAIFallbackProvider(None, "test-model", client=client).fetch("9780000000002") is None
