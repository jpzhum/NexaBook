from __future__ import annotations

from nexabook.models import BookMetadata
from nexabook.services import EnrichmentService, normalize_isbn
import pytest


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


@pytest.mark.parametrize("isbn", ["9780000000003", "0306406153", "X306406152", "123"])
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
