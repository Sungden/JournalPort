"""Read-only figure dimensions/DPI diagnostics; never re-encode scientific images."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Any

from journalport.transform.hashing import file_hash


def figure_technical_metadata(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    value: dict[str, Any] = {
        "sha256": file_hash(path),
        "bytes": len(payload),
        "format": "UNKNOWN",
        "width": None,
        "height": None,
        "dpi": None,
        "color_mode": "UNKNOWN",
    }
    if payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) >= 33:
        value["format"] = "PNG"
        value["width"], value["height"] = struct.unpack(">II", payload[16:24])
        value["color_mode"] = {
            0: "GRAYSCALE",
            2: "RGB",
            3: "PALETTE",
            4: "GRAYSCALE_ALPHA",
            6: "RGBA",
        }.get(payload[25], "UNKNOWN")
        offset = 8
        while offset + 12 <= len(payload):
            length = int.from_bytes(payload[offset : offset + 4], "big")
            if offset + length + 12 > len(payload):
                raise ValueError("truncated PNG chunk")
            if payload[offset + 4 : offset + 8] == b"pHYs" and length == 9:
                x, y, unit = struct.unpack(">IIB", payload[offset + 8 : offset + 17])
                if unit == 1:
                    value["dpi"] = [x * 0.0254, y * 0.0254]
            offset += length + 12
    elif payload.startswith(b"\xff\xd8"):
        value["format"] = "JPEG"
        offset = 2
        while offset + 4 <= len(payload) and payload[offset] == 255:
            marker = payload[offset + 1]
            if marker in {0xD9, 0xDA}:
                break
            length = int.from_bytes(payload[offset + 2 : offset + 4], "big")
            data = payload[offset + 4 : offset + 2 + length]
            if length < 2 or offset + 2 + length > len(payload):
                raise ValueError("truncated JPEG segment")
            if marker == 0xE0 and data.startswith(b"JFIF\0") and len(data) >= 12:
                unit = data[7]
                x, y = struct.unpack(">HH", data[8:12])
                if unit in {1, 2}:
                    factor = 1 if unit == 1 else 2.54
                    value["dpi"] = [x * factor, y * factor]
            if marker in {0xC0, 0xC1, 0xC2} and len(data) >= 6:
                value["height"], value["width"] = struct.unpack(">HH", data[1:5])
                value["color_mode"] = (
                    "RGB" if data[5] == 3 else "GRAYSCALE" if data[5] == 1 else "UNKNOWN"
                )
            offset += 2 + length
    value["technical_validation_status"] = "MANUAL_REVIEW_REQUIRED"
    value["manual_reason"] = "author_image_type_and_applicable_production_requirements_required"
    return value
