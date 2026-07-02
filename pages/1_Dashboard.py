import streamlit as st

from database.db import init_db

init_db()

st.title("Dashboard")
st.info("Dashboard KPIs, filter pills, and candidate table will be built in Phase 3.")
