import streamlit as st

from database.db import init_db
from services.scheduler import start_scheduler

init_db()
start_scheduler()

st.title("Inventory")
st.info("Kit and T-shirt inventory management will be built in Phase 6.")
