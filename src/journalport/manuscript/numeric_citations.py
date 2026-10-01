"""Bounded plain numeric marker parsing shared by canonical parsing and linkage QA."""

from __future__ import annotations

import re


def expand_numeric_marker(marker: str) -> tuple[int, ...]:
    values: list[int] = []
    for item in marker.strip("[] ").split(","):
        parts = re.split(r"[–-]", item.strip())
        if len(parts) == 1 and parts[0].isdigit():
            values.append(int(parts[0]))
        elif len(parts) == 2 and all(part.isdigit() for part in parts):
            first, last = map(int, parts)
            if first > last or last - first > 1000:
                raise ValueError("invalid or excessive citation range")
            values.extend(range(first, last + 1))
        else:
            raise ValueError("unsupported numeric citation marker")
    if any(value < 1 for value in values) or len(values) != len(set(values)):
        raise ValueError("invalid or duplicate numeric citation")
    return tuple(values)
