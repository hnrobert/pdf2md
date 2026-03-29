"""Image extraction from PDF pages."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageExtractor:
    """Extract images from PDF pages into an assets directory."""

    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self._image_count = 0

    def extract_images(self, page, page_number: int) -> list[tuple[str, tuple[float, float, float, float]]]:
        """Extract images from a pdfplumber page.

        Returns list of (markdown_path, bounding_box) tuples.
        """
        results: list[tuple[str, tuple[float, float, float, float]]] = []

        try:
            images = page.images
        except Exception as exc:
            logger.warning("Failed to get images from page %d: %s", page_number, exc)
            return results

        for img_info in images:
            self._image_count += 1
            bbox = (img_info["x0"], img_info["top"], img_info["x1"], img_info["bottom"])

            # Try to extract the actual image data
            image_path = self._save_image_from_page(page, page_number, self._image_count, img_info)
            if image_path:
                results.append((image_path, bbox))

        return results

    def _save_image_from_page(
        self, page, page_number: int, image_index: int, img_info: dict
    ) -> str:
        """Try to extract and save an image, return relative markdown path or empty string."""
        try:
            # Access underlying pdfminer page for image XObjects
            pdfminer_page = page.page
            resources = pdfminer_page.resources

            if resources is None:
                return ""

            xobjects = resources.get("XObject", {})
            if not xobjects:
                return ""

            # Try to find the image by iterating XObjects
            for obj_name in xobjects:
                try:
                    xobj = xobjects[obj_name].resolve()
                    if xobj.get("Subtype") != "Image":
                        continue

                    width = int(xobj.get("Width", 0))
                    height = int(xobj.get("Height", 0))
                    if width <= 0 or height <= 0:
                        continue

                    # Determine format
                    color_space = xobj.get("ColorSpace", "")
                    filters = xobj.get("Filter", "")

                    if isinstance(filters, list):
                        has_jpeg = any("DCT" in str(f) for f in filters)
                        ext = "jpg" if has_jpeg else "png"
                    elif "DCT" in str(filters):
                        ext = "jpg"
                    else:
                        ext = "png"

                    filename = f"page{page_number:03d}_img{image_index:02d}.{ext}"
                    os.makedirs(self.assets_dir, exist_ok=True)
                    output_path = Path(self.assets_dir) / filename

                    # Extract raw stream data
                    stream = xobj.get_data()
                    output_path.write_bytes(stream)

                    return f"assets/{filename}"
                except Exception:
                    continue

            # Fallback: just record image position without data
            logger.debug(
                "Could not extract image data for image %d on page %d",
                image_index,
                page_number,
            )
            return ""

        except Exception as exc:
            logger.warning(
                "Failed to extract image %d on page %d: %s",
                image_index,
                page_number,
                exc,
            )
            return ""
