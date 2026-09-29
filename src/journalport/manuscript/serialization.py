"""Deterministic canonical JSON serialization and logical hashing."""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from dataclasses import asdict, is_dataclass
from typing import Any

from .model import CanonicalManuscript


def canonicalize(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if isinstance(value, dict):
        return {
            unicodedata.normalize("NFC", str(k)): canonicalize(v) for k, v in sorted(value.items())
        }
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON forbids NaN and Infinity")
        return value
    if value is None or isinstance(value, (bool, int)):
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def serialize_canonical(value: CanonicalManuscript | dict[str, Any]) -> bytes:
    return json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def deserialize_canonical(payload: bytes | str) -> CanonicalManuscript:
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    return CanonicalManuscript.from_dict(json.loads(payload))


def logical_hash(value: CanonicalManuscript | dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(serialize_canonical(value)).hexdigest()
