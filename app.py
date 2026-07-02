import streamlit as st

from database.db import init_db

st.set_page_config(page_title="Zintlr Onboarding", page_icon="\U0001F4CB", layout="wide")

init_db()

st.sidebar.title("Zintlr Onboarding")

st.title("Zintlr Onboarding Automation")
st.write("Use the sidebar to navigate: Dashboard, Add Joiner, Candidate Detail, Templates, Scheduled, Inventory, Activity Log.")
