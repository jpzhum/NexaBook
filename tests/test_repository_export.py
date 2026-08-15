from pathlib import Path

import pandas as pd

from nexabook.export import export_books
from nexabook.models import BookMetadata
from nexabook.repository import BookRepository


def test_empty_database_and_synthetic_persistence(tmp_path: Path):
    repository = BookRepository(tmp_path / "books.db")
    repository.initialize()
    repository.add(BookMetadata(isbn="9780000000002", title="Synthetic Book", authors=["Morgan Example"], sources=["fixture"]))
    rows = repository.list_all()
    assert len(rows) == 1
    assert rows[0]["authors"] == ["Morgan Example"]


def test_duplicate_isbn_updates_the_existing_record(tmp_path: Path):
    repository = BookRepository(tmp_path / "books.db")
    repository.initialize()
    first_id = repository.add(
        BookMetadata(
            isbn="9780000000002",
            title="First",
            publisher="Aurora Press",
            sources=["catalog_api"],
        )
    )
    second_id = repository.add(
        BookMetadata(
            isbn="9780000000002",
            title="Updated",
            sources=["open_catalog"],
        )
    )
    rows = repository.list_all()
    assert first_id == second_id
    assert len(rows) == 1
    assert rows[0]["title"] == "Updated"
    assert rows[0]["publisher"] == "Aurora Press"
    assert rows[0]["sources"] == ["catalog_api", "open_catalog"]


def test_csv_and_xlsx_exports_use_generic_schema(tmp_path: Path):
    rows = [{"isbn": "9780000000002", "title": "Synthetic Book", "authors": ["Morgan Example"], "sources": ["fixture"]}]
    csv_path = export_books(rows, tmp_path, "csv")
    xlsx_path = export_books(rows, tmp_path, "xlsx")
    assert list(pd.read_csv(csv_path).columns) == ["isbn", "title", "authors", "publisher", "published_date", "page_count", "language", "sources"]
    assert pd.read_excel(xlsx_path).iloc[0]["title"] == "Synthetic Book"


def test_exports_neutralize_spreadsheet_formulas(tmp_path: Path):
    rows = [
        {
            "isbn": "9780000000002",
            "title": "=HYPERLINK(\"https://example.invalid\")",
            "authors": ["+cmd"],
            "publisher": "-cmd",
            "published_date": "@cmd",
            "language": " \t=cmd",
            "sources": ["fixture"],
        }
    ]
    csv_path = export_books(rows, tmp_path, "csv")
    csv_record = pd.read_csv(csv_path).iloc[0]
    assert csv_record["title"].startswith("'=")
    assert csv_record["authors"].startswith("'+")
    assert csv_record["publisher"].startswith("'-")
    assert csv_record["published_date"].startswith("'@")
    assert csv_record["language"].startswith("' \t=")

    xlsx_path = export_books(rows, tmp_path, "xlsx")
    exported = pd.read_excel(xlsx_path).iloc[0]
    assert exported["title"].startswith("'=")
    assert exported["authors"].startswith("'+")
    assert exported["publisher"].startswith("'-")
    assert exported["published_date"].startswith("'@")
    assert exported["language"].startswith("' \t=")
