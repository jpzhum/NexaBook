from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import BookMetadata


SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    publisher TEXT NOT NULL,
    published_date TEXT NOT NULL,
    description TEXT NOT NULL,
    page_count INTEGER,
    language TEXT NOT NULL,
    cover_url TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


class BookRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(SCHEMA)
            connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS books_isbn_unique ON books(isbn)")

    def add(self, book: BookMetadata) -> int:
        with sqlite3.connect(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT sources_json FROM books WHERE isbn = ?", (book.isbn,)
            ).fetchone()
            sources = list(book.sources)
            if existing:
                stored_sources = json.loads(existing[0])
                sources = list(dict.fromkeys([*stored_sources, *sources]))

            cursor = connection.execute(
                """INSERT INTO books (isbn,title,authors_json,publisher,published_date,description,page_count,language,cover_url,sources_json)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(isbn) DO UPDATE SET
                    title=CASE WHEN excluded.title <> '' THEN excluded.title ELSE books.title END,
                    authors_json=CASE WHEN excluded.authors_json <> '[]' THEN excluded.authors_json ELSE books.authors_json END,
                    publisher=CASE WHEN excluded.publisher <> '' THEN excluded.publisher ELSE books.publisher END,
                    published_date=CASE WHEN excluded.published_date <> '' THEN excluded.published_date ELSE books.published_date END,
                    description=CASE WHEN excluded.description <> '' THEN excluded.description ELSE books.description END,
                    page_count=COALESCE(excluded.page_count, books.page_count),
                    language=CASE WHEN excluded.language <> '' THEN excluded.language ELSE books.language END,
                    cover_url=CASE WHEN excluded.cover_url <> '' THEN excluded.cover_url ELSE books.cover_url END,
                    sources_json=excluded.sources_json
                RETURNING id""",
                (book.isbn, book.title, json.dumps(book.authors), book.publisher, book.published_date, book.description,
                 book.page_count, book.language, book.cover_url, json.dumps(sources)),
            )
            return int(cursor.fetchone()[0])

    def list_all(self) -> list[dict]:
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
        return [{**dict(row), "authors": json.loads(row["authors_json"]), "sources": json.loads(row["sources_json"])} for row in rows]
