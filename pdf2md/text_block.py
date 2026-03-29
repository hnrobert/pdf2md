"""TextBlock data structure for representing spatial text units on a PDF page."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TextBlock:
    """A coherent unit of text extracted from a PDF page with spatial metadata."""

    text: str = ""
    x0: float = 0.0
    y0: float = 0.0
    x1: float = 0.0
    y1: float = 0.0
    font_name: str = ""
    font_size: float = 0.0
    bold: bool = False
    page_number: int = 0
    is_header: bool = False
    is_footer: bool = False

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def center_y(self) -> float:
        return (self.y0 + self.y1) / 2

    def horizontal_overlap_ratio(self, other: TextBlock) -> float:
        """Return the ratio of horizontal overlap to the narrower block's width."""
        overlap = max(0.0, min(self.x1, other.x1) - max(self.x0, other.x0))
        min_width = min(self.width, other.width)
        if min_width <= 0:
            return 0.0
        return overlap / min_width

    def overlaps_bbox(self, bbox: tuple[float, float, float, float], threshold: float = 0.5) -> bool:
        """Check if this block overlaps significantly with a bounding box."""
        bx0, by0, bx1, by1 = bbox
        overlap_x = max(0.0, min(self.x1, bx1) - max(self.x0, bx0))
        overlap_y = max(0.0, min(self.y1, by1) - max(self.y0, by0))
        if self.width <= 0 or self.height <= 0:
            return False
        overlap_area = overlap_x * overlap_y
        self_area = self.width * self.height
        return (overlap_area / self_area) > threshold

    def is_spanning(self, page_width: float, ratio: float = 0.8) -> bool:
        """Check if this block spans most of the page width."""
        if page_width <= 0:
            return False
        return self.width > page_width * ratio
