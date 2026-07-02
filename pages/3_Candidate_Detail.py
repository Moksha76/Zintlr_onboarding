import streamlit as st

from database.db import SessionLocal, init_db
from database.models import Joiner

init_db()

st.title("Candidate Detail")

joiner_id = st.session_state.get("selected_joiner_id")

if not joiner_id:
    st.info("Select a candidate from the Dashboard to view details. Full layout will be built in Phase 3.")
else:
    session = SessionLocal()
    try:
        joiner = session.get(Joiner, joiner_id)
        if joiner:
            st.subheader(joiner.full_name)
            st.write(f"Email: {joiner.candidate_email}")
            st.write(f"Designation: {joiner.designation}")
            st.write(f"Date of joining: {joiner.doj}")
            st.write(f"Stage: {joiner.current_stage}")
            st.info("Full action buttons, checklist, and timeline will be built in Phase 3.")
        else:
            st.error("Candidate not found.")
    finally:
        session.close()
