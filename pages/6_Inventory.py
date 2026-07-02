import streamlit as st

from database.db import init_db

init_db()

st.title("Inventory")
st.info("Kit and T-shirt inventory management will be built in Phase 6.")
