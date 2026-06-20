"""Small shared helpers: dot-path access for nested records, JSON repair."""
from __future__ import annotations

import re
from typing import Any


def dget(obj: Any, path: str, default=None):
    """Read a nested value by dot path, e.g. "founding.page".

    List indices are supported numerically ("board.0.name"). Returns *default*
    if any segment is missing.
    """
    cur = obj
    for seg in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(seg)
        elif isinstance(cur, list) and seg.isdigit():
            idx = int(seg)
            cur = cur[idx] if idx < len(cur) else None
        else:
            return default
        if cur is None:
            return default
    return cur


def strip_json_fence(content: str) -> str:
    content = re.sub(r"^```(?:json)?\s*\n?", "", content.strip())
    content = re.sub(r"\n?```\s*$", "", content)
    return content


def extract_first_json_object(content: str) -> str | None:
    """Find the first balanced {...} object in a string (tolerant of leading
    LLM chatter). Returns the raw substring or None."""
    m = re.search(r"\{", content)
    if not m:
        return None
    start = m.start()
    depth = 0
    for i in range(start, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                return content[start : i + 1]
    return None


def remove_trailing_commas(s: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", s)
