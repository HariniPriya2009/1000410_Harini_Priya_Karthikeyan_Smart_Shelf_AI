"""
Step 5: Dashboard Development.

Streamlit app: upload a shelf image -> run YOLO detection -> show annotated
image + stock insight dashboard with color-coded status.

Run locally:
    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image
from ultralytics import YOLO

THIS_DIR = Path(__file__).resolve().parent

# Support both layouts: streamlit_app.py at repo root, or inside app/.
# Whichever directory actually contains src/ is the repo root.
if (THIS_DIR / "src").exists():
    REPO_ROOT = THIS_DIR
else:
    REPO_ROOT = THIS_DIR.parent

sys.path.append(str(REPO_ROOT))
from src.stock_insights import build_stock_report, restocking_priority  # noqa: E402

MODEL_PATH = REPO_ROOT / "models" / "best.pt"

STATUS_COLORS = {
    "Out of Stock": "#e74c3c",  # red
    "Low Stock": "#f1c40f",     # yellow
    "In Stock": "#2ecc71",      # green
}


@st.cache_resource
def load_model(path: str):
    return YOLO(path)


def run_detection(model, image: np.ndarray, conf_threshold: float):
    results = model.predict(image, conf=conf_threshold, verbose=False)[0]
    annotated = results.plot()  # BGR image with boxes drawn
    class_ids = results.boxes.cls.tolist() if results.boxes is not None else []
    class_names = [model.names[i] for i in sorted(model.names)]
    return annotated, [int(c) for c in class_ids], class_names


def main():
    st.set_page_config(page_title="StockSense Pro", layout="wide")
    st.title("StockSense Pro — Shelf Intelligence Dashboard")
    st.caption("Upload a shelf image to detect products, count stock, and get restock alerts.")

    with st.sidebar:
        st.header("Settings")
        conf_threshold = st.slider("Detection confidence", 0.1, 0.9, 0.4, 0.05)
        st.markdown("---")
        st.markdown(
            "**Stock thresholds**\n"
            "- 0 → Out of Stock\n"
            "- 1–3 → Low Stock\n"
            "- 4+ → In Stock"
        )

    if not MODEL_PATH.exists():
        st.error(
            f"No trained model found at `{MODEL_PATH}`. "
            f"Train a model with `src/train.py` and copy the best weights there."
        )
        return

    model = load_model(str(MODEL_PATH))

    uploaded_file = st.file_uploader("Upload a shelf image", type=["jpg", "jpeg", "png"])

    if uploaded_file is None:
        st.info("Upload an image to get started.")
        return

    image = Image.open(uploaded_file).convert("RGB")
    image_np = np.array(image)

    with st.spinner("Analyzing shelf..."):
        annotated_bgr, class_ids, class_names = run_detection(model, image_np, conf_threshold)
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        report = build_stock_report(class_ids, class_names)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Detected Shelf")
        st.image(annotated_rgb, use_container_width=True)

    with col2:
        st.subheader("Stock Summary")
        m1, m2 = st.columns(2)
        m1.metric("Total items detected", report.total_items)
        m2.metric("Categories tracked", len(report.categories))

        st.markdown("---")
        for cat in report.categories:
            color = STATUS_COLORS[cat.status]
            st.markdown(
                f"<div style='padding:8px;border-radius:6px;background-color:{color}22;"
                f"border-left:4px solid {color};margin-bottom:6px;'>"
                f"<b>{cat.name}</b> — {cat.count} units "
                f"<span style='color:{color};font-weight:600;'>({cat.status})</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.subheader("Restock Priority")
        priority = [c for c in restocking_priority(report) if c.status != "In Stock"]
        if priority:
            for cat in priority:
                st.warning(cat.alert)
        else:
            st.success("All tracked categories are sufficiently stocked.")


if __name__ == "__main__":
    main()
