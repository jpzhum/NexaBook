from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import BookMetadata


SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT NOT NULL,
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

    def add(self, book: BookMetadata) -> int:
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(
                "INSERT INTO books (isbn,title,authors_json,publisher,published_date,description,page_count,language,cover_url,sources_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (book.isbn, book.title, json.dumps(book.authors), book.publisher, book.published_date, book.description,
                 book.page_count, book.language, book.cover_url, json.dumps(book.sources)),
            )
            return int(cursor.lastrowid)

    def list_all(self) -> list[dict]:
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
        return [{**dict(row), "authors": json.loads(row["authors_json"]), "sources": json.loads(row["sources_json"])} for row in rows]
