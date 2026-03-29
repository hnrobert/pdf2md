"""Table extraction from PDF pages to Markdown format."""

from __future__ import annotations

import logging
from typing import Optional

from .utils import escape_markdown

logger = logging.getLogger(__name__)

TABLE_SETTINGS = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 5,
    "join_tolerance": 5,
    "edge_min_length": 10,
    "min_words_vertical": 2,
    "min_words_horizontal": 2,
}


class TableProcessor:
    """Extract tables from PDF pages and convert to Markdown."""

    def extract_tables(self, page) -> list[tuple[list[list[str]], tuple[float, float, float, float]]]:
        """Extract tables from a pdfplumber page.

        Returns list of (table_data, bounding_box) tuples.
        table_data is a list of rows, each row is a list of cell strings.
        bounding_box is (x0, y0, x1, y1).
        """
        try:
            tables = page.find_tables(table_settings=TABLE_SETTINGS)
        except Exception as exc:
            logger.warning("Failed to find tables on page: %s", exc)
            return []

        results = []
        for table in tables:
            try:
                table_data = table.extract()
                if not table_data or all(not any(row) for row in table_data):
                    continue
                bbox = (table.bbox[0], table.bbox[1], table.bbox[2], table.bbox[3])
                normalized = self._normalize_table(table_data)
                results.append((normalized, bbox))
            except Exception as exc:
                logger.warning("Failed to extract table: %s", exc)
                continue

        return results

    def format_table(self, table_data: list[list[str]]) -> list[str]:
        """Convert table data to Markdown pipe table lines."""
        if not table_data:
            return []

        rows = table_data
        header = rows[0]
        col_count = len(header)
        if col_count == 0:
            return []

        divider = ["---"] * col_count
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(divider) + " |",
        ]

        for row in rows[1:]:
            # Pad or truncate to match header
            if len(row) < col_count:
                row = row + [""] * (col_count - len(row))
            elif len(row) > col_count:
                row = row[:col_count]
            lines.append("| " + " | ".join(row) + " |")

        return lines

    def _normalize_table(self, table_data: list[list[Optional[str]]]) -> list[list[str]]:
        """Normalize table cells: replace None with empty string, strip whitespace."""
        normalized = []
        for row in table_data:
            normalized_row = []
            for cell in row:
                if cell is None:
                    normalized_row.append("")
                else:
                    text = " ".join(str(cell).split())
                    normalized_row.append(escape_markdown(text))
            normalized.append(normalized_row)
        return normalized
