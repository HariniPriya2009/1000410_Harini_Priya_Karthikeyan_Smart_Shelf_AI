"""
StockSense Pro — Cute Shelf Intelligence Dashboard 🛒✨
=========================================================
Step 5: Dashboard Development (Summative Assessment)

Features
--------
- Upload a shelf image -> YOLO detection -> annotated output
- Cute pastel UI: gradient banner, KPI cards, rounded cards, emoji icons
- Live KPI row: total items, in-stock / low / out counts, shelf health
- 2x2 analytics grid: products per category, stock status donut,
  shelf fill levels, restock urgency
- Color-coded stock table with progress bars + status chips
- Smart restock alerts + recommendations bubbles
- CSV report download
- Demo mode with sample shelf images (works without upload)

Run locally:
    streamlit run streamlit_app.py
"""

import sys
import csv
import io
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from ultralytics import YOLO

# ------------------------------------------------------------------ paths
THIS_DIR = Path(__file__).resolve().parent
if (THIS_DIR / "src").exists():
    REPO_ROOT = THIS_DIR
else:
    REPO_ROOT = THIS_DIR.parent
sys.path.append(str(REPO_ROOT))

from src.stock_insights import build_stock_report, restocking_priority  # noqa: E402
from theme import inject_css, banner, kpi_cards, section_title  # noqa: E402

MODEL_PATH = REPO_ROOT / "models" / "best.pt"
ASSETS_DIR = REPO_ROOT / "assets"

# ------------------------------------------------------------------ constants
STATUS_COLORS = {
    "Out of Stock": "#f4726b",
    "Low Stock": "#f7b955",
    "In Stock": "#4ec77f",
}
STATUS_EMOJI = {
    "Out of Stock": "🚫",
    "Low Stock": "⚠️",
    "In Stock": "✅",
}

# pretty display names for the model's classes
PRETTY_NAMES = {
    "1_puffed_food": "🥨 Puffed Food",
    "13_dried_fruit": "🍇 Dried Fruit",
    "22_dried_food": "🥫 Dried Food",
    "31_instant_drink": "🥤 Instant Drink",
    "42_instant_noodles": "🍜 Instant Noodles",
    "54_dessert": "🍰 Dessert",
    "71_drink": "🧃 Drinks",
    "79_alcohol": "🍾 Alcohol",
}

PLOT_COLORS = ["#8ec5fc", "#c7a6f3", "#f9c6d0", "#fde7a9", "#a9e8e0", "#9be7a9", "#ffb3ad", "#b8a7f8"]


# ------------------------------------------------------------------ helpers
@st.cache_resource
def load_model(path: str):
    return YOLO(path)


def run_detection(model, image: np.ndarray, conf_threshold: float):
    """Run YOLO on an image. Returns (annotated_bgr, class_ids, class_names, confidences)."""
    results = model.predict(image, conf=conf_threshold, verbose=False)[0]
    annotated = results.plot()
    if results.boxes is not None:
        class_ids = [int(c) for c in results.boxes.cls.tolist()]
        confs = [float(c) for c in results.boxes.conf.tolist()]
    else:
        class_ids, confs = [], []
    class_names = [model.names[i] for i in sorted(model.names)]
    return annotated, class_ids, class_names, confs


def to_dataframe(report) -> pd.DataFrame:
    """Build the cute stock table as a DataFrame."""
    rows = []
    for c in report.categories:
        rows.append(
            {
                "Product": pretty(c.name),
                "Count": c.count,
                "Status": c.status,
                "Emoji": STATUS_EMOJI[c.status],
                "Alert": c.alert,
            }
        )
    return pd.DataFrame(rows)


def stock_table_html(df: pd.DataFrame) -> str:
    """Render the stock table with chips + progress bars (compact, markdown-safe HTML)."""
    max_count = max(df["Count"].max(), 1)
    rows = ""
    for _, r in df.iterrows():
        pct = min(int(r["Count"] / max_count * 100), 100)
        color = STATUS_COLORS[r["Status"]]
        chip = "chip-ok" if r["Status"] == "In Stock" else ("chip-low" if r["Status"] == "Low Stock" else "chip-out")
        rows += (
            '<tr>'
            f'<td>{r["Product"]}</td>'
            f'<td style="text-align:center;">{r["Count"]}</td>'
            '<td><div class="bar-wrap">'
            f'<div class="bar-fill" style="width:{pct}%;background:linear-gradient(90deg,{color}99,{color});"></div>'
            '</div></td>'
            f'<td><span class="chip {chip}">{r["Emoji"]} {r["Status"]}</span></td>'
            '</tr>'
        )
    return (
        '<table class="cute-table">'
        '<thead><tr><th>Product</th><th style="text-align:center;">Units</th><th>Shelf Fill</th><th>Status</th></tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table>'
    )


def shelf_health_score(report) -> int:
    """0-100 score: % of categories not out of stock (weight low stock half)."""
    if not report.categories:
        return 0
    score = 0.0
    for c in report.categories:
        if c.status == "In Stock":
            score += 1
        elif c.status == "Low Stock":
            score += 0.5
    return int(round(score / len(report.categories) * 100))


def pretty(name: str) -> str:
    """Convert raw class name to cute display name (emoji + title)."""
    return PRETTY_NAMES.get(name, name.replace("_", " ").title())


def recommendation_bubbles(report) -> list:
    """Turn stock report into smart recommendation bubbles."""
    out_of = [c for c in report.categories if c.status == "Out of Stock"]
    low = [c for c in report.categories if c.status == "Low Stock"]
    ok = [c for c in report.categories if c.status == "In Stock"]
    bubbles = []
    if out_of:
        names = ", ".join(pretty(c.name) for c in out_of[:4]) + ("…" if len(out_of) > 4 else "")
        bubbles.append(("🚨", f"<b>Urgent!</b> {len(out_of)} categor{'y is' if len(out_of)==1 else 'ies are'} completely out of stock ({names}). Order new stock today!"))
    if low:
        names = ", ".join(pretty(c.name) for c in low[:4]) + ("…" if len(low) > 4 else "")
        bubbles.append(("⚠️", f"<b>Restock soon:</b> {len(low)} categor{'y' if len(low)==1 else 'ies'} running low ({names}). Schedule a refill this week."))
    if ok:
        bubbles.append(("🌟", f"<b>Great job!</b> {len(ok)} categor{'y is' if len(ok)==1 else 'ies are'} fully stocked and healthy."))
    if not out_of and not low:
        bubbles.append(("🎉", "<b>All clear!</b> No restocking needed right now — your shelves look wonderful!"))
    # fast mover heuristic: most units on shelf = likely fast seller
    if report.categories:
        best = max(report.categories, key=lambda c: c.count)
        if best.count >= 4:
            bubbles.append(("📈", f"<b>Top performer:</b> {pretty(best.name)} has {best.count} units — your best-stocked category. Keep it up front!"))
    return bubbles


def render_bubbles(bubbles: list):
    """Render alert bubbles one compact HTML string each (markdown-safe)."""
    for ico, text in bubbles:
        cls = "alert-info"
        if ico == "🚨":
            cls = "alert-out"
        elif ico == "⚠️":
            cls = "alert-low"
        elif ico in ("🌟", "🎉"):
            cls = "alert-ok"
        st.markdown(
            f'<div class="alert-bubble {cls}"><span style="font-size:1.2rem">{ico}</span><span>{text}</span></div>',
            unsafe_allow_html=True,
        )


def csv_download(report) -> str:
    """Build CSV report string for download button."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Product", "Units", "Status", "Alert"])
    for c in report.categories:
        w.writerow([pretty(c.name), c.count, c.status, c.alert])
    w.writerow([])
    w.writerow(["Total items", report.total_items])
    w.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M")])
    return buf.getvalue()


# ------------------------------------------------------------------ main
def main():
    st.set_page_config(page_title="StockSense Pro 🛒", page_icon="🛒", layout="wide")

    # ---------- cute theme ----------
    st.markdown(inject_css(), unsafe_allow_html=True)
    st.markdown(
        banner(
            "🛒 StockSense Pro — Shelf Intelligence",
            "Upload a shelf image to detect products, count stock & get instant restock alerts!",
            "✨ AI-Powered Retail Vision",
        ),
        unsafe_allow_html=True,
    )

    # ---------- sidebar ----------
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        conf_threshold = st.slider("🔍 Detection confidence", 0.10, 0.90, 0.25, 0.05)
        st.markdown("---")
        st.markdown("### 📊 Stock Thresholds")
        st.markdown(
            "<div style='font-family:Quicksand;line-height:1.9'>"
            "<span class='chip chip-out'>0 units</span> &nbsp;→ Out of Stock<br>"
            "<span class='chip chip-low'>1–3 units</span> &nbsp;→ Low Stock<br>"
            "<span class='chip chip-ok'>4+ units</span> &nbsp;→ In Stock</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown("### 💡 How it works")
        st.markdown(
            "<div style='font-family:Quicksand;font-size:0.9rem;line-height:1.7'>"
            "1️⃣ Upload or pick a sample shelf image<br>"
            "2️⃣ YOLO detects every product on the shelf<br>"
            "3️⃣ Stock levels are classified & alerts fire<br>"
            "4️⃣ You get a full analytics dashboard 📊</div>",
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.8rem;color:#8a7fa8;text-align:center'>"
            "Made with 💜 by Harini Priya<br>Summative Assessment • CRS AI</div>",
            unsafe_allow_html=True,
        )

    # ---------- image input ----------
    if not MODEL_PATH.exists():
        st.error(f"No trained model found at `{MODEL_PATH}` — train the model and copy weights to `models/best.pt`.")
        return

    model = load_model(str(MODEL_PATH))

    with st.container(border=True):
        st.markdown(section_title("📷", "Upload your shelf image"), unsafe_allow_html=True)
        up_col, demo_col = st.columns([3, 2])
        with up_col:
            uploaded_file = st.file_uploader("Upload a shelf image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        with demo_col:
            demo_images = sorted(ASSETS_DIR.glob("demo_shelf_*.jpg")) if ASSETS_DIR.exists() else []
            demo_choice = st.selectbox(
                "…or try a sample shelf 🧸",
                ["None"] + [f.name for f in demo_images],
            )

    if uploaded_file is None and (demo_choice is None or demo_choice == "None"):
        st.markdown(
            '<div class="hero-tip">👆 Upload your own shelf image or pick one of the cute sample shelves to see the magic happen! ✨</div>',
            unsafe_allow_html=True,
        )
        return

    # ---------- load image ----------
    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert("RGB")
        source_label = "Your upload"
    else:
        image = Image.open(ASSETS_DIR / demo_choice).convert("RGB")
        source_label = f"Sample: {demo_choice}"

    image_np = np.array(image)

    # ---------- detection ----------
    with st.spinner("🔍 Analyzing your shelf..."):
        annotated_bgr, class_ids, class_names, confs = run_detection(model, image_np, conf_threshold)
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        report = build_stock_report(class_ids, class_names)

    avg_conf = (sum(confs) / len(confs) * 100) if confs else 0.0

    df = to_dataframe(report)
    n_out = sum(1 for c in report.categories if c.status == "Out of Stock")
    n_low = sum(1 for c in report.categories if c.status == "Low Stock")
    n_ok = sum(1 for c in report.categories if c.status == "In Stock")
    health = shelf_health_score(report)

    # ---------- KPI cards ----------
    st.markdown(
        kpi_cards(
            [
                {"icon": "📦", "value": report.total_items, "label": "Products Detected", "color": "kpi-blue"},
                {"icon": "✅", "value": n_ok, "label": "In Stock", "color": "kpi-green"},
                {"icon": "⚠️", "value": n_low, "label": "Low Stock", "color": "kpi-yellow"},
                {"icon": "🚫", "value": n_out, "label": "Out of Stock", "color": "kpi-red"},
                {"icon": "💚", "value": f"{health}%", "label": "Shelf Health", "color": "kpi-purple"},
                {"icon": "🎯", "value": f"{avg_conf:.0f}%", "label": "Avg Confidence", "color": "kpi-teal"},
            ]
        ),
        unsafe_allow_html=True,
    )

    # ---------- detection view ----------
    with st.container(border=True):
        st.markdown(section_title("🔬", "Detection Results"), unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            st.markdown("<p style='text-align:center;font-weight:700;color:#6b4fae'>📷 Original Shelf</p>", unsafe_allow_html=True)
            st.image(image_np, use_container_width=True)
        with right:
            st.markdown("<p style='text-align:center;font-weight:700;color:#6b4fae'>✨ Detected Products</p>", unsafe_allow_html=True)
            st.image(annotated_rgb, use_container_width=True)
        st.caption(f"Source: {source_label} • {report.total_items} products detected • YOLOv8 model • confidence ≥ {conf_threshold:.2f}")

    # ---------- analytics grid (2x2) ----------
    with st.container(border=True):
        st.markdown(section_title("📊", "Shelf Analytics"), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<p style='text-align:center;font-weight:700;color:#6b4fae;font-size:0.95rem'>🧺 Products per Category</p>", unsafe_allow_html=True)
            counts_df = df[df["Count"] > 0].sort_values("Count", ascending=False)
            if counts_df.empty:
                st.markdown('<div class="hero-tip">No products detected — try lowering the confidence slider! 🪄</div>', unsafe_allow_html=True)
            else:
                st.bar_chart(counts_df.set_index("Product")["Count"], color="#9a7ce8")

            st.markdown("<p style='text-align:center;font-weight:700;color:#6b4fae;font-size:0.95rem;margin-top:14px'>🚨 Restock Urgency</p>", unsafe_allow_html=True)
            urgency_df = df.copy()
            urgency_df["Urgency"] = urgency_df["Status"].map({"Out of Stock": 3, "Low Stock": 2, "In Stock": 1})
            urgency_df = urgency_df.sort_values("Urgency", ascending=True)
            st.bar_chart(urgency_df.set_index("Product")["Urgency"], color="#f4726b")
        with c2:
            st.markdown("<p style='text-align:center;font-weight:700;color:#6b4fae;font-size:0.95rem'>🍩 Stock Status Overview</p>", unsafe_allow_html=True)
            donut_df = pd.DataFrame(
                {"Status": ["In Stock", "Low Stock", "Out of Stock"], "Categories": [n_ok, n_low, n_out]}
            ).set_index("Status")
            st.bar_chart(donut_df, color="#4ec77f")

            st.markdown("<p style='text-align:center;font-weight:700;color:#6b4fae;font-size:0.95rem;margin-top:14px'>📦 Shelf Fill Levels</p>", unsafe_allow_html=True)
            fill_df = df.copy()
            max_count = max(fill_df["Count"].max(), 1)
            fill_df["Fill %"] = (fill_df["Count"] / max_count * 100).round(0)
            fill_df = fill_df.sort_values("Fill %", ascending=False)
            st.bar_chart(fill_df.set_index("Product")["Fill %"], color="#7cc7f8")

    # ---------- stock table ----------
    with st.container(border=True):
        st.markdown(section_title("📋", "Stock Status Details"), unsafe_allow_html=True)
        st.markdown(stock_table_html(df), unsafe_allow_html=True)

    # ---------- alerts + recommendations ----------
    with st.container(border=True):
        st.markdown(section_title("🔔", "Restock Alerts & Smart Recommendations"), unsafe_allow_html=True)
        bubbles = recommendation_bubbles(report)
        if bubbles:
            render_bubbles(bubbles)

    # ---------- download ----------
    with st.container(border=True):
        st.markdown(section_title("⬇️", "Download Report"), unsafe_allow_html=True)
        dl1, dl2, dl3 = st.columns([2, 1, 1])
        with dl1:
            st.download_button(
                "📄 Download Stock Report (CSV)",
                data=csv_download(report),
                file_name=f"stock_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                "🖼️ Download Annotated Image",
                data=cv2.imencode(".jpg", annotated_bgr)[1].tobytes(),
                file_name="detected_shelf.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )
        with dl3:
            st.download_button(
                "📊 Download Data (CSV)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="shelf_data.csv",
                mime="text/csv",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
