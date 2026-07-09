import streamlit as st

from components.theme import inject_theme
from database.db import init_db
from services.scheduler import start_scheduler

init_db()
start_scheduler()
inject_theme()

st.title("Activity Log")
st.info("Activity log filters and timeline will be built in Phase 7.")
