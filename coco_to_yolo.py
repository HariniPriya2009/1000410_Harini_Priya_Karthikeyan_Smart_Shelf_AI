"""
Converts RPC (Retail Product Checkout) COCO-style annotations into YOLO format,
keeping only a chosen subset of categories.

RPC dataset structure (after Kaggle download + unzip) is typically:
    retail_product_checkout/
        train2019.json                (or instances_train2019.json)
        val2019.json
        test2019.json
        train2019/*.jpg
        val2019/*.jpg
        test2019/*.jpg

Each JSON follows COCO format:
    {
      "images": [{"id": 1, "file_name": "...", "width": ..., "height": ...}, ...],
      "annotations": [{"image_id": 1, "category_id": 5, "bbox": [x,y,w,h]}, ...],
      "categories": [{"id": 5, "name": "puffed_food_..."}, ...]
    }

STEP 1 — inspect the dataset first to pick your 5-10 categories:
    python src/coco_to_yolo.py --list_categories --json path/to/train2019.json

STEP 2 — convert, keeping only the categories you chose:
    python src/coco_to_yolo.py \\
        --json path/to/train2019.json \\
        --img_dir path/to/train2019 \\
        --out_split train \\
        --categories "category_name_1,category_name_2,category_name_3"

Repeat for val2019.json -> --out_split val, and test2019.json -> --out_split test.
Use the SAME --categories string every time so class IDs stay consistent across splits.
"""

import argparse
import json
import shutil
from pathlib import Path


def load_coco(json_path: str):
    with open(json_path, "r") as f:
        return json.load(f)


def list_categories(coco: dict):
    print(f"{'id':>5}  name")
    for cat in coco["categories"]:
        print(f"{cat['id']:>5}  {cat['name']}")
    print(f"\nTotal categories: {len(coco['categories'])}")


def convert(json_path: str, img_dir: str, out_dir: str, out_split: str, category_names: list):
    coco = load_coco(json_path)

    # Map chosen category names -> COCO category_id -> new sequential YOLO class_id
    name_to_coco_id = {c["name"]: c["id"] for c in coco["categories"]}
    missing = [n for n in category_names if n not in name_to_coco_id]
    if missing:
        raise ValueError(f"Category names not found in this JSON: {missing}. "
                          f"Run with --list_categories to see valid names.")

    coco_id_to_yolo_id = {name_to_coco_id[name]: idx for idx, name in enumerate(category_names)}

    # image_id -> image info
    images_by_id = {img["id"]: img for img in coco["images"]}

    # image_id -> list of YOLO-format annotation lines
    anns_by_image = {}
    for ann in coco["annotations"]:
        cat_id = ann["category_id"]
        if cat_id not in coco_id_to_yolo_id:
            continue  # skip categories we didn't select
        img_info = images_by_id.get(ann["image_id"])
        if img_info is None:
            continue

        x, y, w, h = ann["bbox"]
        img_w, img_h = img_info["width"], img_info["height"]

        # COCO bbox (top-left x,y,w,h) -> YOLO (normalized center x,y,w,h)
        x_center = (x + w / 2) / img_w
        y_center = (y + h / 2) / img_h
        norm_w = w / img_w
        norm_h = h / img_h

        yolo_class = coco_id_to_yolo_id[cat_id]
        line = f"{yolo_class} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}"
        anns_by_image.setdefault(ann["image_id"], []).append(line)

    if not anns_by_image:
        print("WARNING: no annotations matched the selected categories in this JSON. "
              "Double-check --categories spelling against --list_categories output.")
        return

    out_img_dir = Path(out_dir) / out_split / "images"
    out_lbl_dir = Path(out_dir) / out_split / "labels"
    out_img_dir.mkdir(parents=True, exist_ok=True)
    out_lbl_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for image_id, lines in anns_by_image.items():
        img_info = images_by_id[image_id]
        src_img = Path(img_dir) / img_info["file_name"]
        if not src_img.exists():
            continue

        dst_img = out_img_dir / src_img.name
        dst_lbl = out_lbl_dir / (src_img.stem + ".txt")

        shutil.copy(src_img, dst_img)
        dst_lbl.write_text("\n".join(lines))
        written += 1

    # Save/refresh classes.txt at the dataset root so it's consistent across splits
    Path(out_dir, "classes.txt").write_text("\n".join(category_names))

    print(f"[{out_split}] Wrote {written} images with labels to {out_img_dir}")
    print(f"Classes (order matters, matches data.yaml): {category_names}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert RPC COCO annotations to YOLO format")
    parser.add_argument("--json", help="Path to a COCO-format annotation JSON (e.g. train2019.json)")
    parser.add_argument("--img_dir", help="Directory containing the images referenced in the JSON")
    parser.add_argument("--out_dir", default="data")
    parser.add_argument("--out_split", choices=["train", "val", "test"])
    parser.add_argument("--categories", help="Comma-separated category names to keep, "
                                              "e.g. 'puffed_food_1,drink_1,candy_1'")
    parser.add_argument("--list_categories", action="store_true",
                         help="Print all category id/name pairs in the JSON and exit")
    args = parser.parse_args()

    coco_data = load_coco(args.json)

    if args.list_categories:
        list_categories(coco_data)
    else:
        if not (args.img_dir and args.out_split and args.categories):
            parser.error("--img_dir, --out_split, and --categories are required for conversion")
        cat_list = [c.strip() for c in args.categories.split(",")]
        convert(args.json, args.img_dir, args.out_dir, args.out_split, cat_list)
