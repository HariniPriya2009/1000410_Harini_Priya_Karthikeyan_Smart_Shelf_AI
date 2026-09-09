# StockSense Pro
### AI-based Cognitive Retail Vision System for Automated Shelf Intelligence

Built for RetailSense AI Solutions Pvt. Ltd. — detects products on a shelf image,
counts them per category, and flags stock status (Out of Stock / Low Stock / In Stock).

## 1. Problem Definition

- **Input:** A shelf image
- **Output:** Product name, count per category, stock status, and an annotated image
  with bounding boxes
- **Approach:** Category-level object detection (YOLO), not per-SKU classification —
  more tractable with a small student dataset while still demonstrating real
  detection capability.

**Stock thresholds:**
| Count | Status |
|---|---|
| 0 | Out of Stock |
| 1–3 | Low Stock |
| 4+ | In Stock |

**Known real-world challenges:** overlapping products, inconsistent lighting,
visually similar packaging, cluttered shelves. See `src/stock_insights.py` docstring
for how each is handled.

## 2. Project Structure

```
StockSensePro/
├── data/
│   ├── raw/              # downloaded dataset goes here (not committed)
│   ├── train/images,labels
│   ├── val/images,labels
│   └── test/images,labels
├── src/
│   ├── prepare_dataset.py   # select classes, resize, split, YOLO-format labels
│   ├── train.py             # YOLO training + evaluation
│   └── stock_insights.py    # counting, thresholds, alert logic
├── app/
│   └── streamlit_app.py     # upload image -> detection -> dashboard
├── models/                  # trained weights (best.pt) go here
├── notebooks/                # exploratory analysis
├── data.yaml                 # YOLO dataset config
└── requirements.txt
```

## 3. Dataset

We use the **Retail Product Checkout (RPC) Dataset**, available on Kaggle:
https://www.kaggle.com/datasets/diyer22/retail-product-checkout-dataset

It ships with COCO-style JSON annotations (`train2019.json`, `val2019.json`,
`test2019.json`) — NOT YOLO `.txt` format — so it needs a conversion step.

```bash
# 1. Download & unzip (on your own machine, with Kaggle API configured):
kaggle datasets download -d diyer22/retail-product-checkout-dataset -p data/raw --unzip

# 2. See what categories exist (200 total — you only need 5-10):
python src/coco_to_yolo.py --list_categories --json data/raw/train2019.json

# 3. Convert your chosen categories for each split (same --categories string every time):
python src/coco_to_yolo.py --json data/raw/train2019.json --img_dir data/raw/train2019 \
    --out_split train --categories "name_1,name_2,name_3,name_4,name_5"

python src/coco_to_yolo.py --json data/raw/val2019.json --img_dir data/raw/val2019 \
    --out_split val --categories "name_1,name_2,name_3,name_4,name_5"

python src/coco_to_yolo.py --json data/raw/test2019.json --img_dir data/raw/test2019 \
    --out_split test --categories "name_1,name_2,name_3,name_4,name_5"
```

This populates `data/train`, `data/val`, `data/test` directly — you can skip
`prepare_dataset.py` for the RPC path since the converter already writes
YOLO-format labels and respects the dataset's own train/val/test split.
Update `data.yaml`'s `names` list to match `data/classes.txt` afterward.

**Category selection tip:** pick 5–10 visually distinct categories first (e.g.
different brands) before attempting near-duplicate SKUs (flavor variants) — it's
an easier first model and still fulfills the "5-10 categories" requirement.

## 4. Setup

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## 5. Pipeline

1. `python src/prepare_dataset.py` — organizes raw images/annotations into
   train/val/test with YOLO-format labels, applies augmentation
2. `python src/train.py` — trains YOLOv8 on the prepared dataset
3. `streamlit run app/streamlit_app.py` — launch the dashboard locally

## 6. Deployment

1. Push this repo to GitHub (include `models/best.pt` via Git LFS if >100MB, or
   host weights externally and download at app startup)
2. Go to https://streamlit.io/cloud, sign in with GitHub, select this repo,
   set main file to `app/streamlit_app.py`
3. Add `requirements.txt` — Streamlit Cloud installs it automatically
4. Public link goes here once deployed: `<ADD LINK>`

## 7. Results

_(Fill in after training: precision, recall, confusion matrix, example detections)_

## 8. Team / Submission Info

Repository: `IADAI201(Student_id)-studentname`
