from datetime import timedelta

import streamlit as st

import config
from database.db import SessionLocal, init_db
from database.models import ActivityLog, Joiner
from services.scheduler import start_scheduler

init_db()
start_scheduler()

st.title("Add Joiner")

with st.form("add_joiner_form", clear_on_submit=False):
    full_name = st.text_input("Full name")
    candidate_email = st.text_input("Candidate email")
    designation = st.selectbox("Designation", options=[""] + config.DESIGNATIONS)
    doj = st.date_input("Date of joining", value=None, format="DD/MM/YYYY")
    submitted = st.form_submit_button("Add Joiner")

if submitted:
    if not full_name.strip() or not candidate_email.strip() or not designation or not doj:
        st.error("All fields are required.")
    else:
        session = SessionLocal()
        try:
            existing = (
                session.query(Joiner)
                .filter(Joiner.candidate_email == candidate_email.strip())
                .first()
            )
            if existing:
                st.error(f"A joiner with email {candidate_email} already exists.")
            else:
                team_name = config.DESIGNATION_TO_TEAM.get(designation, "team")
                sim_required = designation in config.DESIGNATIONS_REQUIRING_SIM
                form11_due_date = doj + timedelta(days=config.FORM11_OFFSET_DAYS)

                joiner = Joiner(
                    full_name=full_name.strip(),
                    candidate_email=candidate_email.strip(),
                    designation=designation,
                    team_name=team_name,
                    doj=doj,
                    current_stage="NEW",
                    sim_required=sim_required,
                    form11_due_date=form11_due_date,
                )
                session.add(joiner)
                session.commit()
                session.refresh(joiner)

                session.add(
                    ActivityLog(
                        event_type="joiner_added",
                        joiner_id=joiner.id,
                        details=f"Joiner added: {joiner.full_name} ({joiner.designation})",
                        tone="ok",
                    )
                )
                session.commit()

                st.success(f"{joiner.full_name} added successfully.")
                st.session_state["selected_joiner_id"] = joiner.id
                st.switch_page("pages/3_Candidate_Detail.py")
        finally:
            session.close()
