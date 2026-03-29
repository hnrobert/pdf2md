"""Utility helpers for markdown generation."""

from __future__ import annotations

import re
from typing import Iterable


def escape_markdown(text: str) -> str:
    """Escape markdown control characters in plain text content."""
    if not text:
        return ""

    escaped = text.replace("\\", "\\\\")
    for ch in ["`", "*", "_", "{", "}", "[", "]", "<", ">", "|"]:
        escaped = escaped.replace(ch, f"\\{ch}")
    return escaped


def clean_markdown_content(lines: Iterable[str]) -> str:
    """Join markdown lines and collapse repeated blank lines."""
    text = "\n".join(lines).rstrip() + "\n"
    return re.sub(r"\n{3,}", "\n\n", text)
