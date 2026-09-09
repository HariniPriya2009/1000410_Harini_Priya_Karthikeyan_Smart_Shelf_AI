"""
Step 2: Data Collection & Preprocessing for StockSense Pro.

Expects raw data organized as:
    data/raw/<category_name>/*.jpg      (if you're building your own set)
or a COCO/RPC-style annotation file if using the Retail Product Checkout dataset
    (in that case, adapt `load_annotations()` to parse it into the same
    intermediate format this script uses: list of (image_path, [bboxes]))

Bbox format used internally: [class_id, x_center, y_center, width, height]
all normalized 0-1 (this IS YOLO format, so no extra conversion needed at the end).

Usage:
    python src/prepare_dataset.py --raw_dir data/raw --out_dir data --img_size 640
"""

import argparse
import random
import shutil
from pathlib import Path

import cv2
import numpy as np

random.seed(42)

TRAIN_RATIO, VAL_RATIO, TEST_RATIO = 0.70, 0.15, 0.15


def list_categories(raw_dir: Path):
    """Assumes data/raw/<category>/*.jpg structure with a per-image .txt
    YOLO-format label file alongside each image (same basename)."""
    return sorted([d.name for d in raw_dir.iterdir() if d.is_dir()])


def gather_image_label_pairs(category_dir: Path):
    exts = {".jpg", ".jpeg", ".png"}
    pairs = []
    for img_path in category_dir.iterdir():
        if img_path.suffix.lower() in exts:
            label_path = img_path.with_suffix(".txt")
            if label_path.exists():
                pairs.append((img_path, label_path))
    return pairs


def resize_image_and_labels(img_path: Path, label_path: Path, out_img_path: Path,
                             out_label_path: Path, img_size: int):
    img = cv2.imread(str(img_path))
    if img is None:
        return False
    resized = cv2.resize(img, (img_size, img_size))
    cv2.imwrite(str(out_img_path), resized)
    # YOLO labels are already normalized (0-1), so they transfer as-is
    # regardless of resize — just copy the label file.
    shutil.copy(label_path, out_label_path)
    return True


def augment_image(img: np.ndarray, mode: str) -> np.ndarray:
    """Simple augmentations. NOTE: rotation/flip change box coordinates —
    if you augment, you MUST transform the label file's coordinates too.
    This function is provided for brightness-only augmentation, which is
    safe (does not move bounding boxes). For flip/rotation augmentation,
    use a library like `albumentations` with bbox-aware transforms instead
    of hand-rolling it, to avoid silently corrupting your labels.
    """
    if mode == "brightness_up":
        return cv2.convertScaleAbs(img, alpha=1.0, beta=30)
    if mode == "brightness_down":
        return cv2.convertScaleAbs(img, alpha=1.0, beta=-30)
    return img


def split_pairs(pairs, train_ratio=TRAIN_RATIO, val_ratio=VAL_RATIO):
    random.shuffle(pairs)
    n = len(pairs)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    return pairs[:n_train], pairs[n_train:n_train + n_val], pairs[n_train + n_val:]


def main(raw_dir: str, out_dir: str, img_size: int):
    raw_dir = Path(raw_dir)
    out_dir = Path(out_dir)
    categories = list_categories(raw_dir)

    if not categories:
        print(f"No category folders found in {raw_dir}. "
              f"Expected structure: {raw_dir}/<category_name>/image.jpg + image.txt")
        return

    print(f"Found {len(categories)} categories: {categories}")

    class_map = {name: idx for idx, name in enumerate(categories)}
    (out_dir / "classes.txt").write_text("\n".join(categories))

    split_counts = {"train": 0, "val": 0, "test": 0}

    for category in categories:
        pairs = gather_image_label_pairs(raw_dir / category)
        if len(pairs) < 20:
            print(f"  WARNING: '{category}' has only {len(pairs)} labeled images "
                  f"(recommend 40-60+ before augmentation).")

        train_pairs, val_pairs, test_pairs = split_pairs(pairs)

        for split_name, split_pairs_list in [("train", train_pairs),
                                              ("val", val_pairs),
                                              ("test", test_pairs)]:
            img_out_dir = out_dir / split_name / "images"
            lbl_out_dir = out_dir / split_name / "labels"
            img_out_dir.mkdir(parents=True, exist_ok=True)
            lbl_out_dir.mkdir(parents=True, exist_ok=True)

            for img_path, label_path in split_pairs_list:
                out_img = img_out_dir / f"{category}_{img_path.name}"
                out_lbl = lbl_out_dir / f"{category}_{label_path.name}"
                if resize_image_and_labels(img_path, label_path, out_img, out_lbl, img_size):
                    split_counts[split_name] += 1

    print("\nSplit summary:")
    for split_name, count in split_counts.items():
        print(f"  {split_name}: {count} images")

    print(f"\nDone. Update data.yaml 'names' field with: {categories}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare shelf dataset for YOLO training")
    parser.add_argument("--raw_dir", default="data/raw")
    parser.add_argument("--out_dir", default="data")
    parser.add_argument("--img_size", type=int, default=640)
    args = parser.parse_args()
    main(args.raw_dir, args.out_dir, args.img_size)
