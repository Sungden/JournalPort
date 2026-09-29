"""Pure operator registry; every supported operator is deterministic."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

Operator = Callable[[Any, Any], bool]


def _contains(current: Any, expected: Any) -> bool:
    return expected in current


def _matches(current: Any, expected: Any) -> bool:
    return re.search(str(expected), str(current), flags=re.UNICODE) is not None


OPERATORS: dict[str, Operator] = {
    "EQ": lambda a, b: a == b,
    "NE": lambda a, b: a != b,
    "LT": lambda a, b: a < b,
    "LTE": lambda a, b: a <= b,
    "GT": lambda a, b: a > b,
    "GTE": lambda a, b: a >= b,
    "EXISTS": lambda a, _b: a is not None and a != "" and a != [],
    "NOT_EXISTS": lambda a, _b: a is None or a == "" or a == [],
    "IN": lambda a, b: a in b,
    "NOT_IN": lambda a, b: a not in b,
    "COUNT_EQ": lambda a, b: len(a) == b,
    "COUNT_LTE": lambda a, b: len(a) <= b,
    "COUNT_GTE": lambda a, b: len(a) >= b,
    "MATCH_REGEX": _matches,
    "NOT_MATCH_REGEX": lambda a, b: not _matches(a, b),
    "CONTAINS": _contains,
    "NOT_CONTAINS": lambda a, b: not _contains(a, b),
}


def evaluate_operator(operator: str, current: Any, expected: Any) -> bool:
    return OPERATORS[operator](current, expected)
