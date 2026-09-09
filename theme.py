"""
Custom cute theme CSS for StockSense Pro.
Pastel gradient header, rounded cards, soft shadows, emoji icons.
Inject via st.markdown(..., unsafe_allow_html=True).
"""

def inject_css() -> str:
    return """
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&family=Baloo+2:wght@600;700&display=swap" rel="stylesheet">

    <style>
    /* ---------- base ---------- */
    .stApp {
        background: linear-gradient(180deg, #fdf6ff 0%, #f3f8ff 45%, #fef9f4 100%);
        font-family: 'Quicksand', sans-serif;
    }
    #MainMenu, footer, header {visibility: hidden;}

    h1, h2, h3 { font-family: 'Baloo 2', cursive !important; color: #4a3f6b !important; }

    /* ---------- cute gradient banner ---------- */
    .banner {
        background: linear-gradient(100deg, #8ec5fc 0%, #e0c3fc 35%, #f9c6d0 65%, #fde7a9 100%);
        border-radius: 24px;
        padding: 28px 34px;
        color: #ffffff;
        box-shadow: 0 10px 30px rgba(176, 137, 235, 0.35);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        flex-wrap: wrap;
        position: relative;
        overflow: hidden;
    }
    .banner::after {
        content: "";
        position: absolute;
        right: -30px; top: -45px;
        width: 170px; height: 170px;
        background: rgba(255,255,255,0.25);
        border-radius: 50%;
    }
    .banner::before {
        content: "";
        position: absolute;
        right: 90px; bottom: -60px;
        width: 120px; height: 120px;
        background: rgba(255,255,255,0.18);
        border-radius: 50%;
    }
    .banner-title {
        font-family: 'Baloo 2', cursive;
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.15;
        text-shadow: 0 2px 10px rgba(74, 63, 107, 0.35);
        color: #ffffff;
    }
    .banner-sub {
        font-family: 'Quicksand', sans-serif;
        font-size: 0.98rem;
        font-weight: 600;
        margin: 6px 0 0 0;
        opacity: 0.95;
        color: #ffffff;
        text-shadow: 0 1px 6px rgba(74, 63, 107, 0.3);
    }
    .banner-badge {
        background: rgba(255,255,255,0.92);
        color: #6b4fae;
        padding: 8px 18px;
        border-radius: 999px;
        font-family: 'Quicksand', sans-serif;
        font-weight: 700;
        font-size: 0.9rem;
        box-shadow: 0 4px 14px rgba(74, 63, 107, 0.25);
        white-space: nowrap;
    }

    /* ---------- KPI metric cards ---------- */
    .kpi-row { display: flex; gap: 14px; flex-wrap: wrap; margin: 18px 0 6px 0; }
    .kpi {
        flex: 1 1 0;
        min-width: 145px;
        border-radius: 20px;
        padding: 16px 14px;
        color: #fff;
        text-align: center;
        box-shadow: 0 8px 20px rgba(74,63,107,0.18);
        transition: transform .18s ease;
    }
    .kpi:hover { transform: translateY(-5px) rotate(-0.6deg); }
    .kpi .ico { font-size: 1.55rem; }
    .kpi .val {
        font-family: 'Baloo 2', cursive;
        font-size: 1.9rem;
        font-weight: 700;
        line-height: 1.1;
        margin-top: 2px;
    }
    .kpi .lbl {
        font-size: 0.78rem;
        font-weight: 600;
        opacity: 0.95;
        letter-spacing: 0.2px;
    }
    .kpi-blue   { background: linear-gradient(135deg, #7cc7f8, #4a9fe8); }
    .kpi-green  { background: linear-gradient(135deg, #9be7a9, #4ec77f); }
    .kpi-yellow { background: linear-gradient(135deg, #ffe29a, #f7b955); }
    .kpi-red    { background: linear-gradient(135deg, #ffb3ad, #f4726b); }
    .kpi-purple { background: linear-gradient(135deg, #c7a6f3, #9a6ee8); }
    .kpi-pink   { background: linear-gradient(135deg, #f9b8d0, #ee7fae); }
    .kpi-teal   { background: linear-gradient(135deg, #a9e8e0, #5ecfc0); }

    /* ---------- section cards ---------- */
    .section-card {
        background: rgba(255,255,255,0.92);
        border: 2px solid #efe6ff;
        border-radius: 22px;
        padding: 18px 22px;
        box-shadow: 0 6px 18px rgba(74,63,107,0.10);
        margin-bottom: 14px;
    }
    .section-title {
        font-family: 'Baloo 2', cursive;
        font-size: 1.15rem;
        font-weight: 700;
        color: #6b4fae;
        margin: 0 0 10px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ---------- stock status chips ---------- */
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
    }
    .chip-ok    { background: #e2f9ea; color: #1e8e4e; border: 1.5px solid #9be7b8; }
    .chip-low   { background: #fff5d6; color: #b78b0a; border: 1.5px solid #f7dd8f; }
    .chip-out   { background: #ffe1de; color: #d63b30; border: 1.5px solid #ffb0aa; }

    /* ---------- alert bubbles ---------- */
    .alert-bubble {
        border-radius: 16px;
        padding: 12px 18px;
        margin: 8px 0;
        font-weight: 600;
        font-size: 0.92rem;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 4px 12px rgba(74,63,107,0.10);
    }
    .alert-out  { background: linear-gradient(90deg, #ffe5e2, #ffd0cb); color: #c43d33; }
    .alert-low  { background: linear-gradient(90deg, #fff6d9, #ffecb0); color: #a97d08; }
    .alert-ok   { background: linear-gradient(90deg, #e3faec, #cdf5dc); color: #238a53; }
    .alert-info { background: linear-gradient(90deg, #e8f1ff, #d3e5ff); color: #2d6fc2; }

    /* ---------- table ---------- */
    .cute-table { width: 100%; border-collapse: separate; border-spacing: 0 8px; font-family: 'Quicksand', sans-serif; }
    .cute-table th {
        text-align: left;
        color: #6b4fae;
        font-family: 'Baloo 2', cursive;
        font-size: 0.9rem;
        padding: 4px 12px;
    }
    .cute-table td {
        background: #ffffff;
        padding: 10px 12px;
        border-top: 1.5px solid #f1e9ff;
        border-bottom: 1.5px solid #f1e9ff;
    }
    .cute-table td:first-child { border-left: 1.5px solid #f1e9ff; border-radius: 14px 0 0 14px; font-weight: 700; color: #4a3f6b; }
    .cute-table td:last-child  { border-right: 1.5px solid #f1e9ff; border-radius: 0 14px 14px 0; }

    /* ---------- progress bars ---------- */
    .bar-wrap { background: #f1e9ff; border-radius: 999px; height: 12px; width: 100%; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 999px; }

    /* ---------- upload dropzone glow ---------- */
    .stFileUploader {
        border: 2px dashed #c7b2f5;
        border-radius: 18px;
        padding: 6px;
        background: rgba(255,255,255,0.85);
    }

    /* ---------- sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #efe2ff 0%, #fdf0f6 100%);
        border-right: 2px solid #e7dcff;
    }
    section[data-testid="stSidebar"] * { font-family: 'Quicksand', sans-serif; }

    /* ---------- streamlit widget polish ---------- */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1.5px solid #efe6ff;
        border-radius: 16px;
        padding: 12px 16px;
        box-shadow: 0 4px 12px rgba(74,63,107,0.08);
    }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 14px 14px 0 0;
        background: #f1e9ff;
        font-family: 'Quicksand', sans-serif;
        font-weight: 700;
        color: #6b4fae;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #b69df2, #9a7ce8);
        color: #ffffff;
    }

    /* dividers */
    hr { border: none; border-top: 2px dashed #e3d6ff !important; margin: 14px 0; }

    /* ---------- native bordered containers styled cute ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,0.95);
        border: 2px solid #efe6ff !important;
        border-radius: 22px !important;
        box-shadow: 0 6px 18px rgba(74,63,107,0.10);
        padding: 6px 8px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: #d9c8ff !important; }

    /* scroll hint strip */
    .hero-tip {
        background: rgba(255,255,255,0.9);
        border: 2px solid #efe6ff;
        border-radius: 18px;
        padding: 10px 18px;
        color: #6b6385;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 10px 0 4px 0;
        text-align: center;
    }
    </style>
    """


def banner(title: str, subtitle: str, badge: str) -> str:
    """Cute gradient banner with title + subtitle + badge (compact single-line HTML)."""
    return (
        '<div class="banner"><div>'
        f'<p class="banner-title">{title}</p>'
        f'<p class="banner-sub">{subtitle}</p>'
        '</div>'
        f'<div class="banner-badge">{badge}</div>'
        '</div>'
    )


def kpi_cards(cards: list) -> str:
    """
    cards: list of dicts {icon, value, label, color}
    color: one of kpi-blue/green/yellow/red/purple/pink/teal
    Compact single-line HTML (markdown-safe).
    """
    items = "".join(
        f'<div class="kpi {c["color"]}">'
        f'<div class="ico">{c["icon"]}</div>'
        f'<div class="val">{c["value"]}</div>'
        f'<div class="lbl">{c["label"]}</div>'
        '</div>'
        for c in cards
    )
    return f'<div class="kpi-row">{items}</div>'


def section_title(icon: str, text: str) -> str:
    """Cute section heading (compact single-line HTML)."""
    return f'<p class="section-title"><span>{icon}</span> {text}</p>'
