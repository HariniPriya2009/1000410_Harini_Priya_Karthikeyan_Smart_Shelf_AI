"""
Step 4: Stock Insight & Alert System.

Converts raw YOLO detections into business-usable output:
  - per-category counts
  - stock status per category (Out of Stock / Low Stock / In Stock)
  - restock alerts
  - (optional) restocking priority ranking

Challenge handling notes:
  - Overlapping products: rely on YOLO's built-in NMS (non-max suppression)
    to avoid double-counting the same physical item as two detections.
  - Similar packaging: this is a training-data problem, not something fixable
    at the insight layer — if two categories get confused, they need more
    (and more distinct) labeled examples.
"""

from collections import Counter
from dataclasses import dataclass, field


OUT_OF_STOCK_MAX = 0
LOW_STOCK_MAX = 3  # 1-3 = Low Stock, 4+ = In Stock


@dataclass
class CategoryStock:
    name: str
    count: int
    status: str
    alert: str


@dataclass
class StockReport:
    categories: list = field(default_factory=list)
    total_items: int = 0

    def to_dict(self):
        return {
            "total_items": self.total_items,
            "categories": [
                {"name": c.name, "count": c.count, "status": c.status, "alert": c.alert}
                for c in self.categories
            ],
        }


def classify_stock(count: int) -> str:
    if count <= OUT_OF_STOCK_MAX:
        return "Out of Stock"
    if count <= LOW_STOCK_MAX:
        return "Low Stock"
    return "In Stock"


def alert_for_status(status: str, category: str) -> str:
    if status == "Out of Stock":
        return f"Restock needed: {category} is out of stock."
    if status == "Low Stock":
        return f"Restock soon: {category} is running low."
    return f"Stock sufficient: {category}."


def build_stock_report(detections: list, class_names: list) -> StockReport:
    """
    Args:
        detections: list of class_id ints, one per detected bounding box
                    (i.e. what you get after running YOLO inference and
                    extracting `results.boxes.cls`)
        class_names: list mapping class_id -> category name (from data.yaml)

    Returns:
        StockReport with per-category counts, status, and alerts.
    """
    counts = Counter(detections)
    categories = []

    # Include every known category, even ones with zero detections,
    # so "Out of Stock" categories are surfaced rather than silently omitted.
    for class_id, name in enumerate(class_names):
        count = counts.get(class_id, 0)
        status = classify_stock(count)
        alert = alert_for_status(status, name)
        categories.append(CategoryStock(name=name, count=count, status=status, alert=alert))

    return StockReport(categories=categories, total_items=sum(counts.values()))


def restocking_priority(report: StockReport) -> list:
    """Optional advanced insight: rank categories by urgency
    (Out of Stock first, then Low Stock, sorted by count ascending)."""
    priority_order = {"Out of Stock": 0, "Low Stock": 1, "In Stock": 2}
    return sorted(
        report.categories,
        key=lambda c: (priority_order[c.status], c.count),
    )
