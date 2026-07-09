from datetime import date, datetime, time

import streamlit as st

from components.theme import inject_theme
from database.db import SessionLocal, init_db
from database.models import EmailTemplate, Joiner, ScheduledEmail
from services import scheduled_email_service, stage_service
from services.scheduler import start_scheduler

init_db()
start_scheduler()
inject_theme()

st.title("Scheduled")
st.caption("Schedule the 4 pre-onboarding emails for a candidate — they send automatically at the time you pick.")

PREONBOARD_KEYS = ["preonboard_story", "preonboard_culture", "preonboard_leadership", "preonboard_joining"]
ELIGIBLE_STAGES = {"DB_RECEIVED", "DB_SENT", "ONBOARDING"}

session = SessionLocal()
try:
    display_names = {
        t.template_key: t.display_name
        for t in session.query(EmailTemplate).filter(EmailTemplate.active.is_(True)).all()
    }

    eligible_joiners = (
        session.query(Joiner).filter(Joiner.current_stage.in_(ELIGIBLE_STAGES)).order_by(Joiner.full_name).all()
    )

    st.write("")
    with st.container(border=True):
        st.subheader("Schedule a pre-onboarding email")

        if not eligible_joiners:
            st.info("No candidates are at a stage where pre-onboarding emails apply yet (DB form received or later).")
        else:
            joiner_options = {f"{j.full_name} ({j.candidate_email})": j for j in eligible_joiners}
            selected_label = st.selectbox("Candidate", options=list(joiner_options.keys()))
            selected_joiner = joiner_options[selected_label]

            enabled_stages_map = stage_service.TEMPLATE_ENABLED_STAGES
            available_keys = [
                k
                for k in PREONBOARD_KEYS
                if enabled_stages_map.get(k) is None or selected_joiner.current_stage in enabled_stages_map[k]
            ]

            if not available_keys:
                st.info(f"No pre-onboarding emails apply to {selected_joiner.full_name} at their current stage.")
            else:
                template_options = {display_names.get(k, k): k for k in available_keys}
                selected_template_label = st.selectbox("Email", options=list(template_options.keys()))
                selected_template_key = template_options[selected_template_label]

                col1, col2 = st.columns(2)
                with col1:
                    send_date = st.date_input("Send date", value=date.today(), format="DD/MM/YYYY")
                with col2:
                    send_time = st.time_input("Send time", value=time(9, 0))

                if st.button("Schedule", type="primary"):
                    scheduled_for = datetime.combine(send_date, send_time)
                    scheduled_email_service.schedule_email(
                        selected_joiner.id, selected_template_key, scheduled_for
                    )
                    st.success(
                        f"Scheduled {selected_template_label} for {selected_joiner.full_name} "
                        f"on {scheduled_for.strftime('%d/%m/%Y at %H:%M')}."
                    )
                    st.rerun()

    st.write("")
    st.subheader("Upcoming")
    upcoming = (
        session.query(ScheduledEmail)
        .filter(ScheduledEmail.status == "scheduled")
        .order_by(ScheduledEmail.scheduled_for)
        .all()
    )
    if not upcoming:
        st.caption("Nothing scheduled right now.")
    for row in upcoming:
        joiner = session.get(Joiner, row.joiner_id)
        if not joiner:
            continue
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            c1.write(f"**{joiner.full_name}**")
            c2.write(display_names.get(row.template_key, row.template_key))
            c3.write(row.scheduled_for.strftime("%d/%m/%Y at %H:%M"))
            with c4:
                if st.button("Cancel", key=f"cancel_{row.id}", use_container_width=True):
                    scheduled_email_service.cancel_scheduled_email(row.id)
                    st.rerun()

    st.write("")
    with st.expander("Sent history"):
        sent = (
            session.query(ScheduledEmail)
            .filter(ScheduledEmail.status == "sent")
            .order_by(ScheduledEmail.sent_at.desc())
            .limit(50)
            .all()
        )
        if not sent:
            st.caption("No scheduled emails have gone out yet.")
        for row in sent:
            joiner = session.get(Joiner, row.joiner_id)
            name = joiner.full_name if joiner else f"Joiner #{row.joiner_id}"
            sent_at = row.sent_at.strftime("%d/%m/%Y %H:%M") if row.sent_at else "-"
            st.write(f"🟢 {sent_at} — {display_names.get(row.template_key, row.template_key)} sent to {name}")

    with st.expander("Failed"):
        failed = (
            session.query(ScheduledEmail)
            .filter(ScheduledEmail.status == "failed")
            .order_by(ScheduledEmail.scheduled_for.desc())
            .all()
        )
        if not failed:
            st.caption("No failed sends.")
        for row in failed:
            joiner = session.get(Joiner, row.joiner_id)
            name = joiner.full_name if joiner else f"Joiner #{row.joiner_id}"
            fc1, fc2 = st.columns([4, 1])
            fc1.write(
                f"🔴 {display_names.get(row.template_key, row.template_key)} for {name} — was due "
                f"{row.scheduled_for.strftime('%d/%m/%Y %H:%M')}"
            )
            with fc2:
                if st.button("Retry now", key=f"retry_{row.id}", use_container_width=True):
                    scheduled_email_service.schedule_email(row.joiner_id, row.template_key, datetime.utcnow())
                    row.status = "cancelled"
                    session.commit()
                    st.rerun()
finally:
    session.close()
