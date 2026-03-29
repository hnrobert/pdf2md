"""Page-level processing: convert analyzed PDF page layout to Markdown lines."""

from __future__ import annotations

import logging
from typing import Optional

from .image_extractor import ImageExtractor
from .layout_analyzer import LayoutAnalyzer
from .table_processor import TableProcessor
from .text_block import TextBlock
from .utils import escape_markdown

logger = logging.getLogger(__name__)


class PageProcessor:
    """Convert one PDF page into Markdown lines."""

    def __init__(
        self,
        layout_analyzer: LayoutAnalyzer,
        table_processor: TableProcessor,
        image_extractor: Optional[ImageExtractor],
        ignore_images: bool = False,
    ):
        self.layout_analyzer = layout_analyzer
        self.table_processor = table_processor
        self.image_extractor = image_extractor
        self.ignore_images = ignore_images

    def process_page(self, page, page_number: int) -> list[str]:
        """Process a pdfplumber page and return Markdown lines."""
        # Analyze layout to get ordered text blocks
        blocks = self.layout_analyzer.analyze(page, page_number)

        # Extract tables and their bounding boxes
        tables_with_bbox = self.table_processor.extract_tables(page)
        table_bboxes = [bbox for _, bbox in tables_with_bbox]
        table_lines_by_y: dict[float, list[str]] = {}

        for table_data, bbox in tables_with_bbox:
            formatted = self.table_processor.format_table(table_data)
            if formatted:
                # Key by y-center of table for interleaving with text
                y_center = (bbox[1] + bbox[3]) / 2
                table_lines_by_y[y_center] = formatted

        # Extract images (if not ignored)
        images_with_bbox: list[tuple[str, tuple[float, float, float, float]]] = []
        if not self.ignore_images and self.image_extractor:
            images_with_bbox = self.image_extractor.extract_images(page, page_number)

        if not blocks and not tables_with_bbox and not images_with_bbox:
            return ["<!-- empty page -->"]

        # Filter out blocks that overlap with tables
        text_blocks = [
            b for b in blocks
            if not b.is_header and not b.is_footer
            and not any(b.overlaps_bbox(tb, threshold=0.6) for tb in table_bboxes)
        ]

        # Infer heading levels
        heading_levels = LayoutAnalyzer.infer_heading_levels(blocks)

        # Build output by interleaving text blocks, tables, and images
        lines: list[str] = []

        # Collect all elements with their y-positions for proper interleaving
        elements: list[tuple[float, str, list[str]]] = []  # (y1, type, content_lines)

        for idx, block in enumerate(blocks):
            if block.is_header or block.is_footer:
                continue
            if any(block.overlaps_bbox(tb, threshold=0.6) for tb in table_bboxes):
                continue

            block_lines = self._block_to_markdown(block, idx, heading_levels)
            if block_lines:
                elements.append((block.y1, "text", block_lines))

        for y_center, tbl_lines in table_lines_by_y.items():
            elements.append((y_center, "table", tbl_lines))

        for img_path, bbox in images_with_bbox:
            elements.append((bbox[3], "image", [f"![]({img_path})", ""]))

        # Sort by y-position (top to bottom = descending y1 in PDF coords)
        elements.sort(key=lambda e: -e[0])

        for _, _, content_lines in elements:
            lines.extend(content_lines)

        return lines if lines else ["<!-- empty page -->"]

    def _block_to_markdown(
        self,
        block: TextBlock,
        block_idx: int,
        heading_levels: dict[int, int],
    ) -> list[str]:
        """Convert a single TextBlock to Markdown lines."""
        text = block.text.strip()
        if not text:
            return []

        # Check if this is a heading
        level = heading_levels.get(block_idx, 0)
        if level > 0:
            prefix = "#" * level
            return [f"{prefix} {escape_markdown(text)}", ""]

        # Bold text
        if block.bold:
            return [f"**{escape_markdown(text)}**", ""]

        # Regular paragraph
        return [escape_markdown(text), ""]
