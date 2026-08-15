from __future__ import annotations

from types import SimpleNamespace

from openai import APIError

from nexabook.models import BookMetadata
from nexabook.providers import GoogleBooksProvider, OpenAIFallbackProvider, OpenLibraryProvider
from nexabook.services import EnrichmentService


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
    assert session.calls[0][1]["timeout"] == 8


def test_providers_reject_unexpected_payload_shapes():
    assert GoogleBooksProvider(session=Session(Response([]))).fetch("9780000000002") is None
    assert OpenLibraryProvider(session=Session(Response([]))).fetch("9780000000002") is None


class Responses:
    def __init__(self, output):
        self.output = output
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.output)


class FailingResponses:
    def create(self, **kwargs):
        raise APIError("unavailable", request=None, body=None)


class DeterministicProvider:
    name = "catalog_api"

    def fetch(self, isbn: str):
        return BookMetadata(
            isbn=isbn,
            title="Deterministic title",
            authors=["Alex Example"],
        )


def test_openai_fallback_validates_json_response():
    responses = Responses('{"title":"LLM Example","authors":["Casey Demo"]}')
    client = SimpleNamespace(responses=responses)
    book = OpenAIFallbackProvider(None, "test-model", client=client).fetch("9780000000002")
    assert book and book.isbn == "9780000000002" and book.title == "LLM Example"
    assert len(responses.calls) == 1
    assert responses.calls[0]["model"] == "test-model"
    assert "9780000000002" in responses.calls[0]["input"]
    assert responses.calls[0]["max_output_tokens"] == 800
    assert responses.calls[0]["store"] is False


def test_openai_fallback_without_api_key_is_inert():
    provider = OpenAIFallbackProvider(None, "test-model")

    assert provider.fetch("9780000000002") is None


def test_openai_sdk_client_has_bounded_retry_policy(monkeypatch):
    captured = {}
    fake_client = SimpleNamespace(responses=Responses("{}"))

    def build_client(**kwargs):
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr("nexabook.providers.OpenAI", build_client)

    OpenAIFallbackProvider("synthetic-key", "test-model")

    assert captured == {
        "api_key": "synthetic-key",
        "timeout": 8.0,
        "max_retries": 2,
    }


def test_openai_fallback_fails_closed_on_invalid_output():
    client = SimpleNamespace(responses=Responses("not-json"))
    assert OpenAIFallbackProvider(None, "test-model", client=client).fetch("9780000000002") is None


def test_openai_fallback_rejects_unexpected_fields():
    client = SimpleNamespace(responses=Responses('{"title":"LLM Example","unsupported":"value"}'))
    assert OpenAIFallbackProvider(None, "test-model", client=client).fetch("9780000000002") is None


def test_openai_fallback_fails_closed_on_api_error():
    client = SimpleNamespace(responses=FailingResponses())
    assert OpenAIFallbackProvider(None, "test-model", client=client).fetch("9780000000002") is None


def test_openai_failure_preserves_deterministic_provider_metadata():
    client = SimpleNamespace(responses=FailingResponses())
    openai_provider = OpenAIFallbackProvider(None, "test-model", client=client)

    book = EnrichmentService(
        [DeterministicProvider(), openai_provider], minimum_fields=5
    ).enrich("9780000000002")

    assert book.title == "Deterministic title"
    assert book.authors == ["Alex Example"]
    assert book.sources == ["catalog_api"]


def test_provider_mappings_tolerate_malformed_optional_nested_fields():
    google = GoogleBooksProvider(
        session=Session(Response({"items": [{"volumeInfo": {"title": "Synthetic", "imageLinks": None}}]}))
    ).fetch("9780000000002")
    library = OpenLibraryProvider(
        session=Session(Response({"title": "Open Example", "publishers": "not-a-list"}))
    ).fetch("9780000000002")

    assert google and google.cover_url == ""
    assert library and library.publisher == ""
