import streamlit as st

from database.db import init_db
from services.scheduler import start_scheduler

init_db()
start_scheduler()

st.title("Scheduled")
st.info("Scheduled email table and creation modal will be built in Phase 5.")
