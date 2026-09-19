"""
Global GDP Explorer — interactive economic intelligence dashboard.

Author : Noura Maher Elamin
Stack  : Streamlit · pandas · numpy · plotly
Data   : World Bank, GDP (current US$), NY.GDP.MKTP.CD
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_TITLE = "Global GDP Explorer"
OWNER = "Noura Maher Elamin"
LINKEDIN = "https://www.linkedin.com/in/nouramaherelamin/"
GITHUB = "https://github.com/nouramaherelamin"
COPYRIGHT_YEAR = 2026

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ──────────────────────────────────────────────────────────────────────────────
# Entity classification
#
# The World Bank file mixes 217 countries/territories with 49 aggregate rows
# (regions, income groups, lending categories). Aggregates must never enter a
# ranking, a map or a country-level statistic, otherwise "World" outranks the
# United States and global GDP is double counted. The list below is resolved
# from ISO-3 codes only, so no extra dependency such as pycountry is required.
# ──────────────────────────────────────────────────────────────────────────────
AGGREGATE_CODES = frozenset(
    {
        "AFE", "AFW", "ARB", "CEB", "CSS", "EAP", "EAR", "EAS", "ECA", "ECS",
        "EMU", "EUU", "FCS", "HIC", "HPC", "IBD", "IBT", "IDA", "IDB", "IDX",
        "INX", "LAC", "LCN", "LDC", "LIC", "LMC", "LMY", "LTE", "MEA", "MIC",
        "MNA", "NAC", "OED", "OSS", "PRE", "PSS", "PST", "SAS", "SSA", "SSF",
        "SST", "TEA", "TEC", "TLA", "TMN", "TSA", "TSS", "UMC", "WLD",
    }
)

# Backstop for codes the list above does not know: aggregate names follow
# recognisable phrases. Matched on whole words only, so a country such as
# Trinidad and Tobago is never mistaken for an IDA grouping.
AGGREGATE_NAME_PATTERN = re.compile(
    r"\b(?:world|income|IDA|IBRD|euro\s+area|european\s+union|OECD|arab\s+world"
    r"|small\s+states|dividend|not\s+classified|fragile|heavily\s+indebted"
    r"|least\s+developed|excluding)\b",
    re.IGNORECASE,
)

# Codes that are real territories but have no ISO-3 geometry in Plotly's map.
NO_MAP_GEOMETRY = frozenset({"CHI", "XKX", "MAF", "SXM", "CUW"})

PALETTE = ["#6EE7D7", "#7DAEFF", "#B79CFF", "#F7A3C4", "#FFC978", "#8FE3A2",
           "#FF9F87", "#9BD7FF"]
SEQ_SCALE = ["#0d2438", "#12496b", "#15749c", "#1fa3b8", "#54d3c2", "#a9f3df"]
DIVERGING = ["#e0576f", "#f0a08a", "#f5e6c8", "#8fd6b4", "#2fa587"]


# ──────────────────────────────────────────────────────────────────────────────
# Theme
# ──────────────────────────────────────────────────────────────────────────────
def inject_presentation_css() -> None:
    """Widen the canvas and hide the sidebar for screen sharing."""
    st.html(
        """
        <style>
        section[data-testid="stSidebar"] { display: none !important; }
        div.block-container { max-width: 1680px; padding-left: 3rem; padding-right: 3rem; }
        .kpi-value { font-size: 2.05rem !important; }
        .hero-title { font-size: clamp(2.8rem, 5.4vw, 5rem) !important; }
        </style>
        """
    )


def inject_theme() -> None:
    """Inject the dashboard stylesheet. Runs before any widget is drawn."""
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@500;600;700&display=swap');

        :root {
            --ink-900: #04090f;
            --ink-800: #071322;
            --surface: rgba(16, 33, 54, 0.62);
            --surface-2: rgba(23, 45, 72, 0.74);
            --line: rgba(148, 183, 226, 0.14);
            --line-strong: rgba(148, 183, 226, 0.28);
            --text: #eef4fb;
            --muted: #93a9c4;
            --faint: #6d85a1;
            --teal: #6ee7d7;
            --blue: #7daeff;
            --violet: #b79cff;
            --rose: #f7a3c4;
            --coral: #ff9f87;
            --amber: #ffc978;
            --radius-lg: 24px;
            --radius-md: 16px;
        }

        html, body, .stApp, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
            font-feature-settings: 'cv02', 'cv03';
        }

        .stApp {
            color: var(--text);
            background:
                radial-gradient(1100px 620px at 6% -8%, rgba(125, 174, 255, 0.16), transparent 62%),
                radial-gradient(900px 520px at 96% 2%, rgba(183, 156, 255, 0.14), transparent 60%),
                radial-gradient(1000px 700px at 50% 108%, rgba(110, 231, 215, 0.10), transparent 62%),
                linear-gradient(168deg, var(--ink-900) 0%, var(--ink-800) 48%, #030811 100%);
            background-attachment: fixed;
        }

        div.block-container { max-width: 1560px; padding-top: 1.2rem; padding-bottom: 3rem; }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stDecoration"] { display: none; }

        h1, h2, h3, h4, .hero-title, .kpi-value, .stat-value {
            font-family: 'Sora', 'Inter', sans-serif;
            letter-spacing: -0.015em;
        }

        .kpi-value, .stat-value, .rank-figure, [data-testid="stMetricValue"] {
            font-variant-numeric: tabular-nums;
        }

        /* Sidebar ------------------------------------------------------- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(190deg, rgba(7, 18, 32, 0.96), rgba(3, 9, 17, 0.98));
            border-right: 1px solid var(--line);
            backdrop-filter: blur(14px);
        }
        section[data-testid="stSidebar"] .stMarkdown p { color: var(--muted); }
        section[data-testid="stSidebar"] label { color: #c8dbf2 !important; font-weight: 600; }
        .side-brand { display: flex; align-items: center; gap: 0.7rem; padding: 0.35rem 0 1rem; }
        .side-mark {
            width: 42px; height: 42px; border-radius: 13px; display: grid; place-items: center;
            font-size: 1.25rem;
            background: linear-gradient(140deg, rgba(110,231,215,0.22), rgba(125,174,255,0.20));
            border: 1px solid var(--line-strong);
        }
        .side-name { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 1.05rem; line-height: 1.15; }
        .side-sub { color: var(--faint); font-size: 0.74rem; margin-top: 0.15rem; }
        .side-heading {
            color: var(--faint); font-size: 0.72rem; font-weight: 700;
            letter-spacing: 0.06em; margin: 0.9rem 0 0.35rem;
        }
        .side-foot { color: var(--faint); font-size: 0.72rem; line-height: 1.6; }
        .side-foot a { color: var(--teal); text-decoration: none; font-weight: 600; }

        section[data-testid="stSidebar"] [role="radiogroup"] { gap: 0.15rem; }
        section[data-testid="stSidebar"] [role="radiogroup"] label {
            border-radius: 11px; padding: 0.42rem 0.6rem;
            transition: background 0.18s ease, color 0.18s ease;
        }
        section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: rgba(125, 174, 255, 0.10);
        }
        section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(95deg, rgba(110,231,215,0.16), rgba(125,174,255,0.10));
            box-shadow: inset 2px 0 0 var(--teal);
        }

        /* Hero ---------------------------------------------------------- */
        .hero {
            position: relative; overflow: hidden;
            padding: 2.3rem 2.5rem; margin-bottom: 1.3rem;
            border: 1px solid var(--line); border-radius: 28px;
            background: linear-gradient(135deg, rgba(24, 49, 80, 0.82), rgba(8, 19, 34, 0.68));
            backdrop-filter: blur(18px);
            box-shadow: 0 28px 70px rgba(0, 0, 0, 0.36);
            animation: rise 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
        }
        .hero::before {
            content: ""; position: absolute; inset: -40% -10% auto auto;
            width: 420px; height: 420px; border-radius: 50%;
            background: radial-gradient(circle, rgba(110, 231, 215, 0.18), transparent 68%);
            pointer-events: none;
        }
        .hero-kicker { color: var(--teal); font-size: 0.78rem; font-weight: 600; letter-spacing: 0.03em; }
        .hero-title {
            font-size: clamp(2.2rem, 4.4vw, 3.9rem); font-weight: 700; line-height: 1.02;
            margin: 0.55rem 0 0;
            background: linear-gradient(96deg, #ffffff 8%, #cfe6ff 52%, #93f0e0 96%);
            -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
        }
        .hero-text { position: relative; max-width: 62ch; margin-top: 0.85rem; color: #a9bed6; line-height: 1.68; }
        .hero-meta { position: relative; display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.25rem; }
        .chip {
            display: inline-flex; align-items: center; gap: 0.45rem;
            padding: 0.44rem 0.85rem; border-radius: 999px;
            border: 1px solid var(--line-strong); background: rgba(110, 231, 215, 0.07);
            color: #cfe9f5; font-size: 0.78rem; font-weight: 600;
        }
        .pulse {
            width: 7px; height: 7px; border-radius: 50%; background: var(--teal);
            box-shadow: 0 0 0 0 rgba(110, 231, 215, 0.6); animation: pulse 2.6s ease-out infinite;
        }

        /* Sections ------------------------------------------------------ */
        .sec { margin: 1.5rem 0 0.7rem; }
        .sec-title { font-size: 1.3rem; font-weight: 600; margin: 0; }
        .sec-sub { color: var(--muted); font-size: 0.9rem; margin-top: 0.25rem; max-width: 76ch; line-height: 1.6; }

        /* Cards --------------------------------------------------------- */
        .kpi {
            position: relative; overflow: hidden; height: 100%;
            padding: 1.15rem 1.25rem; border-radius: var(--radius-lg);
            border: 1px solid var(--line);
            background: linear-gradient(150deg, var(--surface-2), var(--surface));
            backdrop-filter: blur(16px);
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.24);
            animation: rise 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
            transition: transform 0.22s ease, border-color 0.22s ease;
        }
        .kpi:hover { transform: translateY(-3px); border-color: var(--line-strong); }
        .kpi::after {
            content: ""; position: absolute; right: -56px; bottom: -56px;
            width: 140px; height: 140px; border-radius: 50%;
            background: radial-gradient(circle, rgba(125, 174, 255, 0.16), transparent 70%);
        }
        .kpi-top { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
        .kpi-icon { font-size: 1.1rem; }
        .kpi-label { color: var(--muted); font-size: 0.78rem; font-weight: 600; }
        .kpi-value { margin-top: 0.55rem; font-size: 1.72rem; font-weight: 700; color: #fff; line-height: 1.1; }
        .kpi-note { margin-top: 0.3rem; color: var(--faint); font-size: 0.76rem; line-height: 1.5; }
        .delta { font-size: 0.78rem; font-weight: 600; padding: 0.16rem 0.5rem; border-radius: 999px; white-space: nowrap; }
        .delta.up { color: #8fe3a2; background: rgba(143, 227, 162, 0.12); }
        .delta.down { color: #ff9aa8; background: rgba(255, 154, 168, 0.12); }
        .delta.flat { color: var(--faint); background: rgba(148, 183, 226, 0.10); }

        .panel {
            padding: 1.3rem 1.45rem; border-radius: var(--radius-lg);
            border: 1px solid var(--line);
            background: linear-gradient(155deg, var(--surface-2), var(--surface));
            backdrop-filter: blur(16px); height: 100%;
        }
        .panel h4 { margin: 0 0 0.5rem; font-size: 1.02rem; color: #fff; }
        .panel p, .panel li { color: #a3b8d0; line-height: 1.72; font-size: 0.92rem; }
        .panel ul { margin: 0.3rem 0 0.9rem; padding-left: 1.1rem; }

        .rank-card {
            position: relative; padding: 1rem 1.1rem; border-radius: var(--radius-md);
            border: 1px solid var(--line); background: var(--surface);
            backdrop-filter: blur(12px); height: 100%;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .rank-card:hover { transform: translateY(-3px); border-color: var(--line-strong); }
        .rank-pos { color: var(--teal); font-size: 0.76rem; font-weight: 700; }
        .rank-name { margin-top: 0.3rem; font-weight: 600; color: #fff; font-size: 0.98rem; line-height: 1.3; }
        .rank-figure { margin-top: 0.35rem; color: #b9cbe0; font-size: 0.9rem; }
        .rank-bar { margin-top: 0.7rem; height: 4px; border-radius: 999px; background: rgba(148, 183, 226, 0.14); overflow: hidden; }
        .rank-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--teal), var(--blue)); }
        .rank-share { margin-top: 0.42rem; color: var(--faint); font-size: 0.74rem; }

        .insight {
            padding: 0.9rem 1.1rem; margin-bottom: 0.6rem;
            border: 1px solid var(--line); border-left: 3px solid var(--teal);
            border-radius: 4px 16px 16px 4px;
            background: linear-gradient(95deg, rgba(110, 231, 215, 0.07), rgba(16, 33, 54, 0.35));
            color: #c2d4e8; font-size: 0.9rem; line-height: 1.65;
        }
        .insight b { color: #fff; font-weight: 600; }
        .insight.blue { border-left-color: var(--blue); background: linear-gradient(95deg, rgba(125,174,255,0.07), rgba(16,33,54,0.35)); }
        .insight.violet { border-left-color: var(--violet); background: linear-gradient(95deg, rgba(183,156,255,0.07), rgba(16,33,54,0.35)); }
        .insight.rose { border-left-color: var(--rose); background: linear-gradient(95deg, rgba(247,163,196,0.07), rgba(16,33,54,0.35)); }

        .link-btn {
            display: inline-flex; align-items: center; gap: .5rem;
            padding: .62rem 1.15rem; margin: .3rem .35rem 0 0;
            border-radius: 12px; border: 1px solid var(--line-strong);
            background: linear-gradient(140deg, rgba(125,174,255,.14), rgba(110,231,215,.09));
            color: #dcebff; font-weight: 600; font-size: .9rem; text-decoration: none;
            transition: border-color .18s ease, transform .18s ease;
        }
        .link-btn:hover { border-color: var(--teal); color: #fff; transform: translateY(-2px); }
        .fact-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: .7rem; margin-top: .3rem;
        }
        .fact {
            padding: .75rem .9rem; border-radius: 13px; border: 1px solid var(--line);
            background: rgba(16,33,54,.5);
        }
        .fact-label { color: var(--faint); font-size: .74rem; font-weight: 600; }
        .fact-value { margin-top: .2rem; color: #eef4fb; font-weight: 600; font-size: .95rem;
                      font-variant-numeric: tabular-nums; }

        .vs-card {
            padding: 1.1rem 1.2rem; border-radius: var(--radius-md); border: 1px solid var(--line);
            background: var(--surface); text-align: center;
        }
        .vs-name { font-family: 'Sora', sans-serif; font-weight: 600; font-size: 1.05rem; color: #fff; }
        .vs-score { margin-top: 0.4rem; font-size: 2rem; font-weight: 700; font-variant-numeric: tabular-nums; }
        .vs-note { color: var(--faint); font-size: 0.78rem; margin-top: 0.2rem; }
        .win { color: var(--teal); }
        .lose { color: var(--faint); }

        /* Streamlit widgets --------------------------------------------- */
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            border: 1px solid var(--line); border-radius: var(--radius-md); overflow: hidden;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 0.2rem; border-bottom: 1px solid var(--line); }
        .stTabs [data-baseweb="tab"] { color: var(--muted); font-weight: 600; padding: 0.7rem 1rem; }
        .stTabs [aria-selected="true"] { color: var(--teal) !important; }
        .stButton button, .stDownloadButton button {
            width: 100%; border-radius: 12px; font-weight: 600;
            border: 1px solid var(--line-strong); color: #dcebff;
            background: linear-gradient(140deg, rgba(125, 174, 255, 0.16), rgba(110, 231, 215, 0.10));
            transition: transform 0.18s ease, border-color 0.18s ease;
        }
        .stButton button:hover, .stDownloadButton button:hover {
            transform: translateY(-2px); border-color: var(--teal); color: #fff;
        }
        [data-testid="stMetricValue"] { font-family: 'Sora', sans-serif; }
        :focus-visible { outline: 2px solid var(--teal); outline-offset: 2px; }

        /* Footer -------------------------------------------------------- */
        .foot {
            margin-top: 2.6rem; padding: 1.5rem 0 0.4rem;
            border-top: 1px solid var(--line); text-align: center;
            color: var(--faint); font-size: 0.82rem; line-height: 1.85;
        }
        .foot a { color: var(--teal); text-decoration: none; font-weight: 600; }
        .foot a:hover { text-decoration: underline; }
        .foot-links { display: flex; justify-content: center; gap: 1.4rem; margin-top: 0.4rem; flex-wrap: wrap; }

        @keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(110, 231, 215, 0.55); }
            70% { box-shadow: 0 0 0 9px rgba(110, 231, 215, 0); }
            100% { box-shadow: 0 0 0 0 rgba(110, 231, 215, 0); }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after { animation: none !important; transition: none !important; }
        }
        @media (max-width: 900px) {
            div.block-container { padding-left: 1rem; padding-right: 1rem; }
            .hero { padding: 1.6rem 1.4rem; border-radius: 22px; }
            .kpi-value { font-size: 1.45rem; }
        }
        </style>
        """
    )


def html(markup: str) -> None:
    """Render trusted markup with whitespace collapsed.

    Collapsing prevents Streamlit's markdown pass from ever treating indented
    HTML as a code block, which is what makes raw tags show up in the UI.
    """
    st.html(" ".join(markup.split()))


# ──────────────────────────────────────────────────────────────────────────────
# Formatting
# ──────────────────────────────────────────────────────────────────────────────
def money(value, decimals: int = 2, dash: str = "—") -> str:
    """Format a USD amount with a magnitude suffix."""
    if value is None or pd.isna(value):
        return dash
    value = float(value)
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    for cutoff, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if magnitude >= cutoff:
            return f"{sign}${magnitude / cutoff:,.{decimals}f}{suffix}"
    return f"{sign}${magnitude:,.0f}"


def pct(value, decimals: int = 2, sign: bool = False, dash: str = "—") -> str:
    """Format a percentage value."""
    if value is None or pd.isna(value):
        return dash
    fmt = f"{{:+,.{decimals}f}}%" if sign else f"{{:,.{decimals}f}}%"
    return fmt.format(float(value))


def num(value, decimals: int = 0, dash: str = "—") -> str:
    if value is None or pd.isna(value):
        return dash
    return f"{float(value):,.{decimals}f}"


def delta_chip(value, suffix: str = "%") -> str:
    """Return a coloured delta pill, or an empty string when unavailable."""
    if value is None or pd.isna(value):
        return ""
    tone = "up" if value > 0.05 else "down" if value < -0.05 else "flat"
    arrow = "▲" if tone == "up" else "▼" if tone == "down" else "▪"
    return f'<span class="delta {tone}">{arrow} {float(value):+,.2f}{suffix}</span>'


def kpi(icon: str, label: str, value: str, note: str = "", badge: str = "") -> None:
    html(
        f'<div class="kpi"><div class="kpi-top"><span class="kpi-icon">{icon}</span>{badge}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-note">{note}</div></div>'
    )


def facts(pairs: list[tuple[str, str]]) -> None:
    """Render a compact grid of label/value facts."""
    cells = "".join(
        f'<div class="fact"><div class="fact-label">{label}</div>'
        f'<div class="fact-value">{value}</div></div>'
        for label, value in pairs
    )
    html(f'<div class="fact-grid">{cells}</div>')


def section(title: str, subtitle: str = "") -> None:
    sub = f'<div class="sec-sub">{subtitle}</div>' if subtitle else ""
    html(f'<div class="sec"><div class="sec-title">{title}</div>{sub}</div>')


def insight(text: str, tone: str = "") -> None:
    html(f'<div class="insight {tone}">{text}</div>')


def style_fig(fig: go.Figure, height: int = 460, legend_top: bool = True) -> go.Figure:
    """Apply the dashboard chart theme."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#c9dbef", size=13),
        title=dict(font=dict(family="Sora, sans-serif", size=16, color="#ffffff"), x=0.01, xanchor="left"),
        margin=dict(l=16, r=16, t=58, b=42),
        hoverlabel=dict(bgcolor="#0b1a2c", bordercolor="rgba(148,183,226,.3)", font=dict(color="#fff", family="Inter")),
        colorway=PALETTE,
        separators=".,",
    )
    if legend_top:
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1,
                        bgcolor="rgba(0,0,0,0)", title_text="")
        )
    fig.update_xaxes(gridcolor="rgba(148,183,226,.08)", zerolinecolor="rgba(148,183,226,.16)",
                     linecolor="rgba(148,183,226,.16)", title_font_size=12)
    fig.update_yaxes(gridcolor="rgba(148,183,226,.08)", zerolinecolor="rgba(148,183,226,.16)",
                     linecolor="rgba(148,183,226,.16)", title_font_size=12)
    return fig


def show(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, use_container_width=True, key=key,
                    config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})


def download(label: str, frame: pd.DataFrame, filename: str, key: str) -> None:
    """Offer a dataframe as a UTF-8 CSV download."""
    st.download_button(
        label,
        data=frame.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
        key=key,
    )


inject_theme()


# ──────────────────────────────────────────────────────────────────────────────
# Data layer
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
SEARCH_DIRS = (BASE_DIR, BASE_DIR / "data", BASE_DIR.parent / "data", Path.cwd())


def find_file(name: str) -> Path | None:
    for folder in SEARCH_DIRS:
        candidate = folder / name
        if candidate.is_file():
            return candidate
    return None


def signature(*paths: Path | None) -> tuple:
    """Fingerprint the source files so edits invalidate the cache automatically."""
    marks = []
    for path in paths:
        if path is None:
            marks.append(("missing",))
        else:
            info = path.stat()
            marks.append((str(path), info.st_size, info.st_mtime_ns))
    return tuple(marks)


def classify(codes: pd.Series, names: pd.Series) -> pd.Series:
    """True for individual countries and territories, False for aggregates."""
    by_code = ~codes.str.upper().isin(AGGREGATE_CODES)
    by_name = ~names.fillna("").str.contains(AGGREGATE_NAME_PATTERN, regex=True)
    return by_code & by_name


@st.cache_data(show_spinner="Preparing GDP data…")
def load_data(wide_file: str | None, long_file: str | None, _signature: tuple) -> pd.DataFrame:
    """Build the tidy analytical dataset.

    The wide World Bank export is the source of truth because it carries country
    names. The long export is used when the wide file is unavailable. Growth is
    always recomputed here rather than trusted from the CSV, so a gap in a series
    can never masquerade as a one-year change.
    """
    frame = None

    if wide_file:
        wide = pd.read_csv(wide_file)
        wide = wide.drop(columns=[c for c in wide.columns if str(c).startswith("Unnamed:")], errors="ignore")
        year_columns = [c for c in wide.columns if str(c).strip().isdigit()]
        if not year_columns:
            raise ValueError("No year columns were found in gdp_data.csv.")
        frame = wide.melt(
            id_vars=["Country Name", "Country Code"],
            value_vars=year_columns,
            var_name="Year",
            value_name="GDP",
        )

    if frame is None and long_file:
        long = pd.read_csv(long_file)
        missing = {"Country Code", "Year", "GDP"} - set(long.columns)
        if missing:
            raise ValueError(f"gdp_data_long.csv is missing columns: {', '.join(sorted(missing))}")
        frame = long[["Country Code", "Year", "GDP"]].copy()
        frame["Country Name"] = frame["Country Code"]

    if frame is None:
        raise FileNotFoundError(
            "No data found. Place gdp_data.csv (or gdp_data_long.csv) next to streamlit_app.py."
        )

    frame["Country Code"] = frame["Country Code"].astype(str).str.strip().str.upper()
    frame["Country Name"] = frame["Country Name"].astype(str).str.strip()
    frame["Year"] = pd.to_numeric(frame["Year"], errors="coerce")
    frame["GDP"] = pd.to_numeric(frame["GDP"], errors="coerce")

    frame = frame.dropna(subset=["Year"])
    frame["Year"] = frame["Year"].astype(int)
    frame = frame[frame["Country Code"].str.len() == 3]
    frame = frame.drop_duplicates(subset=["Country Code", "Year"], keep="last")
    frame = frame.sort_values(["Country Code", "Year"]).reset_index(drop=True)

    # Year-over-year growth, computed only between consecutive observed years.
    observed = frame.dropna(subset=["GDP"]).copy()
    observed = observed[observed["GDP"] > 0]
    grouped = observed.groupby("Country Code", sort=False)
    previous_gdp = grouped["GDP"].shift()
    previous_year = grouped["Year"].shift()
    consecutive = (observed["Year"] - previous_year) == 1
    growth = np.where(
        consecutive & previous_gdp.notna() & (previous_gdp > 0),
        (observed["GDP"] / previous_gdp - 1) * 100,
        np.nan,
    )
    observed["YoY Growth %"] = growth
    frame = frame.merge(
        observed[["Country Code", "Year", "YoY Growth %"]],
        on=["Country Code", "Year"],
        how="left",
    )

    frame["Is Country"] = classify(frame["Country Code"], frame["Country Name"])
    return frame[["Country Name", "Country Code", "Year", "GDP", "YoY Growth %", "Is Country"]]


@st.cache_data(show_spinner=False)
def period_metrics(frame: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """Per-country statistics for a period: CAGR, average growth, volatility, peak."""
    window = frame[(frame["Year"] >= start_year) & (frame["Year"] <= end_year)]
    window = window.dropna(subset=["GDP"]).sort_values(["Country Code", "Year"])
    if window.empty:
        return pd.DataFrame(
            columns=["Country Name", "Country Code", "First Year", "Last Year", "First GDP",
                     "Last GDP", "Peak GDP", "Peak Year", "Observations", "CAGR %",
                     "Average Growth %", "Volatility %", "Total Growth %"]
        )

    keys = ["Country Code", "Country Name"]
    summary = window.groupby(keys, as_index=False).agg(
        **{
            "First Year": ("Year", "first"),
            "Last Year": ("Year", "last"),
            "First GDP": ("GDP", "first"),
            "Last GDP": ("GDP", "last"),
            "Peak GDP": ("GDP", "max"),
            "Observations": ("GDP", "size"),
        }
    )

    peak_rows = window.loc[window.groupby("Country Code")["GDP"].idxmax(), ["Country Code", "Year"]]
    peak_rows = peak_rows.rename(columns={"Year": "Peak Year"})
    summary = summary.merge(peak_rows, on="Country Code", how="left")

    # Growth inside the period only: the first year's YoY refers to the year
    # before the window opens, so it is excluded.
    inner = window[window["Year"] > start_year].dropna(subset=["YoY Growth %"])
    growth_stats = inner.groupby("Country Code", as_index=False).agg(
        **{
            "Average Growth %": ("YoY Growth %", "mean"),
            "Volatility %": ("YoY Growth %", "std"),
            "Growth Observations": ("YoY Growth %", "size"),
        }
    )
    summary = summary.merge(growth_stats, on="Country Code", how="left")

    span = summary["Last Year"] - summary["First Year"]
    ratio = summary["Last GDP"] / summary["First GDP"].replace(0, np.nan)
    valid = (span > 0) & (summary["First GDP"] > 0) & (summary["Last GDP"] > 0)
    summary["CAGR %"] = np.where(valid, (ratio ** (1 / span.where(span > 0)) - 1) * 100, np.nan)
    summary["Total Growth %"] = np.where(summary["First GDP"] > 0, (ratio - 1) * 100, np.nan)
    summary.loc[summary["Growth Observations"].fillna(0) < 2, "Volatility %"] = np.nan

    return summary.sort_values("Last GDP", ascending=False).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def endpoint_metrics(frame: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """Per-country metrics anchored on the exact start and end years.

    Custom period analysis compares two specific points in time, so a country
    qualifies for CAGR only when it actually reported GDP in both of those years.
    Each metric carries its own eligibility rule rather than one blanket filter:

    * Total growth and CAGR need a positive GDP value in both endpoint years.
    * Average growth needs at least one year-on-year change inside the window.
    * Volatility needs at least two, since a single change has no spread.
    """
    window = frame[(frame["Year"] >= start_year) & (frame["Year"] <= end_year)]
    window = window.dropna(subset=["GDP"]).sort_values(["Country Code", "Year"])

    columns = ["Country Name", "Country Code", "Start GDP", "End GDP", "Observations",
               "Longest Run", "First Year", "Last Year", "Total Growth %", "CAGR %",
               "Average Growth %", "Volatility %", "Peak GDP", "Peak Year", "Status"]
    if window.empty:
        return pd.DataFrame(columns=columns)

    base = window.groupby(["Country Code", "Country Name"], as_index=False).agg(
        **{
            "Observations": ("GDP", "size"),
            "First Year": ("Year", "min"),
            "Last Year": ("Year", "max"),
            "Peak GDP": ("GDP", "max"),
        }
    )
    peaks = window.loc[window.groupby("Country Code")["GDP"].idxmax(), ["Country Code", "Year"]]
    base = base.merge(peaks.rename(columns={"Year": "Peak Year"}), on="Country Code", how="left")

    endpoints = window[window["Year"].isin([start_year, end_year])]
    pivot = endpoints.pivot_table(index="Country Code", columns="Year", values="GDP", aggfunc="first")
    base["Start GDP"] = base["Country Code"].map(pivot[start_year]) if start_year in pivot.columns else np.nan
    base["End GDP"] = base["Country Code"].map(pivot[end_year]) if end_year in pivot.columns else np.nan

    # Longest run of consecutive reported years inside the window.
    years = window[["Country Code", "Year"]].copy()
    years["Break"] = years.groupby("Country Code")["Year"].diff().ne(1).cumsum()
    runs = years.groupby(["Country Code", "Break"]).size().groupby("Country Code").max()
    base["Longest Run"] = base["Country Code"].map(runs).fillna(0).astype(int)

    inner = window[window["Year"] > start_year].dropna(subset=["YoY Growth %"])
    growth = inner.groupby("Country Code", as_index=False).agg(
        **{
            "Average Growth %": ("YoY Growth %", "mean"),
            "Volatility %": ("YoY Growth %", "std"),
            "Growth Observations": ("YoY Growth %", "size"),
        }
    )
    base = base.merge(growth, on="Country Code", how="left")

    span = end_year - start_year
    both_endpoints = base["Start GDP"].notna() & base["End GDP"].notna() & (base["Start GDP"] > 0)
    ratio = base["End GDP"] / base["Start GDP"].where(base["Start GDP"] > 0)
    base["Total Growth %"] = np.where(both_endpoints, (ratio - 1) * 100, np.nan)
    base["CAGR %"] = np.where(both_endpoints & (span > 0), (ratio ** (1 / span) - 1) * 100, np.nan)

    base.loc[base["Growth Observations"].fillna(0) < 1, "Average Growth %"] = np.nan
    base.loc[base["Growth Observations"].fillna(0) < 2, "Volatility %"] = np.nan

    base["Status"] = np.where(
        both_endpoints, f"Reported in both {start_year} and {end_year}",
        np.where(base["Start GDP"].notna(), f"No {end_year} value",
                 np.where(base["End GDP"].notna(), f"No {start_year} value", "No endpoint values")),
    )
    return base[columns].sort_values("End GDP", ascending=False, na_position="last").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def year_snapshot(frame: pd.DataFrame, year: int) -> pd.DataFrame:
    """Ranked country table for one year, with share and rank."""
    snapshot = frame[(frame["Year"] == year)].dropna(subset=["GDP"]).copy()
    snapshot = snapshot.sort_values("GDP", ascending=False).reset_index(drop=True)
    total = snapshot["GDP"].sum()
    snapshot["GDP Share %"] = snapshot["GDP"] / total * 100 if total else np.nan
    snapshot["Rank"] = np.arange(1, len(snapshot) + 1)
    return snapshot


@st.cache_data(show_spinner=False)
def yearly_totals(frame: pd.DataFrame) -> pd.DataFrame:
    """Global totals per year, plus coverage, computed from countries only."""
    totals = frame.dropna(subset=["GDP"]).groupby("Year", as_index=False).agg(
        **{"GDP": ("GDP", "sum"), "Economies": ("Country Code", "nunique")}
    )
    totals = totals.sort_values("Year").reset_index(drop=True)
    totals["YoY Growth %"] = totals["GDP"].pct_change() * 100
    return totals


@st.cache_data(show_spinner=False)
def concentration(frame: pd.DataFrame, year: int) -> dict:
    """Concentration statistics for one year."""
    snapshot = year_snapshot(frame, year)
    if snapshot.empty:
        return {}
    share = (snapshot["GDP"] / snapshot["GDP"].sum()).to_numpy()
    cumulative = np.cumsum(share) * 100
    hhi = float(np.sum((share * 100) ** 2))
    ordered = np.sort(share)
    n = len(ordered)
    index = np.arange(1, n + 1)
    gini = float((2 * np.sum(index * ordered) / (n * np.sum(ordered))) - (n + 1) / n) if n else np.nan
    to_half = int(np.searchsorted(cumulative, 50) + 1) if n else 0
    return {
        "top1": float(cumulative[0]) if n else np.nan,
        "top5": float(cumulative[min(4, n - 1)]) if n else np.nan,
        "top10": float(cumulative[min(9, n - 1)]) if n else np.nan,
        "top20": float(cumulative[min(19, n - 1)]) if n else np.nan,
        "hhi": hhi,
        "gini": gini,
        "countries_to_half": to_half,
        "cumulative": cumulative,
        "names": snapshot["Country Name"].tolist(),
    }


@st.cache_data(show_spinner=False)
def quality_report(frame: pd.DataFrame) -> dict:
    """Coverage and integrity checks across the whole prepared dataset."""
    countries = frame[frame["Is Country"]]
    observed = frame.dropna(subset=["GDP"])
    span = int(frame["Year"].max() - frame["Year"].min() + 1)

    coverage = (
        frame.dropna(subset=["GDP"])
        .groupby(["Country Name", "Country Code"], as_index=False)
        .agg(**{"First Year": ("Year", "min"), "Last Year": ("Year", "max"), "Observations": ("Year", "nunique")})
    )
    coverage["Expected Years"] = span
    coverage["Coverage %"] = coverage["Observations"] / span * 100
    coverage["Internal Gaps"] = (
        coverage["Last Year"] - coverage["First Year"] + 1 - coverage["Observations"]
    ).clip(lower=0)
    coverage = coverage.sort_values("Coverage %", ascending=False).reset_index(drop=True)

    return {
        "rows": len(frame),
        "observed": len(observed),
        "missing": int(frame["GDP"].isna().sum()),
        "missing_pct": float(frame["GDP"].isna().mean() * 100) if len(frame) else np.nan,
        "entities": int(frame["Country Code"].nunique()),
        "countries": int(countries["Country Code"].nunique()),
        "aggregates": int(frame["Country Code"].nunique() - countries["Country Code"].nunique()),
        "duplicates": int(frame.duplicated(subset=["Country Code", "Year"]).sum()),
        "negatives": int((observed["GDP"] < 0).sum()),
        "zeros": int((observed["GDP"] == 0).sum()),
        "span": span,
        "complete": int((coverage["Coverage %"] >= 99.9).sum()),
        "gap_entities": int((coverage["Internal Gaps"] > 0).sum()),
        "coverage": coverage,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Load
# ──────────────────────────────────────────────────────────────────────────────
wide_path = find_file("gdp_data.csv")
long_path = find_file("gdp_data_long.csv")

try:
    data = load_data(
        str(wide_path) if wide_path else None,
        str(long_path) if long_path else None,
        signature(wide_path, long_path),
    )
except Exception as error:  # noqa: BLE001 - surfaced to the user verbatim
    st.error(f"Could not load the GDP data: {error}")
    st.caption("Expected gdp_data.csv (wide World Bank export) beside streamlit_app.py, in ./data or ../data.")
    st.stop()

countries_only = data[data["Is Country"]].copy()

if countries_only.empty:
    st.error("The dataset contains no individual countries after aggregate rows were removed.")
    st.stop()

MIN_YEAR = int(countries_only["Year"].min())
MAX_YEAR = int(countries_only["Year"].max())
ALL_COUNTRIES = sorted(countries_only["Country Name"].dropna().unique().tolist())
DEFAULT_COMPARE = [c for c in ("United States", "China", "Germany", "Japan", "India") if c in ALL_COUNTRIES]
if not DEFAULT_COMPARE:
    DEFAULT_COMPARE = ALL_COUNTRIES[:4]

PAGES = [
    "Overview",
    "Global Economy",
    "Growth Analysis",
    "World Map",
    "Rankings",
    "Country Profiles",
    "Country Comparison",
    "Head to Head",
    "Custom Analysis",
    "Data Explorer",
    "Data Quality",
    "Download Center",
    "Methodology",
    "About",
]


def reset_filters() -> None:
    for key in ("nav", "period", "year", "compare", "top_n", "presentation"):
        st.session_state.pop(key, None)


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    html(
        '<div class="side-brand"><div class="side-mark">🌍</div>'
        '<div><div class="side-name">GDP Explorer</div>'
        '<div class="side-sub">World Bank national accounts</div></div></div>'
    )

    html('<div class="side-heading">Sections</div>')
    page = st.radio("Sections", PAGES, label_visibility="collapsed", key="nav")

    html('<div class="side-heading">Analysis period</div>')
    period = st.slider(
        "Period",
        min_value=MIN_YEAR,
        max_value=MAX_YEAR,
        value=(MIN_YEAR, MAX_YEAR),
        label_visibility="collapsed",
        key="period",
        help="Every metric on every page is calculated inside this window.",
    )
    period_start, period_end = int(period[0]), int(period[1])

    html('<div class="side-heading">Focus year</div>')
    if period_start == period_end:
        focus_year = period_start
        st.caption(f"Fixed to {focus_year} by the current period.")
    else:
        focus_year = int(
            st.slider(
                "Focus year",
                min_value=period_start,
                max_value=period_end,
                value=period_end,
                label_visibility="collapsed",
                key="year",
                help="Drives the KPI band, rankings, the map and all snapshot figures.",
            )
        )

    html('<div class="side-heading">Countries to compare</div>')
    compare_countries = st.multiselect(
        "Countries",
        ALL_COUNTRIES,
        default=DEFAULT_COMPARE,
        max_selections=10,
        label_visibility="collapsed",
        key="compare",
        placeholder="Search for a country",
    )

    html('<div class="side-heading">Leaderboard size</div>')
    top_n = st.slider("Top N", 5, 30, 10, label_visibility="collapsed", key="top_n")

    st.divider()
    presentation = st.toggle("Presentation mode", key="presentation",
                             help="Hides the sidebar and enlarges figures for screen sharing.")
    st.button("Reset all filters", on_click=reset_filters, key="reset")

    st.divider()
    html(
        f'<div class="side-foot">Built by {OWNER}<br>'
        f'<a href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a> · '
        f'<a href="{GITHUB}" target="_blank" rel="noopener">GitHub</a></div>'
    )

if presentation:
    inject_presentation_css()
    page = st.radio("Section", PAGES, horizontal=True, index=PAGES.index(page), key="nav_top")

# ──────────────────────────────────────────────────────────────────────────────
# Derived state — recomputed on every interaction so all views stay in sync
# ──────────────────────────────────────────────────────────────────────────────
period_frame = countries_only[
    (countries_only["Year"] >= period_start) & (countries_only["Year"] <= period_end)
].copy()

snapshot = year_snapshot(period_frame, focus_year)
metrics = period_metrics(period_frame, period_start, period_end)
totals = yearly_totals(period_frame)

global_gdp = float(snapshot["GDP"].sum()) if not snapshot.empty else np.nan
economies = int(snapshot["Country Code"].nunique()) if not snapshot.empty else 0
median_gdp = float(snapshot["GDP"].median()) if not snapshot.empty else np.nan

previous_total = totals.loc[totals["Year"] == focus_year - 1, "GDP"]
previous_total = float(previous_total.iloc[0]) if len(previous_total) else np.nan
global_yoy = ((global_gdp / previous_total) - 1) * 100 if previous_total and not pd.isna(previous_total) else np.nan

conc = concentration(period_frame, focus_year)
leader = snapshot.iloc[0] if not snapshot.empty else None

period_totals_first = totals.iloc[0] if not totals.empty else None
period_totals_last = totals.iloc[-1] if not totals.empty else None
global_cagr = np.nan
if period_totals_first is not None and period_totals_last is not None:
    span = int(period_totals_last["Year"] - period_totals_first["Year"])
    if span > 0 and period_totals_first["GDP"] > 0:
        global_cagr = ((period_totals_last["GDP"] / period_totals_first["GDP"]) ** (1 / span) - 1) * 100


# ──────────────────────────────────────────────────────────────────────────────
# Hero and KPI band (shared by every page)
# ──────────────────────────────────────────────────────────────────────────────
html(
    f'<div class="hero"><div class="hero-kicker">World Bank GDP, current US dollars</div>'
    f'<h1 class="hero-title">{APP_TITLE}</h1>'
    f'<p class="hero-text">Rankings, growth, concentration and country detail for '
    f'{len(ALL_COUNTRIES)} economies between {MIN_YEAR} and {MAX_YEAR}. '
    f'Aggregate rows such as the World total and income groups are held out of every '
    f'country-level figure.</p>'
    f'<div class="hero-meta">'
    f'<span class="chip"><span class="pulse"></span>Focus year {focus_year}</span>'
    f'<span class="chip">Period {period_start}–{period_end}</span>'
    f'<span class="chip">{economies} economies reporting</span>'
    f'<span class="chip">{page}</span>'
    f'</div></div>'
)

k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1:
    kpi("🌐", "World GDP", money(global_gdp), f"Sum of {economies} reporting economies in {focus_year}",
        delta_chip(global_yoy))
with k2:
    kpi("🥇", "Largest economy",
        leader["Country Name"] if leader is not None else "—",
        f"{money(leader['GDP'])} · {pct(leader['GDP Share %'])} of world GDP" if leader is not None else "No data",
        delta_chip(leader["YoY Growth %"]) if leader is not None else "")
with k3:
    kpi("📈", "World CAGR", pct(global_cagr),
        f"Compound annual growth, {period_start}–{period_end}")
with k4:
    kpi("⚖️", "Median economy", money(median_gdp),
        f"Half of economies fall below this in {focus_year}")

st.write("")


# ──────────────────────────────────────────────────────────────────────────────
# Pages
# ──────────────────────────────────────────────────────────────────────────────
if page == "Overview":
    section("Executive overview", f"How the world economy looked in {focus_year}, measured across the {period_start}–{period_end} window.")

    if snapshot.empty:
        st.info(f"No country reported GDP in {focus_year}. Move the focus year or widen the period.")
    else:
        left, right = st.columns([1.5, 1], gap="large")

        with left:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=totals["Year"], y=totals["GDP"], mode="lines", name="World GDP",
                line=dict(color="#6ee7d7", width=2.6, shape="spline"),
                fill="tozeroy", fillcolor="rgba(110,231,215,0.13)",
                hovertemplate="%{x}<br>%{y:$,.4s}<extra></extra>",
            ))
            marker = totals[totals["Year"] == focus_year]
            if not marker.empty:
                fig.add_trace(go.Scatter(
                    x=marker["Year"], y=marker["GDP"], mode="markers", name=str(focus_year),
                    marker=dict(size=13, color="#ffc978", line=dict(color="#04090f", width=2)),
                    hovertemplate=f"{focus_year}<br>%{{y:$,.4s}}<extra></extra>",
                ))
            fig.update_layout(title="World GDP over the selected period", showlegend=False)
            fig.update_yaxes(title="GDP (current US$)", tickformat="$,.2s")
            style_fig(fig, 430)
            show(fig, "ov_trend")

        with right:
            top5 = snapshot.head(5)
            fig = go.Figure(go.Bar(
                x=top5["GDP"][::-1], y=top5["Country Name"][::-1], orientation="h",
                marker=dict(color=top5["GDP"][::-1], colorscale=SEQ_SCALE, line=dict(width=0)),
                text=[money(v, 1) for v in top5["GDP"][::-1]],
                textposition="inside", insidetextanchor="end",
                textfont=dict(color="#04141f", size=12),
                hovertemplate="%{y}<br>%{x:$,.4s}<extra></extra>",
            ))
            fig.update_layout(title=f"Five largest economies, {focus_year}", showlegend=False)
            fig.update_xaxes(tickformat="$,.2s", title="")
            style_fig(fig, 430)
            show(fig, "ov_top5")

        section("Top economies", f"Share of the {money(global_gdp)} reported for {focus_year}.")
        cards = snapshot.head(min(top_n, 10))
        biggest = float(cards["GDP"].max())
        columns = st.columns(5, gap="small")
        for position, (_, row) in enumerate(cards.iterrows()):
            with columns[position % 5]:
                width = row["GDP"] / biggest * 100 if biggest else 0
                html(
                    f'<div class="rank-card"><div class="rank-pos">#{int(row["Rank"])}</div>'
                    f'<div class="rank-name">{row["Country Name"]}</div>'
                    f'<div class="rank-figure">{money(row["GDP"])}</div>'
                    f'<div class="rank-bar"><div class="rank-fill" style="width:{width:.1f}%"></div></div>'
                    f'<div class="rank-share">{pct(row["GDP Share %"])} of world GDP · '
                    f'{pct(row["YoY Growth %"], sign=True)} year on year</div></div>'
                )
            if position % 5 == 4 and position != len(cards) - 1:
                st.write("")
                columns = st.columns(5, gap="small")

        section("Executive insights", "Generated from the current filters, not written in advance.")

        risers = snapshot.dropna(subset=["YoY Growth %"])
        col_a, col_b = st.columns(2, gap="large")

        with col_a:
            if not pd.isna(global_yoy):
                direction = "expanded" if global_yoy >= 0 else "contracted"
                insight(
                    f"<b>World output {direction} {pct(abs(global_yoy))}</b> between {focus_year - 1} and "
                    f"{focus_year}, moving from {money(previous_total)} to {money(global_gdp)}."
                )
            else:
                insight(f"<b>No comparison year.</b> {focus_year - 1} falls outside the selected period, "
                        f"so a year-on-year change cannot be calculated.")

            if conc:
                insight(
                    f"<b>Concentration is high.</b> The ten largest economies hold {pct(conc['top10'])} of "
                    f"world GDP, and just {conc['countries_to_half']} countries account for the first half "
                    f"of it.", "blue"
                )

            if not risers.empty:
                fastest = risers.nlargest(1, "YoY Growth %").iloc[0]
                insight(
                    f"<b>Largest annual increase:</b> {fastest['Country Name']}, "
                    f"{pct(fastest['YoY Growth %'], sign=True)} in {focus_year}, reaching "
                    f"{money(fastest['GDP'])}.", "violet"
                )

        with col_b:
            if not metrics.empty and metrics["CAGR %"].notna().any():
                eligible_cagr = metrics[metrics["Observations"] >= 10].dropna(subset=["CAGR %"])
                if not eligible_cagr.empty:
                    best_cagr = eligible_cagr.nlargest(1, "CAGR %").iloc[0]
                    insight(
                        f"<b>Highest CAGR:</b> {best_cagr['Country Name']} at "
                        f"{pct(best_cagr['CAGR %'])} a year across {int(best_cagr['First Year'])}–"
                        f"{int(best_cagr['Last Year'])}, from at least 10 observed years."
                    )
                top_vol = metrics[metrics["Observations"] >= 10].dropna(subset=["Volatility %"])
                if not top_vol.empty:
                    vol_row = top_vol.nlargest(1, "Volatility %").iloc[0]
                    insight(
                        f"<b>Highest growth volatility:</b> {vol_row['Country Name']}, a standard deviation of "
                        f"{num(vol_row['Volatility %'], 2)} percentage points in annual growth over the period.",
                        "violet"
                    )

            if not risers.empty:
                weakest = risers.nsmallest(1, "YoY Growth %").iloc[0]
                insight(
                    f"<b>Largest annual decrease:</b> {weakest['Country Name']}, "
                    f"{pct(weakest['YoY Growth %'], sign=True)} in {focus_year}.", "rose"
                )

            if len(snapshot) >= 2:
                first, second = snapshot.iloc[0], snapshot.iloc[1]
                gap = first["GDP"] - second["GDP"]
                ratio = first["GDP"] / second["GDP"] if second["GDP"] else np.nan
                insight(
                    f"<b>Gap at the top:</b> {first['Country Name']} leads {second['Country Name']} by "
                    f"{money(gap)}, about {num(ratio, 2)}× its size.", "blue"
                )

        section("Take the numbers with you")
        d1, d2 = st.columns(2, gap="medium")
        with d1:
            download(f"Download the {focus_year} snapshot",
                     snapshot[["Rank", "Country Name", "Country Code", "Year", "GDP", "GDP Share %", "YoY Growth %"]].round(4),
                     f"gdp_snapshot_{focus_year}.csv", "dl_ov_snap")
        with d2:
            download(f"Download period metrics ({period_start}–{period_end})",
                     metrics.round(4), f"gdp_metrics_{period_start}_{period_end}.csv", "dl_ov_metrics")


elif page == "Global Economy":
    section("Global trends", f"Aggregate output, annual change and reporting coverage across {period_start}–{period_end}.")

    if totals.empty:
        st.info("No observations fall inside the selected period.")
    else:
        scale = st.radio("GDP axis", ["Linear", "Logarithmic"], horizontal=True, key="trend_scale")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=totals["Year"], y=totals["GDP"], mode="lines", name="World GDP",
            line=dict(color="#7daeff", width=2.8, shape="spline"),
            fill="tozeroy", fillcolor="rgba(125,174,255,0.12)",
            hovertemplate="%{x}<br>%{y:$,.4s}<extra></extra>",
        ))
        fig.update_layout(title="World GDP, sum of reporting countries", showlegend=False)
        fig.update_yaxes(title="GDP (current US$)", tickformat="$,.2s",
                         type="log" if scale == "Logarithmic" else "linear")
        style_fig(fig, 440)
        show(fig, "gt_total")

        col_a, col_b = st.columns(2, gap="large")

        with col_a:
            growth = totals.dropna(subset=["YoY Growth %"])
            colors = ["#8fe3a2" if v >= 0 else "#ff9aa8" for v in growth["YoY Growth %"]]
            fig = go.Figure(go.Bar(
                x=growth["Year"], y=growth["YoY Growth %"], marker_color=colors,
                hovertemplate="%{x}<br>%{y:+.2f}%<extra></extra>",
            ))
            fig.add_hline(y=0, line_color="rgba(148,183,226,.3)")
            fig.update_layout(title="World GDP growth, year on year", showlegend=False)
            fig.update_yaxes(title="Change (%)", ticksuffix="%")
            style_fig(fig, 400)
            show(fig, "gt_growth")

        with col_b:
            fig = go.Figure(go.Scatter(
                x=totals["Year"], y=totals["Economies"], mode="lines",
                line=dict(color="#b79cff", width=2.4, shape="hv"),
                fill="tozeroy", fillcolor="rgba(183,156,255,0.10)",
                hovertemplate="%{x}<br>%{y} economies reporting<extra></extra>",
            ))
            fig.update_layout(title="Economies reporting GDP each year", showlegend=False)
            fig.update_yaxes(title="Countries")
            style_fig(fig, 400)
            show(fig, "gt_coverage")

        insight(
            "<b>Read coverage alongside the total.</b> Early years carry fewer reporting countries, so part of the "
            "rise in world GDP before the 1990s reflects wider reporting rather than real output.", "blue"
        )

        section("GDP distribution", f"How the {economies} reporting economies of {focus_year} are spread out.")
        positive = snapshot[snapshot["GDP"] > 0].copy()
        if positive.empty:
            st.info("No positive GDP values in the focus year.")
        else:
            positive["Log GDP"] = np.log10(positive["GDP"])
            col_a, col_b = st.columns(2, gap="large")
            with col_a:
                fig = go.Figure(go.Histogram(
                    x=positive["Log GDP"], nbinsx=32, marker_color="#7daeff", opacity=0.85,
                    hovertemplate="10^%{x:.1f} US$<br>%{y} economies<extra></extra>",
                ))
                fig.update_layout(title=f"Distribution of GDP in {focus_year} (log scale)", showlegend=False, bargap=0.05)
                fig.update_xaxes(title="GDP, powers of ten (US$)")
                fig.update_yaxes(title="Economies")
                style_fig(fig, 410)
                show(fig, "gt_hist")
            with col_b:
                fig = go.Figure(go.Box(
                    y=positive["Log GDP"], name=str(focus_year), boxpoints="outliers",
                    marker_color="#6ee7d7", line_color="#6ee7d7",
                    hovertemplate="10^%{y:.2f} US$<extra></extra>",
                ))
                fig.update_layout(title="Spread and outliers", showlegend=False)
                fig.update_yaxes(title="GDP, powers of ten (US$)")
                style_fig(fig, 410)
                show(fig, "gt_box")

            insight(
                f"<b>The distribution is extremely skewed.</b> The mean economy reports "
                f"{money(snapshot['GDP'].mean())} while the median reports {money(median_gdp)} — "
                f"a handful of very large economies pull the average far above the midpoint."
            )

        section("Concentration", "How much of world output sits with the largest economies.")
        if conc:
            c1, c2, c3, c4 = st.columns(4, gap="medium")
            with c1:
                kpi("⑤", "Top five", pct(conc["top5"]), f"Combined share in {focus_year}")
            with c2:
                kpi("⑩", "Top ten", pct(conc["top10"]), f"Combined share in {focus_year}")
            with c3:
                kpi("⑳", "Top twenty", pct(conc["top20"]), f"Combined share in {focus_year}")
            with c4:
                kpi("🎯", "Half of world GDP", f"{conc['countries_to_half']} countries",
                    "Economies needed to reach 50%")

            col_a, col_b = st.columns([1.35, 1], gap="large")

            with col_a:
                cumulative = conc["cumulative"]
                depth = min(60, len(cumulative))
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(1, depth + 1)), y=cumulative[:depth], mode="lines",
                    line=dict(color="#6ee7d7", width=2.8),
                    fill="tozeroy", fillcolor="rgba(110,231,215,0.10)",
                    text=conc["names"][:depth],
                    hovertemplate="Top %{x}: %{y:.1f}% of world GDP<br>%{text}<extra></extra>",
                ))
                fig.add_hline(y=50, line_dash="dot", line_color="rgba(255,201,120,.6)",
                              annotation_text="Half of world GDP", annotation_font_color="#ffc978")
                fig.update_layout(title=f"Cumulative share of world GDP, {focus_year}", showlegend=False)
                fig.update_xaxes(title="Economies, largest first")
                fig.update_yaxes(title="Cumulative share (%)", ticksuffix="%", range=[0, 102])
                style_fig(fig, 440)
                show(fig, "ge_conc")

            with col_b:
                tiers = pd.DataFrame({
                    "Group": ["Top 5", "Next 5 (6–10)", "Next 10 (11–20)", "All other economies"],
                    "Share": [
                        conc["top5"],
                        max(conc["top10"] - conc["top5"], 0),
                        max(conc["top20"] - conc["top10"], 0),
                        max(100 - conc["top20"], 0),
                    ],
                })
                fig = go.Figure(go.Pie(
                    labels=tiers["Group"], values=tiers["Share"], hole=0.58, sort=False,
                    marker=dict(colors=["#6ee7d7", "#7daeff", "#b79cff", "rgba(148,183,226,.22)"],
                                line=dict(color="rgba(4,9,15,.6)", width=1.5)),
                    textinfo="percent", textfont=dict(family="Inter", size=12, color="#04141f"),
                    hovertemplate="%{label}: %{value:.2f}% of world GDP<extra></extra>",
                ))
                fig.update_layout(
                    title=f"Where world GDP sits, {focus_year}",
                    annotations=[dict(text=f"{focus_year}", x=0.5, y=0.5, showarrow=False,
                                      font=dict(family="Sora", size=18, color="#eef4fb"))],
                )
                style_fig(fig, 440)
                show(fig, "ge_donut")

            insight(
                f"<b>Herfindahl–Hirschman index: {num(conc['hhi'], 0)}.</b> Calculated on GDP shares in "
                f"percentage points, where 10,000 would mean a single economy produces everything. "
                f"The Gini coefficient across economies is {num(conc['gini'], 3)}.", "violet"
            )

        section("Top economies and GDP share",
                f"The largest {min(top_n, len(snapshot))} economies of {focus_year}, sized by the sidebar's leaderboard control.")
        leaders = snapshot.head(top_n).copy()
        col_a, col_b = st.columns([1.2, 1], gap="large")

        with col_a:
            drawn = leaders.iloc[::-1]
            fig = go.Figure(go.Bar(
                x=drawn["GDP"], y=drawn["Country Name"], orientation="h",
                marker=dict(color=drawn["GDP"], colorscale=SEQ_SCALE, line=dict(width=0)),
                customdata=drawn["GDP Share %"],
                hovertemplate="%{y}<br>%{x:$,.4s}<br>%{customdata:.2f}% of world GDP<extra></extra>",
            ))
            fig.update_layout(title=f"Largest economies, {focus_year}", showlegend=False)
            fig.update_xaxes(title="GDP (current US$)", tickformat="$,.2s")
            style_fig(fig, max(430, len(leaders) * 30))
            show(fig, "ge_top")

        with col_b:
            share_history = period_frame[period_frame["Country Name"].isin(leaders.head(6)["Country Name"])]
            share_history = share_history.dropna(subset=["GDP"]).merge(
                totals[["Year", "GDP"]].rename(columns={"GDP": "World"}), on="Year", how="left")
            if share_history.empty:
                st.info("No share history available for these economies in this period.")
            else:
                share_history["Share %"] = share_history["GDP"] / share_history["World"] * 100
                fig = px.line(share_history.sort_values("Year"), x="Year", y="Share %",
                              color="Country Name", color_discrete_sequence=PALETTE)
                fig.update_traces(line=dict(width=2.4, shape="spline"),
                                  hovertemplate="%{fullData.name}<br>%{x}: %{y:.2f}%<extra></extra>")
                fig.update_layout(title="Share of world GDP over the period")
                fig.update_yaxes(title="Share (%)", ticksuffix="%")
                style_fig(fig, max(430, len(leaders) * 30))
                show(fig, "ge_share")


elif page == "Growth Analysis":
    section("Growth analysis", f"Compound growth, average annual change and volatility measured over {period_start}–{period_end}.")

    eligible = metrics[metrics["Observations"] >= 2].copy()

    if eligible.empty:
        st.info("The selected period holds fewer than two observed years, so growth cannot be measured. "
                "Widen the period in the sidebar.")
    else:
        min_obs = st.slider(
            "Minimum years of data required",
            2, max(2, int(eligible["Observations"].max())),
            min(10, int(eligible["Observations"].max())),
            key="growth_minobs",
            help="Filters out economies with thin series, which otherwise dominate growth leaderboards.",
        )
        eligible = metrics[metrics["Observations"] >= min_obs].copy()
        st.caption(f"{len(eligible)} economies meet the threshold of {min_obs} observed years.")

        if eligible.empty:
            st.info("No economy meets that threshold. Lower it or widen the period.")
        else:
            col_a, col_b = st.columns(2, gap="large")

            with col_a:
                best = eligible.dropna(subset=["CAGR %"]).nlargest(top_n, "CAGR %").sort_values("CAGR %")
                fig = go.Figure(go.Bar(
                    x=best["CAGR %"], y=best["Country Name"], orientation="h",
                    marker=dict(color=best["CAGR %"], colorscale=SEQ_SCALE, line=dict(width=0)),
                    hovertemplate="%{y}<br>CAGR %{x:.2f}%<extra></extra>",
                ))
                fig.update_layout(title=f"Fastest compound growth, top {len(best)}", showlegend=False)
                fig.update_xaxes(title="CAGR (%)", ticksuffix="%")
                style_fig(fig, max(420, len(best) * 30))
                show(fig, "ga_cagr")

            with col_b:
                volatile = eligible.dropna(subset=["Volatility %"]).nlargest(top_n, "Volatility %").sort_values("Volatility %")
                fig = go.Figure(go.Bar(
                    x=volatile["Volatility %"], y=volatile["Country Name"], orientation="h",
                    marker=dict(color="#f7a3c4", line=dict(width=0)),
                    hovertemplate="%{y}<br>Volatility %{x:.2f} pp<extra></extra>",
                ))
                fig.update_layout(title=f"Most volatile growth, top {len(volatile)}", showlegend=False)
                fig.update_xaxes(title="Standard deviation of annual growth (pp)")
                style_fig(fig, max(420, len(volatile) * 30))
                show(fig, "ga_vol")

            section("Growth against volatility", "Every dot is an economy. Up is faster growth, right is a bumpier ride.")
            scatter = eligible.dropna(subset=["CAGR %", "Volatility %", "Last GDP"]).copy()
            if not scatter.empty:
                scatter["Size"] = np.log10(scatter["Last GDP"].clip(lower=1))
                fig = go.Figure(go.Scatter(
                    x=scatter["Volatility %"], y=scatter["CAGR %"], mode="markers",
                    marker=dict(
                        size=scatter["Size"], sizemode="area",
                        sizeref=2.0 * scatter["Size"].max() / (34 ** 2), sizemin=4,
                        color=scatter["Average Growth %"], colorscale=SEQ_SCALE,
                        showscale=True, colorbar=dict(title="Avg<br>growth %", thickness=12),
                        line=dict(color="rgba(255,255,255,.25)", width=0.6),
                    ),
                    text=scatter["Country Name"],
                    customdata=np.stack([scatter["Last GDP"], scatter["Observations"]], axis=-1),
                    hovertemplate=("<b>%{text}</b><br>CAGR %{y:.2f}%<br>Volatility %{x:.2f} pp"
                                   "<br>Latest GDP %{customdata[0]:$,.4s}"
                                   "<br>%{customdata[1]} years observed<extra></extra>"),
                ))
                median_vol = scatter["Volatility %"].median()
                median_cagr = scatter["CAGR %"].median()
                fig.add_vline(x=median_vol, line_dash="dot", line_color="rgba(148,183,226,.3)")
                fig.add_hline(y=median_cagr, line_dash="dot", line_color="rgba(148,183,226,.3)")
                fig.update_layout(title="Return and turbulence", showlegend=False)
                fig.update_xaxes(title="Volatility of annual growth (pp)")
                fig.update_yaxes(title="CAGR (%)", ticksuffix="%")
                style_fig(fig, 520)
                show(fig, "ga_scatter")

                quadrant = scatter[(scatter["CAGR %"] > median_cagr) & (scatter["Volatility %"] < median_vol)]
                if not quadrant.empty:
                    names = ", ".join(quadrant.nlargest(4, "CAGR %")["Country Name"])
                    insight(
                        f"<b>Above-median CAGR with below-median volatility:</b> {len(quadrant)} economies fall in "
                        f"this quadrant, the four highest by CAGR being {names}. Medians for this selection are "
                        f"{pct(median_cagr)} CAGR and {num(median_vol, 2)} pp volatility.", "blue"
                    )

            section("Growth heatmap", "Annual change for the countries selected in the sidebar.")
            heat_countries = compare_countries or snapshot.head(8)["Country Name"].tolist()
            heat_source = period_frame[period_frame["Country Name"].isin(heat_countries)]
            heat = heat_source.pivot_table(index="Country Name", columns="Year",
                                           values="YoY Growth %", aggfunc="mean")
            if heat.empty:
                st.info("Pick at least one country in the sidebar to build the heatmap.")
            else:
                window = min(25, period_end - period_start + 1)
                keep = [y for y in sorted(heat.columns) if y > period_end - window]
                heat = heat.reindex(columns=keep)
                heat = heat.reindex(index=[c for c in heat_countries if c in heat.index])
                limit = float(np.nanpercentile(np.abs(heat.to_numpy()), 95)) if heat.notna().any().any() else 10
                limit = max(limit, 1.0)
                fig = go.Figure(go.Heatmap(
                    z=heat.to_numpy(), x=[str(y) for y in heat.columns], y=heat.index.tolist(),
                    colorscale=DIVERGING, zmid=0, zmin=-limit, zmax=limit,
                    colorbar=dict(title="YoY %", thickness=12),
                    hovertemplate="%{y} · %{x}<br>%{z:+.2f}%<extra></extra>",
                    hoverongaps=False, xgap=1, ygap=1,
                ))
                fig.update_layout(title=f"Year-on-year growth, last {len(keep)} years of the period")
                style_fig(fig, max(360, len(heat.index) * 46 + 140), legend_top=False)
                show(fig, "ga_heat")

            section("Growth table")
            table = eligible[[
                "Country Name", "Country Code", "First Year", "Last Year", "Observations",
                "CAGR %", "Average Growth %", "Volatility %", "Total Growth %", "Last GDP",
            ]].sort_values("CAGR %", ascending=False)
            st.dataframe(
                table.round(2), use_container_width=True, hide_index=True, height=420,
                column_config={
                    "Last GDP": st.column_config.NumberColumn("Last GDP", format="$%.0f"),
                    "CAGR %": st.column_config.NumberColumn("CAGR %", format="%.2f%%"),
                    "Average Growth %": st.column_config.NumberColumn("Avg growth %", format="%.2f%%"),
                    "Volatility %": st.column_config.NumberColumn("Volatility (pp)", format="%.2f"),
                    "Total Growth %": st.column_config.NumberColumn("Total growth %", format="%.1f%%"),
                },
            )
            download("Download the growth table", table.round(4),
                     f"gdp_growth_{period_start}_{period_end}.csv", "dl_growth")


elif page == "World Map":
    section("World map", f"Geographic view for {focus_year}. Aggregate rows are excluded, so every shaded country is an individual economy.")

    metric_choice = st.radio(
        "Metric",
        ["GDP", "YoY Growth %", "GDP Share %", "CAGR %"],
        horizontal=True,
        key="map_metric",
    )

    map_base = snapshot.merge(
        metrics[["Country Code", "CAGR %", "Average Growth %", "Volatility %"]],
        on="Country Code", how="left",
    )
    mappable_codes = set(period_frame.loc[period_frame["Year"] == focus_year, "Country Code"])
    map_base = map_base[map_base["Country Code"].isin(mappable_codes)]
    map_df = map_base[~map_base["Country Code"].isin(NO_MAP_GEOMETRY)].dropna(subset=[metric_choice]).copy()

    # Hover values are pre-formatted strings so a missing metric reads "N/A"
    # instead of rendering as NaN inside the tooltip.
    for frame_ref in (map_base, map_df):
        frame_ref["GDP text"] = frame_ref["GDP"].apply(lambda v: money(v, dash="N/A"))
        frame_ref["Share text"] = frame_ref["GDP Share %"].apply(lambda v: pct(v, dash="N/A"))
        frame_ref["Growth text"] = frame_ref["YoY Growth %"].apply(lambda v: pct(v, sign=True, dash="N/A"))
        frame_ref["CAGR text"] = frame_ref["CAGR %"].apply(lambda v: pct(v, dash="N/A"))
        frame_ref["Rank text"] = frame_ref["Rank"].apply(lambda v: f"#{int(v)}" if pd.notna(v) else "N/A")

    if map_df.empty:
        st.info(f"No country has a value for {metric_choice} in {focus_year}.")
    else:
        if metric_choice == "GDP":
            map_df["Shaded"] = np.log10(map_df["GDP"].clip(lower=1))
            scale, midpoint, bar_title = SEQ_SCALE, None, "GDP<br>(log₁₀ US$)"
        elif metric_choice == "GDP Share %":
            map_df["Shaded"] = np.log10(map_df["GDP Share %"].clip(lower=1e-4))
            scale, midpoint, bar_title = SEQ_SCALE, None, "Share<br>(log₁₀ %)"
        else:
            map_df["Shaded"] = map_df[metric_choice]
            bound = float(np.nanpercentile(np.abs(map_df["Shaded"]), 95)) or 10.0
            scale, midpoint, bar_title = DIVERGING, 0, f"{metric_choice}"

        fig = go.Figure(go.Choropleth(
            locations=map_df["Country Code"],
            z=map_df["Shaded"],
            text=map_df["Country Name"],
            customdata=np.stack([
                map_df["GDP text"], map_df["Share text"],
                map_df["Growth text"], map_df["CAGR text"], map_df["Rank text"],
            ], axis=-1),
            colorscale=scale,
            zmid=midpoint,
            zmin=-bound if midpoint == 0 else None,
            zmax=bound if midpoint == 0 else None,
            marker_line_color="rgba(4,9,15,.55)",
            marker_line_width=0.4,
            colorbar=dict(title=bar_title, thickness=13, len=0.72, outlinewidth=0),
            hovertemplate=(
                "<b>%{text}</b><br>Year " + str(focus_year)
                + "<br>World rank %{customdata[4]}"
                "<br>GDP %{customdata[0]}"
                "<br>GDP share %{customdata[1]}"
                "<br>YoY growth %{customdata[2]}"
                "<br>CAGR %{customdata[3]}<extra></extra>"
            ),
        ))
        fig.update_geos(
            projection_type="natural earth", bgcolor="rgba(0,0,0,0)",
            showframe=False, showcoastlines=True, coastlinecolor="rgba(148,183,226,.18)",
            showland=True, landcolor="rgba(148,183,226,.05)",
            showocean=True, oceancolor="rgba(4,9,15,0)",
            lataxis_range=[-58, 85],
        )
        fig.update_layout(
            title=f"{metric_choice} by country, {focus_year}",
            height=620 if not presentation else 720,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#c9dbef"),
            margin=dict(l=0, r=0, t=56, b=0),
            hoverlabel=dict(bgcolor="#0b1a2c", bordercolor="rgba(148,183,226,.3)", font_color="#fff"),
            title_font=dict(family="Sora, sans-serif", size=16, color="#fff"),
        )
        show(fig, "map_main")

        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            best = map_df.nlargest(1, metric_choice).iloc[0]
            kpi("🔺", f"Highest {metric_choice}", best["Country Name"],
                money(best[metric_choice]) if metric_choice == "GDP" else pct(best[metric_choice]))
        with c2:
            worst = map_df.nsmallest(1, metric_choice).iloc[0]
            kpi("🔻", f"Lowest {metric_choice}", worst["Country Name"],
                money(worst[metric_choice]) if metric_choice == "GDP" else pct(worst[metric_choice]))
        with c3:
            kpi("🗺️", "Countries shaded", num(len(map_df)),
                f"{len(map_base) - len(map_df)} reporting economies could not be drawn")

        skipped = sorted(set(map_base["Country Name"]) - set(map_df["Country Name"]))
        if skipped:
            preview = ", ".join(skipped[:8]) + ("…" if len(skipped) > 8 else "")
            insight(
                f"<b>Not every economy can be drawn.</b> {len(skipped)} reporting economies are missing from the "
                f"map because they have no standard map geometry or no value for this metric: {preview}", "blue"
            )

        download(f"Download map data ({metric_choice}, {focus_year})",
                 map_base[["Rank", "Country Name", "Country Code", "GDP", "GDP Share %",
                           "YoY Growth %", "CAGR %"]].round(4),
                 f"gdp_map_{focus_year}.csv", "dl_map")


elif page == "Country Profiles":
    section("Country profile", "Everything the dataset holds about one economy, inside the selected period.")

    default_country = compare_countries[0] if compare_countries else (
        snapshot.iloc[0]["Country Name"] if not snapshot.empty else ALL_COUNTRIES[0]
    )
    profile_country = st.selectbox(
        "Country",
        ALL_COUNTRIES,
        index=ALL_COUNTRIES.index(default_country) if default_country in ALL_COUNTRIES else 0,
        key="profile_country",
    )

    series = period_frame[period_frame["Country Name"] == profile_country].dropna(subset=["GDP"]).sort_values("Year")
    row = metrics[metrics["Country Name"] == profile_country]

    if series.empty:
        st.info(f"{profile_country} reported no GDP between {period_start} and {period_end}.")
    else:
        row = row.iloc[0]
        focus_row = snapshot[snapshot["Country Name"] == profile_country]
        has_focus = not focus_row.empty
        focus_row = focus_row.iloc[0] if has_focus else None

        k1, k2, k3, k4 = st.columns(4, gap="medium")
        with k1:
            kpi("💵", f"GDP in {focus_year}",
                money(focus_row["GDP"]) if has_focus else "Not reported",
                f"Latest in period: {money(row['Last GDP'])} ({int(row['Last Year'])})",
                delta_chip(focus_row["YoY Growth %"]) if has_focus else "")
        with k2:
            kpi("🏅", f"World rank in {focus_year}",
                f"#{int(focus_row['Rank'])}" if has_focus else "—",
                f"Out of {economies} reporting economies")
        with k3:
            kpi("🌍", "Share of world GDP",
                pct(focus_row["GDP Share %"]) if has_focus else "—",
                f"In {focus_year}")
        with k4:
            kpi("📈", "CAGR", pct(row["CAGR %"]),
                f"{int(row['First Year'])}–{int(row['Last Year'])}, {int(row['Observations'])} years observed")

        k5, k6, k7, k8 = st.columns(4, gap="medium")
        with k5:
            kpi("📊", "Average annual growth", pct(row["Average Growth %"]), "Mean of yearly changes in period")
        with k6:
            kpi("🌡️", "Volatility", num(row["Volatility %"], 2) + " pp",
                "Standard deviation of annual growth")
        with k7:
            kpi("🏔️", "Peak GDP", money(row["Peak GDP"]), f"Reached in {int(row['Peak Year'])}")
        with k8:
            kpi("🚀", "Growth across period", pct(row["Total Growth %"]),
                f"{money(row['First GDP'])} → {money(row['Last GDP'])}")

        expected_years = int(row["Last Year"] - row["First Year"] + 1)
        missing_years = max(expected_years - int(row["Observations"]), 0)
        facts([
            ("Country code", str(series.iloc[0]["Country Code"])),
            ("First year with data", str(int(row["First Year"]))),
            ("Latest year with data", str(int(row["Last Year"]))),
            ("Observations in period", str(int(row["Observations"]))),
            ("Missing years inside range", str(missing_years)),
            ("Period applied", f"{period_start}–{period_end}"),
        ])

        col_a, col_b = st.columns([1.45, 1], gap="large")

        with col_a:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=series["Year"], y=series["GDP"], mode="lines",
                line=dict(color="#7daeff", width=2.8, shape="spline"),
                fill="tozeroy", fillcolor="rgba(125,174,255,0.13)", name="GDP",
                hovertemplate="%{x}<br>%{y:$,.4s}<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=[row["Peak Year"]], y=[row["Peak GDP"]], mode="markers+text",
                marker=dict(size=12, color="#ffc978", line=dict(color="#04090f", width=2)),
                text=["peak"], textposition="top center", textfont=dict(color="#ffc978", size=11),
                name="Peak", hovertemplate=f"Peak {int(row['Peak Year'])}<br>%{{y:$,.4s}}<extra></extra>",
            ))
            fig.update_layout(title=f"{profile_country} — GDP history", showlegend=False)
            fig.update_yaxes(title="GDP (current US$)", tickformat="$,.2s")
            style_fig(fig, 430)
            show(fig, "cp_gdp")

        with col_b:
            growth_series = series.dropna(subset=["YoY Growth %"])
            if growth_series.empty:
                st.info("Not enough consecutive years to chart annual growth.")
            else:
                colors = ["#8fe3a2" if v >= 0 else "#ff9aa8" for v in growth_series["YoY Growth %"]]
                fig = go.Figure(go.Bar(
                    x=growth_series["Year"], y=growth_series["YoY Growth %"], marker_color=colors,
                    hovertemplate="%{x}<br>%{y:+.2f}%<extra></extra>",
                ))
                fig.add_hline(y=row["Average Growth %"], line_dash="dot", line_color="#6ee7d7",
                              annotation_text="period average", annotation_font_color="#6ee7d7")
                fig.update_layout(title="Annual growth", showlegend=False)
                fig.update_yaxes(title="Change (%)", ticksuffix="%")
                style_fig(fig, 430)
                show(fig, "cp_growth")

        share_series = period_frame.dropna(subset=["GDP"]).groupby("Year", as_index=False)["GDP"].sum()
        share_series = share_series.rename(columns={"GDP": "World"}).merge(
            series[["Year", "GDP"]], on="Year", how="inner")
        if not share_series.empty:
            share_series["Share %"] = share_series["GDP"] / share_series["World"] * 100
            fig = go.Figure(go.Scatter(
                x=share_series["Year"], y=share_series["Share %"], mode="lines",
                line=dict(color="#b79cff", width=2.6, shape="spline"),
                fill="tozeroy", fillcolor="rgba(183,156,255,0.10)",
                hovertemplate="%{x}<br>%{y:.2f}% of world GDP<extra></extra>",
            ))
            fig.update_layout(title=f"{profile_country}'s share of world GDP", showlegend=False)
            fig.update_yaxes(title="Share (%)", ticksuffix="%")
            style_fig(fig, 380)
            show(fig, "cp_share")

        best_year = series.dropna(subset=["YoY Growth %"]).nlargest(1, "YoY Growth %")
        worst_year = series.dropna(subset=["YoY Growth %"]).nsmallest(1, "YoY Growth %")
        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            if not best_year.empty:
                b = best_year.iloc[0]
                insight(f"<b>Largest annual increase:</b> {int(b['Year'])}, "
                        f"{pct(b['YoY Growth %'], sign=True)} to {money(b['GDP'])}.")
            if int(row["Peak Year"]) != int(row["Last Year"]):
                drop = (row["Last GDP"] / row["Peak GDP"] - 1) * 100
                insight(f"<b>Below the period peak.</b> Output in {int(row['Last Year'])} sits {pct(abs(drop))} under the "
                        f"{int(row['Peak Year'])} high of {money(row['Peak GDP'])}.", "rose")
        with col_b:
            if not worst_year.empty:
                w = worst_year.iloc[0]
                insight(f"<b>Largest annual decrease:</b> {int(w['Year'])}, "
                        f"{pct(w['YoY Growth %'], sign=True)} to {money(w['GDP'])}.", "rose")
            gaps = int(row["Last Year"] - row["First Year"] + 1 - row["Observations"])
            if gaps > 0:
                insight(f"<b>{gaps} missing years</b> sit inside {profile_country}'s series. Growth is left blank "
                        f"across those breaks rather than bridged.", "blue")

        download(f"Download {profile_country} series",
                 series[["Country Name", "Country Code", "Year", "GDP", "YoY Growth %"]].round(4),
                 f"gdp_{profile_country.lower().replace(' ', '_')}.csv", "dl_profile")


elif page == "Country Comparison":
    section("Compare countries", "Side by side across the selected period. Choose the countries in the sidebar.")

    comparison = period_frame[period_frame["Country Name"].isin(compare_countries)].dropna(subset=["GDP"])

    if not compare_countries:
        st.info("No countries selected. Pick up to ten in the sidebar to build the comparison.")
    elif comparison.empty:
        st.info(f"None of the selected countries reported GDP between {period_start} and {period_end}. "
                "Widen the period or choose other countries.")
    else:
        view = st.radio("View", ["Absolute GDP", "Indexed to period start", "Share of world GDP"],
                        horizontal=True, key="cmp_view")

        if view == "Absolute GDP":
            fig = px.line(comparison.sort_values("Year"), x="Year", y="GDP", color="Country Name",
                          color_discrete_sequence=PALETTE)
            fig.update_traces(line=dict(width=2.6, shape="spline"),
                              hovertemplate="%{fullData.name}<br>%{x}: %{y:$,.4s}<extra></extra>")
            fig.update_layout(title="GDP over time")
            fig.update_yaxes(title="GDP (current US$)", tickformat="$,.2s")
        elif view == "Indexed to period start":
            indexed = comparison.sort_values("Year").copy()
            base = indexed.groupby("Country Name")["GDP"].transform("first")
            indexed["Index"] = indexed["GDP"] / base * 100
            fig = px.line(indexed, x="Year", y="Index", color="Country Name",
                          color_discrete_sequence=PALETTE)
            fig.update_traces(line=dict(width=2.6, shape="spline"),
                              hovertemplate="%{fullData.name}<br>%{x}: %{y:,.0f}<extra></extra>")
            fig.add_hline(y=100, line_dash="dot", line_color="rgba(148,183,226,.3)")
            fig.update_layout(title="Growth from each country's first year in the period (start = 100)")
            fig.update_yaxes(title="Index", type="log")
        else:
            world = period_frame.dropna(subset=["GDP"]).groupby("Year", as_index=False)["GDP"].sum()
            world = world.rename(columns={"GDP": "World"})
            shares = comparison.merge(world, on="Year", how="left")
            shares["Share %"] = shares["GDP"] / shares["World"] * 100
            fig = px.area(shares.sort_values("Year"), x="Year", y="Share %", color="Country Name",
                          color_discrete_sequence=PALETTE)
            fig.update_traces(hovertemplate="%{fullData.name}<br>%{x}: %{y:.2f}%<extra></extra>")
            fig.update_layout(title="Combined share of world GDP")
            fig.update_yaxes(title="Share (%)", ticksuffix="%")

        style_fig(fig, 500)
        show(fig, "cmp_main")

        growth_frame = comparison.dropna(subset=["YoY Growth %"]).sort_values("Year")
        if not growth_frame.empty:
            fig = px.line(growth_frame, x="Year", y="YoY Growth %", color="Country Name",
                          color_discrete_sequence=PALETTE)
            fig.update_traces(line=dict(width=2.2), hovertemplate="%{fullData.name}<br>%{x}: %{y:+.2f}%<extra></extra>")
            fig.add_hline(y=0, line_color="rgba(148,183,226,.3)")
            fig.update_layout(title="Annual growth")
            fig.update_yaxes(title="Change (%)", ticksuffix="%")
            style_fig(fig, 420)
            show(fig, "cmp_growth")

        section("Comparison table", f"Period metrics for {period_start}–{period_end}, with the {focus_year} snapshot.")
        table = metrics[metrics["Country Name"].isin(compare_countries)].copy()
        focus_bits = snapshot[["Country Code", "Rank", "GDP", "GDP Share %", "YoY Growth %"]].rename(
            columns={"GDP": f"GDP {focus_year}", "Rank": f"Rank {focus_year}",
                     "GDP Share %": f"Share {focus_year} %", "YoY Growth %": f"Growth {focus_year} %"}
        )
        table = table.merge(focus_bits, on="Country Code", how="left").sort_values(
            f"GDP {focus_year}", ascending=False, na_position="last")
        columns = ["Country Name", f"Rank {focus_year}", f"GDP {focus_year}", f"Share {focus_year} %",
                   f"Growth {focus_year} %", "CAGR %", "Average Growth %", "Volatility %",
                   "Total Growth %", "Peak GDP", "Peak Year"]
        st.dataframe(
            table[columns].round(2), use_container_width=True, hide_index=True,
            column_config={
                f"GDP {focus_year}": st.column_config.NumberColumn(format="$%.0f"),
                "Peak GDP": st.column_config.NumberColumn(format="$%.0f"),
                "Peak Year": st.column_config.NumberColumn(format="%d"),
                f"Rank {focus_year}": st.column_config.NumberColumn(format="%d"),
            },
        )

        radar = table.dropna(subset=["CAGR %", "Average Growth %", "Volatility %"])
        if len(radar) >= 2:
            axes = {"CAGR %": "Compound growth", "Average Growth %": "Average growth",
                    f"Share {focus_year} %": "World share", "Total Growth %": "Period growth"}
            available = [c for c in axes if c in radar.columns and radar[c].notna().any()]
            fig = go.Figure()
            for position, (_, entry) in enumerate(radar.iterrows()):
                values = []
                for column in available:
                    column_values = radar[column]
                    low, high = column_values.min(), column_values.max()
                    spread = high - low
                    values.append(50.0 if spread == 0 or pd.isna(entry[column])
                                  else float((entry[column] - low) / spread * 100))
                fig.add_trace(go.Scatterpolar(
                    r=values + values[:1], theta=[axes[c] for c in available] + [axes[available[0]]],
                    fill="toself", name=entry["Country Name"],
                    line=dict(color=PALETTE[position % len(PALETTE)], width=2),
                    opacity=0.65, hovertemplate="%{theta}: %{r:.0f} of 100<extra>%{fullData.name}</extra>",
                ))
            fig.update_layout(
                title="Relative position within the selected group (100 = highest value in group)",
                polar=dict(
                    bgcolor="rgba(148,183,226,.04)",
                    radialaxis=dict(range=[0, 100], gridcolor="rgba(148,183,226,.12)", tickfont=dict(size=10)),
                    angularaxis=dict(gridcolor="rgba(148,183,226,.12)"),
                ),
            )
            style_fig(fig, 520)
            show(fig, "cmp_radar")

        download("Download the comparison", table[columns].round(4),
                 f"gdp_comparison_{period_start}_{period_end}.csv", "dl_compare")


elif page == "Head to Head":
    section("Head to head", "Two economies, the same metrics, one winner per row.")

    pick_a = compare_countries[0] if compare_countries else ("United States" if "United States" in ALL_COUNTRIES else ALL_COUNTRIES[0])
    pick_b = compare_countries[1] if len(compare_countries) > 1 else ("China" if "China" in ALL_COUNTRIES else ALL_COUNTRIES[min(1, len(ALL_COUNTRIES) - 1)])

    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        country_a = st.selectbox("First economy", ALL_COUNTRIES,
                                 index=ALL_COUNTRIES.index(pick_a), key="battle_a")
    with col_b:
        country_b = st.selectbox("Second economy", ALL_COUNTRIES,
                                 index=ALL_COUNTRIES.index(pick_b), key="battle_b")

    if country_a == country_b:
        st.info("Pick two different economies to compare.")
    else:
        def side(name: str) -> dict | None:
            row = metrics[metrics["Country Name"] == name]
            if row.empty:
                return None
            row = row.iloc[0]
            focus = snapshot[snapshot["Country Name"] == name]
            focus = focus.iloc[0] if not focus.empty else None
            return {
                f"GDP in {focus_year}": focus["GDP"] if focus is not None else np.nan,
                f"World rank in {focus_year}": focus["Rank"] if focus is not None else np.nan,
                f"Share of world GDP in {focus_year} (%)": focus["GDP Share %"] if focus is not None else np.nan,
                f"Growth in {focus_year} (%)": focus["YoY Growth %"] if focus is not None else np.nan,
                "CAGR over period (%)": row["CAGR %"],
                "Average annual growth (%)": row["Average Growth %"],
                "Growth volatility (pp)": row["Volatility %"],
                "Total growth over period (%)": row["Total Growth %"],
                "Peak GDP": row["Peak GDP"],
                "Years observed": row["Observations"],
            }

        side_a, side_b = side(country_a), side(country_b)

        if side_a is None or side_b is None:
            st.info("One of these economies has no data inside the selected period.")
        else:
            # Lower is better for rank and volatility; higher is better elsewhere.
            lower_is_better = {f"World rank in {focus_year}", "Growth volatility (pp)"}
            wins_a = sum(
                1 for key in side_a
                if pd.notna(side_a[key]) and pd.notna(side_b[key]) and key != "Years observed"
                and ((side_a[key] < side_b[key]) if key in lower_is_better else (side_a[key] > side_b[key]))
            )
            wins_b = sum(
                1 for key in side_a
                if pd.notna(side_a[key]) and pd.notna(side_b[key]) and key != "Years observed"
                and ((side_b[key] < side_a[key]) if key in lower_is_better else (side_b[key] > side_a[key]))
            )

            score_a, score_b, spacer = st.columns([1, 1, 1.1], gap="medium")
            with score_a:
                html(f'<div class="vs-card"><div class="vs-name">{country_a}</div>'
                     f'<div class="vs-score {"win" if wins_a >= wins_b else "lose"}">{wins_a}</div>'
                     f'<div class="vs-note">metrics led</div></div>')
            with score_b:
                html(f'<div class="vs-card"><div class="vs-name">{country_b}</div>'
                     f'<div class="vs-score {"win" if wins_b >= wins_a else "lose"}">{wins_b}</div>'
                     f'<div class="vs-note">metrics led</div></div>')
            with spacer:
                gdp_a = side_a[f"GDP in {focus_year}"]
                gdp_b = side_b[f"GDP in {focus_year}"]
                gap_now = gdp_a - gdp_b if pd.notna(gdp_a) and pd.notna(gdp_b) else np.nan
                ahead = country_a if pd.notna(gap_now) and gap_now > 0 else country_b
                kpi("📐", f"GDP gap in {focus_year}", money(abs(gap_now)) if pd.notna(gap_now) else "—",
                    f"{ahead} is ahead" if pd.notna(gap_now) else "Not comparable this year")

            def fmt(key: str, value) -> str:
                if pd.isna(value):
                    return "—"
                if "GDP" in key and "%" not in key and "rank" not in key.lower():
                    return money(value)
                if "rank" in key.lower():
                    return f"#{int(value)}"
                if "Years" in key:
                    return f"{int(value)}"
                if "(pp)" in key:
                    return f"{value:,.2f} pp"
                return pct(value)

            rows = []
            for key in side_a:
                lead = ""
                if pd.notna(side_a[key]) and pd.notna(side_b[key]) and key != "Years observed":
                    better_a = (side_a[key] < side_b[key]) if key in lower_is_better else (side_a[key] > side_b[key])
                    lead = country_a if better_a else (country_b if side_a[key] != side_b[key] else "Tied")
                rows.append({"Metric": key, country_a: fmt(key, side_a[key]),
                             country_b: fmt(key, side_b[key]), "Ahead": lead})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            duel = period_frame[period_frame["Country Name"].isin([country_a, country_b])].dropna(subset=["GDP"])
            col_a, col_b = st.columns(2, gap="large")
            with col_a:
                fig = px.line(duel.sort_values("Year"), x="Year", y="GDP", color="Country Name",
                              color_discrete_sequence=["#6ee7d7", "#f7a3c4"])
                fig.update_traces(line=dict(width=3, shape="spline"),
                                  hovertemplate="%{fullData.name}<br>%{x}: %{y:$,.4s}<extra></extra>")
                fig.update_layout(title="GDP")
                fig.update_yaxes(title="GDP (current US$)", tickformat="$,.2s")
                style_fig(fig, 420)
                show(fig, "hh_gdp")
            with col_b:
                ratio = duel.pivot_table(index="Year", columns="Country Name", values="GDP")
                if {country_a, country_b}.issubset(ratio.columns):
                    ratio = ratio.dropna()
                    ratio["Ratio"] = ratio[country_a] / ratio[country_b]
                    fig = go.Figure(go.Scatter(
                        x=ratio.index, y=ratio["Ratio"], mode="lines",
                        line=dict(color="#ffc978", width=2.8, shape="spline"),
                        hovertemplate="%{x}<br>%{y:.2f}×<extra></extra>",
                    ))
                    fig.add_hline(y=1, line_dash="dot", line_color="rgba(148,183,226,.4)",
                                  annotation_text="parity", annotation_font_color="#93a9c4")
                    fig.update_layout(title=f"{country_a} GDP ÷ {country_b} GDP", showlegend=False)
                    fig.update_yaxes(title="Ratio", ticksuffix="×")
                    style_fig(fig, 420)
                    show(fig, "hh_ratio")
                else:
                    st.info("These two economies have no overlapping years in this period.")

            download("Download the head to head", pd.DataFrame(rows),
                     f"gdp_{country_a[:12]}_vs_{country_b[:12]}.csv".lower().replace(" ", "_"), "dl_battle")


elif page == "Rankings":
    section("Rankings", f"Every ranking below covers {focus_year} or the {period_start}–{period_end} period, countries only.")

    metric_label = st.selectbox(
        "Rank by",
        [f"GDP in {focus_year}", f"Share of world GDP in {focus_year}", f"Growth in {focus_year}",
         "CAGR over period", "Average annual growth", "Growth volatility"],
        key="rank_metric",
    )
    order = st.radio("Order", ["Highest first", "Lowest first"], horizontal=True, key="rank_order")

    column_for = {
        f"GDP in {focus_year}": ("GDP", snapshot, "$"),
        f"Share of world GDP in {focus_year}": ("GDP Share %", snapshot, "%"),
        f"Growth in {focus_year}": ("YoY Growth %", snapshot, "%"),
        "CAGR over period": ("CAGR %", metrics, "%"),
        "Average annual growth": ("Average Growth %", metrics, "%"),
        "Growth volatility": ("Volatility %", metrics, "pp"),
    }
    column, source, unit = column_for[metric_label]

    board = source.dropna(subset=[column]).copy()
    if column in {"CAGR %", "Average Growth %", "Volatility %"}:
        min_years = st.slider("Minimum years of data", 2, 30, 10, key="rank_minyears")
        board = board[board["Observations"] >= min_years]
        if "GDP" not in board.columns:
            board = board.merge(snapshot[["Country Code", "GDP", "GDP Share %"]], on="Country Code", how="left")

    if board.empty:
        st.info("No economy matches these settings. Relax the filters or widen the period.")
    else:
        board = board.sort_values(column, ascending=(order == "Lowest first")).reset_index(drop=True)
        board.insert(0, "Position", np.arange(1, len(board) + 1))
        leaders = board.head(top_n)

        col_a, col_b = st.columns([1.5, 1], gap="large")
        with col_a:
            drawn = leaders.iloc[::-1]
            positive_scale = column in {"GDP", "GDP Share %"}
            fig = go.Figure(go.Bar(
                x=drawn[column], y=drawn["Country Name"], orientation="h",
                marker=dict(
                    color=drawn[column],
                    colorscale=SEQ_SCALE if positive_scale else DIVERGING,
                    cmid=None if positive_scale else 0, line=dict(width=0),
                ),
                hovertemplate="%{y}<br>%{x:,.2f}<extra></extra>",
            ))
            fig.update_layout(title=f"Top {len(leaders)} by {metric_label.lower()}", showlegend=False)
            fig.update_xaxes(title=metric_label,
                             tickformat="$,.2s" if unit == "$" else ",.1f",
                             ticksuffix="" if unit == "$" else ("%" if unit == "%" else " pp"))
            style_fig(fig, max(430, len(leaders) * 30))
            show(fig, "rk_bar")

        with col_b:
            tree_source = snapshot.head(max(top_n, 12))
            fig = px.treemap(
                tree_source, path=[px.Constant(f"World {focus_year}"), "Country Name"],
                values="GDP", color="GDP Share %", color_continuous_scale=SEQ_SCALE,
                custom_data=["GDP Share %", "Rank"],
            )
            fig.update_traces(
                marker=dict(line=dict(color="rgba(4,9,15,.6)", width=1.4)),
                textfont=dict(family="Inter", size=13),
                hovertemplate="<b>%{label}</b><br>%{value:$,.4s}<br>%{customdata[0]:.2f}% of world GDP<extra></extra>",
            )
            fig.update_layout(title=f"Where output sits, top {len(tree_source)}",
                              coloraxis_colorbar=dict(title="Share %", thickness=12))
            style_fig(fig, max(430, len(leaders) * 30), legend_top=False)
            show(fig, "rk_tree")

        display_columns = ["Position", "Country Name", "Country Code"]
        for candidate in ["GDP", "GDP Share %", "YoY Growth %", "CAGR %", "Average Growth %",
                          "Volatility %", "Observations"]:
            if candidate in board.columns and candidate not in display_columns:
                display_columns.append(candidate)

        formats = {
            "GDP": st.column_config.NumberColumn(f"GDP {focus_year}", format="$%.0f"),
            "GDP Share %": st.column_config.NumberColumn("Share %", format="%.2f%%"),
            "YoY Growth %": st.column_config.NumberColumn(f"Growth {focus_year} %", format="%.2f%%"),
            "CAGR %": st.column_config.NumberColumn("CAGR %", format="%.2f%%"),
            "Average Growth %": st.column_config.NumberColumn("Avg growth %", format="%.2f%%"),
            "Volatility %": st.column_config.NumberColumn("Volatility (pp)", format="%.2f"),
            "Position": st.column_config.NumberColumn(format="%d"),
            "Observations": st.column_config.NumberColumn("Years observed", format="%d"),
        }
        st.dataframe(
            board[display_columns].round(2), use_container_width=True, hide_index=True, height=440,
            column_config={k: v for k, v in formats.items() if k in display_columns},
        )

        download("Download this ranking", board[display_columns].round(4),
                 f"gdp_ranking_{focus_year}.csv", "dl_rank")


elif page == "Custom Analysis":
    section("Custom period analysis",
            "Compare two specific points in time. Each metric is only shown for economies that meet its own "
            "data requirement, so nothing is estimated across missing years.")

    col_a, col_b, col_c = st.columns([1, 1, 1.4], gap="medium")
    with col_a:
        custom_start = int(st.number_input("Start year", min_value=MIN_YEAR, max_value=MAX_YEAR - 1,
                                           value=max(MIN_YEAR, min(2000, MAX_YEAR - 1)), step=1, key="cp_start"))
    with col_b:
        custom_end = int(st.number_input("End year", min_value=custom_start + 1, max_value=MAX_YEAR,
                                         value=MAX_YEAR, step=1, key="cp_end"))
    with col_c:
        chosen = st.multiselect("Economies", ALL_COUNTRIES,
                                default=compare_countries or DEFAULT_COMPARE,
                                max_selections=12, key="cp_countries",
                                placeholder="Search for a country")

    custom_frame = countries_only[(countries_only["Year"] >= custom_start) & (countries_only["Year"] <= custom_end)]
    custom_table = endpoint_metrics(custom_frame, custom_start, custom_end)

    world_start = custom_frame.loc[custom_frame["Year"] == custom_start, "GDP"].sum()
    world_end = custom_frame.loc[custom_frame["Year"] == custom_end, "GDP"].sum()
    world_span = custom_end - custom_start
    world_cagr = ((world_end / world_start) ** (1 / world_span) - 1) * 100 if world_start > 0 and world_span > 0 else np.nan

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        kpi("🗓️", "Window", f"{custom_start}–{custom_end}", f"{world_span} years apart")
    with k2:
        kpi("🌐", f"World GDP in {custom_start}", money(world_start),
            f"{int((custom_frame['Year'] == custom_start).sum())} economies reporting")
    with k3:
        kpi("🌐", f"World GDP in {custom_end}", money(world_end),
            f"{int((custom_frame['Year'] == custom_end).sum())} economies reporting")
    with k4:
        kpi("📈", "World CAGR", pct(world_cagr),
            f"Total change {pct((world_end / world_start - 1) * 100 if world_start else np.nan)}")

    if not chosen:
        st.info("Select at least one economy above to see the period breakdown.")
    else:
        window = custom_table[custom_table["Country Name"].isin(chosen)].copy()

        if window.empty:
            st.info(f"None of the selected economies reported GDP between {custom_start} and {custom_end}.")
        else:
            eligible_cagr = window[window["CAGR %"].notna()]
            missing_endpoints = window[window["CAGR %"].isna()]

            facts([
                ("Economies selected", str(len(window))),
                (f"Reported in {custom_start} and {custom_end}", str(len(eligible_cagr))),
                ("CAGR and total growth shown", str(len(eligible_cagr))),
                ("Average growth shown", str(int(window["Average Growth %"].notna().sum()))),
                ("Volatility shown", str(int(window["Volatility %"].notna().sum()))),
            ])

            if not missing_endpoints.empty:
                names = ", ".join(
                    f"{r['Country Name']} ({r['Status'].lower()})"
                    for _, r in missing_endpoints.head(6).iterrows()
                )
                insight(
                    f"<b>{len(missing_endpoints)} of {len(window)} selected economies have no endpoint-to-endpoint "
                    f"measurement.</b> CAGR and total growth are left blank for them rather than substituted with "
                    f"the nearest available year: {names}.", "blue"
                )

            if eligible_cagr.empty:
                st.info(f"No selected economy reported GDP in both {custom_start} and {custom_end}, "
                        f"so compound growth cannot be calculated for this window.")
            else:
                ordered = eligible_cagr.sort_values("CAGR %", ascending=False)
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=ordered["Country Name"], y=ordered["CAGR %"], name="CAGR",
                    marker_color="#6ee7d7",
                    hovertemplate="%{x}<br>CAGR %{y:.2f}%<extra></extra>",
                ))
                fig.add_trace(go.Bar(
                    x=ordered["Country Name"], y=ordered["Average Growth %"], name="Average annual growth",
                    marker_color="#7daeff",
                    hovertemplate="%{x}<br>Average %{y:.2f}%<extra></extra>",
                ))
                fig.add_hline(y=world_cagr, line_dash="dot", line_color="#ffc978",
                              annotation_text=f"world CAGR {pct(world_cagr)}", annotation_font_color="#ffc978")
                fig.update_layout(title=f"Growth between {custom_start} and {custom_end}", barmode="group")
                fig.update_yaxes(title="Growth (%)", ticksuffix="%")
                style_fig(fig, 450)
                show(fig, "ca_bars")

                above = ordered[ordered["CAGR %"] > world_cagr] if pd.notna(world_cagr) else ordered.iloc[0:0]
                if not above.empty:
                    insight(
                        f"<b>{len(above)} of {len(ordered)} measurable economies recorded a CAGR above the world "
                        f"rate of {pct(world_cagr)}</b> between {custom_start} and {custom_end}. The highest is "
                        f"{above.iloc[0]['Country Name']} at {pct(above.iloc[0]['CAGR %'])} a year."
                    )

            paths = custom_frame[custom_frame["Country Name"].isin(chosen)].dropna(subset=["GDP"]).sort_values("Year")
            if not paths.empty:
                base = paths.groupby("Country Name")["GDP"].transform("first")
                paths = paths.assign(Index=paths["GDP"] / base * 100)
                fig = px.line(paths, x="Year", y="Index", color="Country Name",
                              color_discrete_sequence=PALETTE)
                fig.update_traces(line=dict(width=2.6, shape="spline"),
                                  hovertemplate="%{fullData.name}<br>%{x}: %{y:,.0f}<extra></extra>")
                fig.add_hline(y=100, line_dash="dot", line_color="rgba(148,183,226,.3)")
                fig.update_layout(title="Indexed growth path (each country's first reported year = 100)")
                fig.update_yaxes(title="Index", type="log")
                style_fig(fig, 460)
                show(fig, "ca_paths")

            display = window[["Country Name", "Country Code", "Status", "First Year", "Last Year",
                              "Observations", "Longest Run", "Start GDP", "End GDP",
                              "Total Growth %", "CAGR %", "Average Growth %", "Volatility %"]]
            st.dataframe(
                display.round(2), use_container_width=True, hide_index=True,
                column_config={
                    "Start GDP": st.column_config.NumberColumn(f"GDP {custom_start}", format="$%.0f"),
                    "End GDP": st.column_config.NumberColumn(f"GDP {custom_end}", format="$%.0f"),
                    "First Year": st.column_config.NumberColumn(format="%d"),
                    "Last Year": st.column_config.NumberColumn(format="%d"),
                    "Observations": st.column_config.NumberColumn("Years reported", format="%d"),
                    "Longest Run": st.column_config.NumberColumn("Longest consecutive run", format="%d"),
                    "Total Growth %": st.column_config.NumberColumn(format="%.1f%%"),
                    "CAGR %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Average Growth %": st.column_config.NumberColumn("Avg growth %", format="%.2f%%"),
                    "Volatility %": st.column_config.NumberColumn("Volatility (pp)", format="%.2f"),
                },
            )
            st.caption("A blank cell means that metric's data requirement was not met, not that the value is zero.")

            download("Download this period analysis", display.round(4),
                     f"gdp_period_{custom_start}_{custom_end}.csv", "dl_custom")


elif page == "Data Explorer":
    section("Data explorer", "Search, filter and export the prepared dataset behind every chart.")

    col_a, col_b, col_c = st.columns([1.4, 1, 1], gap="medium")
    with col_a:
        query = st.text_input("Search", placeholder="Country name or ISO-3 code", key="ex_query")
    with col_b:
        scope = st.selectbox("Rows to include", ["Countries only", "Aggregates only", "Everything"], key="ex_scope")
    with col_c:
        completeness = st.selectbox("GDP values", ["Reported only", "Include missing years"], key="ex_missing")

    explorer_years = st.slider("Years", MIN_YEAR, MAX_YEAR, (period_start, period_end), key="ex_years")

    explorer = data[(data["Year"] >= explorer_years[0]) & (data["Year"] <= explorer_years[1])].copy()
    if scope == "Countries only":
        explorer = explorer[explorer["Is Country"]]
    elif scope == "Aggregates only":
        explorer = explorer[~explorer["Is Country"]]
    if completeness == "Reported only":
        explorer = explorer.dropna(subset=["GDP"])
    if query.strip():
        needle = query.strip()
        explorer = explorer[
            explorer["Country Name"].str.contains(needle, case=False, na=False)
            | explorer["Country Code"].str.contains(needle, case=False, na=False)
        ]

    explorer = explorer.rename(columns={"Is Country": "Country (not aggregate)"})
    explorer = explorer[["Country Name", "Country Code", "Year", "GDP", "YoY Growth %", "Country (not aggregate)"]]
    explorer = explorer.sort_values(["Year", "GDP"], ascending=[False, False])

    st.caption(f"{len(explorer):,} rows · {explorer['Country Code'].nunique():,} entities · "
               f"{explorer_years[0]}–{explorer_years[1]}")

    if explorer.empty:
        st.info("Nothing matches this search. Clear the text box or widen the year range.")
    else:
        st.dataframe(
            explorer, use_container_width=True, hide_index=True, height=520,
            column_config={
                "GDP": st.column_config.NumberColumn("GDP (US$)", format="$%.0f"),
                "YoY Growth %": st.column_config.NumberColumn("YoY growth", format="%.2f%%"),
                "Year": st.column_config.NumberColumn(format="%d"),
            },
        )
        st.caption("The download below contains exactly the rows shown above, with these filters applied.")
        download("Download exactly these filtered rows", explorer.round(4),
                 "gdp_explorer_filtered.csv", "dl_ex_filtered")


elif page == "Data Quality":
    section("Data quality",
            "Countries and World Bank aggregates are assessed separately, because mixing them makes every "
            "coverage figure misleading.")

    country_frame = data[data["Is Country"]]
    aggregate_frame = data[~data["Is Country"]]
    country_report = quality_report(country_frame)
    aggregate_report = quality_report(aggregate_frame)

    html(
        f'<div class="insight blue"><b>Two populations, reported separately.</b> The file holds '
        f'{country_report["entities"]} countries and territories and {aggregate_report["entities"]} World Bank '
        f'aggregates. Only countries and territories appear in rankings, maps, profiles and world totals.</div>'
    )

    scope_choice = st.radio("Scope", ["Countries and territories", "World Bank aggregates"],
                            horizontal=True, key="dq_scope")
    is_country_scope = scope_choice == "Countries and territories"
    report = country_report if is_country_scope else aggregate_report
    scope_frame = country_frame if is_country_scope else aggregate_frame
    noun = "countries and territories" if is_country_scope else "aggregate entities"

    k1, k2, k3, k4, k5 = st.columns(5, gap="medium")
    with k1:
        kpi("🧾", "Rows in scope", num(report["rows"]), f"{num(report['observed'])} carry a GDP value")
    with k2:
        kpi("🌍" if is_country_scope else "🧩", "Entities", num(report["entities"]), noun.capitalize())
    with k3:
        kpi("⚠️", "Missing GDP", num(report["missing"]), f"{pct(report['missing_pct'])} of rows in scope")
    with k4:
        kpi("🔁", "Duplicate keys", num(report["duplicates"]), "Country and year combinations")
    with k5:
        kpi("📅", "Year range", f"{int(scope_frame['Year'].min())}–{int(scope_frame['Year'].max())}",
            f"{report['span']} years expected per entity")

    k6, k7, k8, k9 = st.columns(4, gap="medium")
    with k6:
        kpi("✅", "Complete series", num(report["complete"]), "Reporting every year in the range")
    with k7:
        kpi("🕳️", "Series with internal gaps", num(report["gap_entities"]), "At least one missing year inside")
    with k8:
        kpi("➖", "Negative GDP values", num(report["negatives"]), "Should be zero in a valid extract")
    with k9:
        kpi("⓪", "Zero GDP values", num(report["zeros"]), "Excluded from growth calculations")

    col_a, col_b = st.columns([1.3, 1], gap="large")

    with col_a:
        coverage_by_year = scope_frame.groupby("Year").agg(
            Reported=("GDP", "count"), Total=("GDP", "size")
        ).reset_index()
        coverage_by_year["Coverage %"] = coverage_by_year["Reported"] / coverage_by_year["Total"] * 100
        fig = go.Figure(go.Scatter(
            x=coverage_by_year["Year"], y=coverage_by_year["Coverage %"], mode="lines",
            line=dict(color="#6ee7d7" if is_country_scope else "#ff9f87", width=2.6, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(110,231,215,0.10)" if is_country_scope else "rgba(255,159,135,0.10)",
            customdata=coverage_by_year["Reported"],
            hovertemplate="%{x}<br>%{y:.1f}% reporting (%{customdata} entities)<extra></extra>",
        ))
        fig.update_layout(title=f"Share of {noun} reporting GDP, by year", showlegend=False)
        fig.update_yaxes(title="Coverage (%)", ticksuffix="%", range=[0, 102])
        style_fig(fig, 420)
        show(fig, "dq_coverage")

    with col_b:
        checks = pd.DataFrame({
            "Check": ["Complete series", "Series with internal gaps", "Duplicate country-year keys",
                      "Negative GDP values", "Zero GDP values"],
            "Count": [report["complete"], report["gap_entities"], report["duplicates"],
                      report["negatives"], report["zeros"]],
        })
        fig = go.Figure(go.Bar(
            x=checks["Count"], y=checks["Check"], orientation="h",
            marker_color=["#8fe3a2", "#ffc978", "#f7a3c4", "#ff9f87", "#ff9f87"],
            hovertemplate="%{y}: %{x}<extra></extra>",
        ))
        fig.update_layout(title=f"Integrity checks — {noun}", showlegend=False)
        fig.update_xaxes(title="Entities")
        style_fig(fig, 420)
        show(fig, "dq_checks")

    insight(
        f"<b>Gaps are left as gaps.</b> {report['gap_entities']} series in this scope have at least one missing "
        f"year inside their reporting range. Year-on-year growth is only calculated between consecutive observed "
        f"years, so a break never turns into a fabricated jump."
    )

    section("Coverage by entity", "Sorted by how much of the full year range each entity reports.")
    coverage = report["coverage"]
    worst_first = st.toggle("Show least complete first", value=False, key="dq_order")
    coverage_view = coverage.sort_values("Coverage %", ascending=worst_first)
    st.dataframe(
        coverage_view.round(1), use_container_width=True, hide_index=True, height=420,
        column_config={
            "Coverage %": st.column_config.ProgressColumn("Coverage", min_value=0, max_value=100, format="%.0f%%"),
            "First Year": st.column_config.NumberColumn(format="%d"),
            "Last Year": st.column_config.NumberColumn(format="%d"),
            "Expected Years": st.column_config.NumberColumn(format="%d"),
            "Observations": st.column_config.NumberColumn(format="%d"),
            "Internal Gaps": st.column_config.NumberColumn(format="%d"),
        },
    )
    download(f"Download the coverage report ({noun})", coverage.round(4),
             "gdp_coverage_report.csv" if is_country_scope else "gdp_coverage_report_aggregates.csv",
             "dl_quality")


elif page == "Download Center":
    section("Download centre",
            "Every file is generated from the data and filters currently applied, as UTF-8 CSV.")

    facts([
        ("Analysis period", f"{period_start}–{period_end}"),
        ("Focus year", str(focus_year)),
        ("Countries in scope", str(len(ALL_COUNTRIES))),
        ("Leaderboard size", str(top_n)),
    ])

    country_rows = data[data["Is Country"]]
    aggregate_rows = data[~data["Is Country"]]
    coverage_report = quality_report(country_rows)["coverage"]

    country_summary = metrics.merge(
        snapshot[["Country Code", "Rank", "GDP", "GDP Share %", "YoY Growth %"]].rename(
            columns={"Rank": f"Rank {focus_year}", "GDP": f"GDP {focus_year}",
                     "GDP Share %": f"Share {focus_year} %", "YoY Growth %": f"Growth {focus_year} %"}),
        on="Country Code", how="left",
    )

    section("Core datasets", "Always complete, whatever the sidebar filters say.")
    col_a, col_b, col_c = st.columns(3, gap="medium")
    with col_a:
        download("Full clean dataset", data.round(4), "gdp_clean_full.csv", "dl_full")
        st.caption(f"{len(data):,} rows · countries and aggregates · every year")
    with col_b:
        download("Countries and territories only", country_rows.round(4), "gdp_countries.csv", "dl_countries")
        st.caption(f"{len(country_rows):,} rows · {country_rows['Country Code'].nunique()} entities")
    with col_c:
        download("World Bank aggregates only", aggregate_rows.round(4), "gdp_aggregates.csv", "dl_aggregates")
        st.caption(f"{len(aggregate_rows):,} rows · {aggregate_rows['Country Code'].nunique()} entities")

    section("Current view", "These follow the period, focus year and leaderboard size you have set.")
    col_a, col_b, col_c = st.columns(3, gap="medium")
    with col_a:
        download(f"Snapshot for {focus_year}",
                 snapshot[["Rank", "Country Name", "Country Code", "Year", "GDP",
                           "GDP Share %", "YoY Growth %"]].round(4),
                 f"gdp_snapshot_{focus_year}.csv", "dl_snapshot")
        st.caption(f"{len(snapshot)} economies reporting in {focus_year}")
    with col_b:
        ranking_export = snapshot[["Rank", "Country Name", "Country Code", "GDP",
                                   "GDP Share %", "YoY Growth %"]].head(top_n).round(4)
        download(f"Ranking, top {top_n} in {focus_year}", ranking_export,
                 f"gdp_ranking_{focus_year}.csv", "dl_ranking")
        st.caption("Ordered by GDP, aggregates excluded")
    with col_c:
        download(f"Growth analysis, {period_start}–{period_end}", metrics.round(4),
                 f"gdp_growth_{period_start}_{period_end}.csv", "dl_growth_center")
        st.caption("CAGR, average growth, volatility and peak per country")

    section("Reference tables")
    col_a, col_b, col_c = st.columns(3, gap="medium")
    with col_a:
        download("Country summary", country_summary.round(4), "gdp_country_summary.csv", "dl_summary")
        st.caption("Period metrics joined to the focus-year snapshot")
    with col_b:
        download("Coverage report", coverage_report.round(4), "gdp_coverage_report.csv", "dl_coverage_center")
        st.caption("First year, last year, observations, gaps and coverage")
    with col_c:
        explorer_export = data[(data["Year"] >= period_start) & (data["Year"] <= period_end)]
        explorer_export = explorer_export[explorer_export["Is Country"]].dropna(subset=["GDP"])
        download("Explorer data for this period", explorer_export.round(4),
                 f"gdp_explorer_{period_start}_{period_end}.csv", "dl_explorer_center")
        st.caption(f"{len(explorer_export):,} reported country rows in the current period")

    insight(
        "<b>Filters travel with the files.</b> The snapshot, ranking, growth, summary and explorer exports follow "
        "the sidebar settings. For row-level filtering by search term or entity type, use the download at the "
        "bottom of the Data Explorer, which returns exactly the rows shown there.", "blue"
    )


elif page == "Methodology":
    section("Methodology and limitations", "How each number on this dashboard is produced.")

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        html(
            '<div class="panel"><h4>How the metrics are calculated</h4>'
            '<ul>'
            '<li><b>GDP</b> is gross domestic product in current US dollars, World Bank series NY.GDP.MKTP.CD, '
            'exactly as published.</li>'
            '<li><b>Year-on-year growth</b> is the change from one year to the next, calculated only between '
            'consecutive observed years. Where a year is missing, the value is left blank.</li>'
            '<li><b>CAGR</b> is the compound annual growth rate, (last ÷ first)^(1 ÷ years) − 1. On the growth '
            'pages it uses the first and last observed years inside the period. In Custom Analysis it uses the '
            'two endpoint years you choose, and stays blank unless both were actually reported.</li>'
            '<li><b>Total growth</b> is the change between those same two reference points.</li>'
            '<li><b>Average growth</b> is the mean of the yearly changes inside the period, and needs at least '
            'one such change.</li>'
            '<li><b>Volatility</b> is the standard deviation of those yearly changes, in percentage points, and '
            'needs at least two of them.</li>'
            '<li><b>World GDP</b> is the sum of reporting countries for that year. Aggregate rows are excluded, '
            'so nothing is counted twice.</li>'
            '<li><b>GDP share</b> is a country\'s GDP divided by that same world total.</li>'
            '<li><b>Concentration</b> uses cumulative share, a Herfindahl–Hirschman index on percentage shares, '
            'and a Gini coefficient across economies.</li>'
            '</ul></div>'
        )

    with col_b:
        html(
            '<div class="panel"><h4>Limitations worth knowing</h4>'
            '<ul>'
            '<li>Figures are nominal, in current dollars. They are not adjusted for inflation or purchasing power, '
            'so growth partly reflects prices and exchange rates.</li>'
            '<li>Reporting coverage widens over time. Rising world GDP in early decades partly reflects more '
            'countries reporting, not only more output.</li>'
            '<li>Countries that dissolved or formed mid-series carry broken histories, so a long-run CAGR for them '
            'spans two different political entities.</li>'
            '<li>World totals here cover reporting countries only and differ slightly from the World Bank\'s own '
            'published world aggregate.</li>'
            '<li>Growth leaderboards apply a minimum number of observed years, because a two-point series can '
            'produce a large and uninformative CAGR.</li>'
            '<li>A few territories have no standard map geometry and cannot be shaded, though they remain in '
            'every table and ranking.</li>'
            '<li>The dashboard reports what the source file contains. It does not fill, interpolate or estimate '
            'missing values.</li>'
            '</ul></div>'
        )

    section("How countries are separated from aggregates")
    html(
        '<div class="panel"><p>The World Bank file mixes individual economies with aggregate rows such as World, '
        'European Union, high-income countries and IDA borrowers. Left in place, those rows dominate every ranking '
        'and double-count output. This dashboard identifies them from their ISO-3 codes, backed by a whole-word '
        'name check, so no additional package is needed. Aggregates are held out of rankings, maps, profiles and '
        'every world total, and stay browsable in the data explorer and the download centre.</p></div>'
    )

    section("Data pipeline")
    html(
        '<div class="panel"><p>The wide World Bank export is the source of truth because it carries country names. '
        'It is reshaped from one column per year into one row per country-year, types are coerced, duplicate '
        'country-year keys are dropped, and growth is recomputed from scratch rather than trusted from any '
        'pre-calculated column. Prepared data and derived metrics are cached and keyed on the source files\' size '
        'and modification time, so editing a CSV refreshes the dashboard without clearing the cache by hand.</p>'
        '</div>'
    )


elif page == "About":
    section("About this project")

    col_a, col_b = st.columns([1.25, 1], gap="large")

    with col_a:
        html(
            '<div class="panel"><h4>Global GDP Explorer</h4>'
            '<p>An interactive data analytics dashboard for exploring global economic performance, historical GDP '
            'trends, country comparisons, rankings, growth patterns, geographic distribution, and global GDP '
            'concentration.</p>'
            '<h4>What it covers</h4>'
            '<ul>'
            '<li>Global GDP trends, annual growth and reporting coverage</li>'
            '<li>Growth analysis: CAGR, average growth and volatility</li>'
            '<li>An interactive world map across four metrics</li>'
            '<li>Dynamic rankings, country profiles, comparison and head to head</li>'
            '<li>Custom period analysis between any two years</li>'
            '<li>Data explorer, data quality reporting and a download centre</li>'
            '</ul>'
            '<h4>Built with</h4>'
            '<p>Python, pandas, numpy, Plotly and Streamlit. No other dependencies.</p>'
            '<h4>Data source</h4>'
            '<p>World Bank, World Development Indicators — GDP (current US$), series NY.GDP.MKTP.CD.</p></div>'
        )

    with col_b:
        html(
            f'<div class="panel" style="text-align:center;"><div style="font-size:2.6rem;">👩🏻‍💻</div>'
            f'<h4 style="font-size:1.25rem;margin-top:.5rem;">{OWNER}</h4>'
            f'<p>Creator of the Global GDP Explorer</p>'
            f'<p><a class="link-btn" href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a>'
            f'<a class="link-btn" href="{GITHUB}" target="_blank" rel="noopener">GitHub</a></p></div>'
        )

    facts([
        ("Countries and territories", str(len(ALL_COUNTRIES))),
        ("Years covered", f"{MIN_YEAR}–{MAX_YEAR}"),
        ("Sections", str(len(PAGES))),
        ("Python dependencies", "4"),
    ])


# ──────────────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────────────
html(
    f'<div class="foot"><div>© {COPYRIGHT_YEAR} '
    f'<a href="{LINKEDIN}" target="_blank" rel="noopener">{OWNER}</a> · {APP_TITLE}</div>'
    f'<div>All rights reserved.</div>'
    f'<div>Data: World Bank, GDP in current US dollars · Built with Python, pandas, Plotly and Streamlit</div>'
    f'<div class="foot-links">'
    f'<a href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a>'
    f'<a href="{GITHUB}" target="_blank" rel="noopener">GitHub</a>'
    f'</div></div>'
)