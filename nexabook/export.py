from __future__ import annotations

from pathlib import Path

import pandas as pd


PUBLIC_COLUMNS = ["isbn", "title", "authors", "publisher", "published_date", "page_count", "language", "sources"]


def _safe_cell(value):
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def export_books(rows: list[dict], directory: Path, file_type: str = "csv") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    records = [
        {
            key: _safe_cell(", ".join(row[key]) if isinstance(row.get(key), list) else row.get(key, ""))
            for key in PUBLIC_COLUMNS
        }
        for row in rows
    ]
    frame = pd.DataFrame(records, columns=PUBLIC_COLUMNS)
    target = directory / f"nexabook_export.{file_type}"
    if file_type == "xlsx":
        frame.to_excel(target, index=False)
    elif file_type == "csv":
        frame.to_csv(target, index=False)
    else:
        raise ValueError("Supported export types are csv and xlsx")
    return target
