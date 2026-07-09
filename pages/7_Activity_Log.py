from datetime import date, timedelta

import streamlit as st

from components.theme import inject_theme
from sqlalchemy import or_

from database.db import SessionLocal, init_db
from database.models import ActivityLog, Joiner
from services.scheduler import start_scheduler

init_db()
start_scheduler()
inject_theme()

st.title("Activity Log")
st.caption("A full history of everything the app has done — sends, stage changes, sheet syncs, alerts.")

_TONE_EMOJI = {"ok": "🟢", "warn": "🟠", "danger": "🔴", "info": "⚪"}
_TONE_OPTIONS = ["All", "ok", "warn", "danger", "info"]
_RESULT_LIMIT = 300

session = SessionLocal()
try:
    event_types = sorted(
        {row[0] for row in session.query(ActivityLog.event_type).distinct().all()}
    )
    joiners = session.query(Joiner).order_by(Joiner.full_name).all()
    joiner_options = {"All candidates": None, "System events (no candidate)": "none"}
    joiner_options.update({j.full_name: j.id for j in joiners})

    with st.container(border=True):
        st.subheader("Filters")
        col1, col2 = st.columns(2)
        with col1:
            selected_events = st.multiselect("Event type", options=event_types, default=[])
        with col2:
            selected_joiner_label = st.selectbox("Candidate", options=list(joiner_options.keys()))

        selected_tone = st.pills("Severity", options=_TONE_OPTIONS, default="All")
        selected_tone = selected_tone or "All"

        col3, col4, col5 = st.columns([1, 1, 2])
        with col3:
            start_date = st.date_input("From", value=date.today() - timedelta(days=30), format="DD/MM/YYYY")
        with col4:
            end_date = st.date_input("To", value=date.today(), format="DD/MM/YYYY")
        with col5:
            search_text = st.text_input("Search in details", placeholder="e.g. a candidate name or word")

    query = session.query(ActivityLog)

    if selected_events:
        query = query.filter(ActivityLog.event_type.in_(selected_events))
    if selected_tone != "All":
        query = query.filter(ActivityLog.tone == selected_tone)
    selected_joiner_value = joiner_options[selected_joiner_label]
    if selected_joiner_value == "none":
        query = query.filter(ActivityLog.joiner_id.is_(None))
    elif selected_joiner_value is not None:
        query = query.filter(ActivityLog.joiner_id == selected_joiner_value)
    if search_text:
        query = query.filter(
            or_(
                ActivityLog.details.ilike(f"%{search_text}%"),
                ActivityLog.event_type.ilike(f"%{search_text}%"),
            )
        )

    query = query.filter(
        ActivityLog.timestamp >= start_date,
        ActivityLog.timestamp < end_date + timedelta(days=1),
    )

    total_matches = query.count()
    logs = query.order_by(ActivityLog.timestamp.desc()).limit(_RESULT_LIMIT).all()

    joiner_names = {j.id: j.full_name for j in joiners}

    st.write("")
    if total_matches > _RESULT_LIMIT:
        st.caption(f"Showing the most recent {_RESULT_LIMIT} of {total_matches} matching events.")
    else:
        st.caption(f"{total_matches} matching event(s).")

    if not logs:
        st.info("No activity matches these filters.")

    with st.container(border=True):
        for log in logs:
            who = joiner_names.get(log.joiner_id, "") if log.joiner_id else ""
            who_suffix = f"  ·  {who}" if who else ""
            st.write(
                f"{_TONE_EMOJI.get(log.tone, '⚪')} "
                f"**{log.timestamp.strftime('%d/%m/%Y %H:%M')}**  ·  {log.event_type}{who_suffix}  —  {log.details}"
            )
finally:
    session.close()
