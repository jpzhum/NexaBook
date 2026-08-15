from __future__ import annotations

import pytest
import requests

from nexabook.models import BookMetadata
from nexabook.services import EnrichmentService, normalize_isbn


class FakeProvider:
    def __init__(self, name: str, result: BookMetadata | None) -> None:
        self.name = name
        self.result = result
        self.calls = 0

    def fetch(self, isbn: str):
        self.calls += 1
        return self.result


def test_normalize_isbn_accepts_display_format():
    assert normalize_isbn("978-0-00-000000-2") == "9780000000002"
    assert normalize_isbn("0-306-40615-2") == "0306406152"
    assert normalize_isbn("0 8044 2957 x") == "080442957X"


@pytest.mark.parametrize(
    "isbn",
    [
        "9780000000003",
        "0306406153",
        "X306406152",
        "123",
        "ISBN 978-0-00-000000-2",
        "978_0_00_000000_2",
        "９７８０００００００００２",
    ],
)
def test_normalize_isbn_rejects_invalid_format_or_checksum(isbn):
    with pytest.raises(ValueError):
        normalize_isbn(isbn)


def test_pipeline_merges_missing_fields_in_provider_order():
    first = FakeProvider("catalog_api", BookMetadata(title="Synthetic Systems", authors=["Alex Example"]))
    second = FakeProvider("open_catalog", BookMetadata(publisher="Aurora Press", description="Synthetic metadata."))
    result = EnrichmentService([first, second], minimum_fields=4).enrich("9780000000002")
    assert result.title == "Synthetic Systems"
    assert result.publisher == "Aurora Press"
    assert result.sources == ["catalog_api", "open_catalog"]


def test_pipeline_stops_when_quality_threshold_is_reached():
    first = FakeProvider("complete", BookMetadata(title="Example", authors=["Taylor Demo"], publisher="Horizon Press"))
    unused = FakeProvider("unused", BookMetadata(title="Must not replace"))
    result = EnrichmentService([first, unused], minimum_fields=3).enrich("9780000000002")
    assert result.title == "Example"
    assert unused.calls == 0


def test_sources_only_include_providers_that_contributed_metadata():
    first = FakeProvider(
        "catalog_api",
        BookMetadata(title="Synthetic Systems", authors=["Alex Example"]),
    )
    redundant = FakeProvider(
        "redundant_catalog",
        BookMetadata(title="Synthetic Systems", authors=["Alex Example"]),
    )
    page_count = FakeProvider("page_catalog", BookMetadata(page_count=144))

    result = EnrichmentService([first, redundant, page_count], minimum_fields=5).enrich(
        "9780000000002"
    )

    assert result.page_count == 144
    assert result.sources == ["catalog_api", "page_catalog"]


class UnavailableProvider:
    name = "unavailable"

    def fetch(self, isbn: str):
        raise requests.Timeout("provider timeout")


class BrokenProvider:
    name = "broken"

    def fetch(self, isbn: str):
        raise AttributeError("programming error")


def test_expected_provider_failure_preserves_collected_metadata():
    first = FakeProvider(
        "catalog_api",
        BookMetadata(title="Synthetic Systems", authors=["Alex Example"]),
    )

    result = EnrichmentService([first, UnavailableProvider()], minimum_fields=5).enrich(
        "9780000000002"
    )

    assert result.title == "Synthetic Systems"
    assert result.sources == ["catalog_api"]


def test_unexpected_programming_errors_are_not_hidden():
    with pytest.raises(AttributeError, match="programming error"):
        EnrichmentService([BrokenProvider()]).enrich("9780000000002")
