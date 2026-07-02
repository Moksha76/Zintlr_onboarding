import streamlit as st

from database.db import init_db

init_db()

st.title("Activity Log")
st.info("Activity log filters and timeline will be built in Phase 7.")
