import streamlit as st

from components.theme import inject_theme
from database.db import init_db
from services.scheduler import start_scheduler

init_db()
start_scheduler()
inject_theme()

st.title("Scheduled")
st.info("Scheduled email table and creation modal will be built in Phase 5.")
