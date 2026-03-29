"""Core converter module for PDF to Markdown conversion."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

try:
    import pdfplumber  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    pdfplumber = None  # type: ignore[assignment]

from .image_extractor import ImageExtractor
from .layout_analyzer import LayoutAnalyzer
from .page_processor import PageProcessor
from .table_processor import TableProcessor
from .utils import clean_markdown_content

logger = logging.getLogger(__name__)


def _parse_page_range(page_spec: str, total_pages: int) -> list[int]:
    """Parse a page range string like '1-5,8,10-12' into 0-based page indices."""
    indices: list[int] = []
    for part in page_spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = int(start.strip())
            end = int(end.strip())
            for p in range(start, end + 1):
                if 1 <= p <= total_pages:
                    indices.append(p - 1)
        else:
            p = int(part)
            if 1 <= p <= total_pages:
                indices.append(p - 1)
    return sorted(set(indices))


class PdfToMarkdownConverter:
    """PDF to Markdown converter."""

    def __init__(self):
        self.output_folder: str = ""
        self.assets_dir: str = ""

    def convert_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        ignore_images: bool = False,
        pages: Optional[str] = None,
    ) -> str:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        if not input_path.lower().endswith(".pdf"):
            raise ValueError(f"Only .pdf is supported: {input_path}")

        if pdfplumber is None:
            raise RuntimeError(
                "Missing required dependency 'pdfplumber'. Please run: pip install pdfplumber"
            )

        self._setup_output_structure(input_path, output_path, ignore_images)

        layout_analyzer = LayoutAnalyzer()
        table_processor = TableProcessor()
        image_extractor = (
            ImageExtractor(self.assets_dir) if not ignore_images and self.assets_dir else None
        )
        page_processor = PageProcessor(
            layout_analyzer=layout_analyzer,
            table_processor=table_processor,
            image_extractor=image_extractor,
            ignore_images=ignore_images,
        )

        output_lines: list[str] = []

        with pdfplumber.open(input_path) as pdf:
            total_pages = len(pdf.pages)

            if total_pages == 0:
                logger.warning("PDF has no pages: %s", input_path)
                markdown_content = "\n"
                self._write_output(markdown_content, self._get_final_output_path(input_path, output_path))
                return markdown_content

            # Determine page indices
            if pages:
                page_indices = _parse_page_range(pages, total_pages)
                if not page_indices:
                    raise ValueError(f"No valid pages in range '{pages}' (total: {total_pages})")
            else:
                page_indices = list(range(total_pages))

            # Check if the PDF is scanned (no text on any page)
            has_text = False
            for idx in page_indices:
                if pdf.pages[idx].chars:
                    has_text = True
                    break
            if not has_text:
                logger.warning(
                    "PDF appears to have no text layer (possibly scanned). "
                    "OCR is not supported. Output may be empty."
                )

            for idx in page_indices:
                page = pdf.pages[idx]
                page_number = idx + 1
                logger.debug("Processing page %d/%d", page_number, total_pages)

                page_lines = page_processor.process_page(page, page_number)
                output_lines.extend(page_lines)

        markdown_content = clean_markdown_content(output_lines)
        final_output_path = self._get_final_output_path(input_path, output_path)
        self._write_output(markdown_content, final_output_path)
        self._cleanup_empty_assets_dir()

        logger.info("Conversion completed, output file: %s", final_output_path)
        return markdown_content

    def _setup_output_structure(
        self, input_path: str, output_path: Optional[str], ignore_images: bool
    ):
        input_stem = Path(input_path).stem

        if output_path:
            if os.path.isdir(output_path) or output_path.endswith("/"):
                self.output_folder = os.path.join(output_path, input_stem)
            else:
                self.output_folder = os.path.dirname(output_path)
                if not self.output_folder:
                    self.output_folder = input_stem
        else:
            self.output_folder = input_stem

        os.makedirs(self.output_folder, exist_ok=True)

        if ignore_images:
            self.assets_dir = ""
        else:
            self.assets_dir = os.path.join(self.output_folder, "assets")
            os.makedirs(self.assets_dir, exist_ok=True)

    def _get_final_output_path(self, input_path: str, output_path: Optional[str]) -> str:
        input_stem = Path(input_path).stem

        if output_path:
            if os.path.isdir(output_path) or output_path.endswith("/"):
                return os.path.join(self.output_folder, f"{input_stem}.md")
            return output_path

        return os.path.join(self.output_folder, f"{input_stem}.md")

    def _write_output(self, content: str, output_path: str):
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _cleanup_empty_assets_dir(self):
        if self.assets_dir and os.path.exists(self.assets_dir) and not os.listdir(self.assets_dir):
            os.rmdir(self.assets_dir)
