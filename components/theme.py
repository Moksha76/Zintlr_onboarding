import streamlit as st

PRIMARY = "#4B3F91"
PRIMARY_DARK = "#3A3072"
ACCENT = "#F0A93A"
INK = "#1F2430"
MUTED = "#6B7280"
BORDER = "#E7E5F0"
SURFACE = "#F7F6FB"

_CSS = f"""
<style>
html, body, [class*="css"] {{
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}}

/* App background */
[data-testid="stAppViewContainer"] > .main {{
    background: {SURFACE};
}}
[data-testid="stMain"] .block-container {{
    padding-top: 2rem;
    max-width: 1200px;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: #FFFFFF;
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebarNav"] a {{
    border-radius: 8px;
    font-weight: 500;
    color: {INK};
}}
[data-testid="stSidebarNav"] a:hover {{
    background: {SURFACE};
}}
[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: {PRIMARY}1A;
    color: {PRIMARY};
}}

/* Headings */
h1, h2, h3 {{
    color: {INK};
    letter-spacing: -0.01em;
}}
h1 {{
    font-weight: 800;
}}
h2, h3 {{
    font-weight: 700;
}}

/* Cards (st.container(border=True)) */
[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 14px !important;
    border-color: {BORDER} !important;
    background: #FFFFFF;
    box-shadow: 0 1px 3px rgba(31, 36, 48, 0.05);
}}

/* Buttons */
[data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {{
    border-radius: 8px;
    font-weight: 600;
    transition: transform 0.05s ease-in, box-shadow 0.1s ease-in;
    border: 1px solid {BORDER};
}}
[data-testid="stButton"] button:hover:not(:disabled),
[data-testid="stFormSubmitButton"] button:hover:not(:disabled) {{
    box-shadow: 0 2px 8px rgba(75, 63, 145, 0.18);
    transform: translateY(-1px);
}}
[data-testid="stButton"] button[kind="primary"] {{
    background: {PRIMARY};
    border-color: {PRIMARY};
}}
[data-testid="stButton"] button[kind="primary"]:hover:not(:disabled) {{
    background: {PRIMARY_DARK};
}}

/* Metrics -> KPI cards */
[data-testid="stMetric"] {{
    background: #FFFFFF;
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 3px rgba(31, 36, 48, 0.05);
}}
[data-testid="stMetricLabel"] {{
    color: {MUTED};
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.04em;
}}
[data-testid="stMetricValue"] {{
    color: {PRIMARY};
    font-weight: 800;
}}

/* Expanders */
[data-testid="stExpander"] {{
    border-radius: 12px !important;
    border-color: {BORDER} !important;
    background: #FFFFFF;
}}
[data-testid="stExpander"] summary {{
    font-weight: 600;
}}

/* Inputs */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stDateInput"] input,
[data-baseweb="select"] {{
    border-radius: 8px !important;
}}

/* Dividers: a bit lighter, more breathing room */
hr {{
    border-color: {BORDER};
    margin: 1.6rem 0;
}}

/* Links */
a {{
    color: {PRIMARY};
}}
</style>
"""


def inject_theme():
    st.markdown(_CSS, unsafe_allow_html=True)


def stage_badge_html(text: str, color_hex: str) -> str:
    return (
        f'<span style="background-color:{color_hex}1A; color:{color_hex}; '
        f'padding:3px 12px; border-radius:999px; font-size:0.78em; '
        f'font-weight:700; letter-spacing:0.02em; border:1px solid {color_hex}40;">{text}</span>'
    )
