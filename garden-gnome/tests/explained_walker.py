"""A helper every package calls on its responses (PLAN.md D25).

    from tests.explained_walker import assert_explained
    assert_explained(response.json())

It walks any JSON value and fails on an Explained-like object (a mapping
with a "reason" or a "sources" key: Explained, SiteValue, SeasonTask, and
an event's `explained`) whose reason is empty, whose sources are empty, or
one of whose sources has no name. `problems()` returns the list instead of
failing, for tests that want to say more.
"""
from __future__ import annotations

from typing import Any


def problems(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        if "reason" in value or "sources" in value:
            reason = value.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                found.append(f"{path}: empty reason")
            sources = value.get("sources")
            if not isinstance(sources, list) or not sources:
                found.append(f"{path}: no sources")
            else:
                for i, s in enumerate(sources):
                    if not isinstance(s, dict) or not str(s.get("name") or "").strip():
                        found.append(f"{path}.sources[{i}]: a source with no name")
        for k, v in value.items():
            found.extend(problems(v, f"{path}.{k}"))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            found.extend(problems(v, f"{path}[{i}]"))
    return found


def assert_explained(value: Any) -> None:
    """Fail, naming every place, if any reason or source is missing."""
    found = problems(value)
    assert not found, "values without a reason or a source:\n  " + "\n  ".join(found)
