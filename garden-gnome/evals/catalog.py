"""Catalog names for eval grading, straight from species_catalog.json.

No DB, no SQLModel — the fuzzy matcher only needs names. IDs are the
1-based catalog position, matching what a fresh seed produces.
"""
from __future__ import annotations

import json
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "species_catalog.json"


def load_names(path: Path = CATALOG_PATH) -> list[dict]:
    """[{'id', 'common_name', 'scientific_name'}, ...] for the whole catalog."""
    entries = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            "id": i + 1,
            "common_name": e["species"]["common_name"],
            "scientific_name": e["species"]["scientific_name"],
        }
        for i, e in enumerate(entries)
    ]


def common_names(path: Path = CATALOG_PATH) -> set[str]:
    return {row["common_name"] for row in load_names(path)}
