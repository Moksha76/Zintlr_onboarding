import streamlit as st

from database.db import init_db

init_db()

st.title("Scheduled")
st.info("Scheduled email table and creation modal will be built in Phase 5.")
