"""Guidance lines and their sources, from data/season_rules.json.

A line is "cited" (a named publisher and a web address) or "general"
(worded as general advice, PLAN.md P0-12). tests/test_season_rules.py holds
both kinds to that."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

RULES_FILE = Path(__file__).parent / "data" / "season_rules.json"


@lru_cache(maxsize=1)
def rules() -> dict:
    return json.loads(RULES_FILE.read_text())


def line(key: str) -> dict:
    return rules()["lines"][key]


def source(key: str) -> dict:
    return dict(rules()["sources"][key])


def line_source(key: str) -> dict:
    return source(line(key)["source"])


def default(name: str):
    return rules()["engineering_defaults"][name]
