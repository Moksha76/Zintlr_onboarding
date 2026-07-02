import streamlit as st

from database.db import init_db

init_db()

st.title("Templates")
st.info("Template list, preview, and edit flow will be built in Phase 2.")
