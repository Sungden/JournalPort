"""Static compliance report renderers."""

from .html_report import render_html
from .json_report import render_json

__all__ = ["render_html", "render_json"]
