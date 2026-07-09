import streamlit as st

from components.theme import inject_theme
from database.db import init_db
from services.scheduler import start_scheduler

st.set_page_config(page_title="Zintlr Onboarding", page_icon="\U0001F4CB", layout="wide")

init_db()
start_scheduler()
inject_theme()

st.sidebar.title("Zintlr Onboarding")

st.title("Zintlr Onboarding Automation")
st.caption("Everything you need to take a joiner from BG verification through Form 11, in one place.")

st.write("")

cards = [
    ("Dashboard", "See every candidate's stage at a glance and jump into the next action.", "pages/1_Dashboard.py"),
    ("Add Joiner", "Add a new candidate manually.", "pages/2_Add_Joiner.py"),
    ("Templates", "Edit email and document templates, and send previews.", "pages/4_Templates.py"),
    ("Scheduled", "Upcoming pre-onboarding emails.", "pages/5_Scheduled.py"),
    ("Inventory", "Kit and T-shirt stock levels.", "pages/6_Inventory.py"),
    ("Activity Log", "A full history of everything the app has done.", "pages/7_Activity_Log.py"),
]

for row_start in range(0, len(cards), 3):
    cols = st.columns(3)
    for col, (label, desc, page) in zip(cols, cards[row_start : row_start + 3]):
        with col:
            with st.container(border=True):
                st.markdown(f"**{label}**")
                st.caption(desc)
                if st.button("Open →", key=f"open_{page}", use_container_width=True):
                    st.switch_page(page)
