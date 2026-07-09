from datetime import timedelta

import streamlit as st

import config
from components.email_preview import show_email_preview
from components.outlook_connect import render_outlook_connect_section
from components.theme import inject_theme, stage_badge_html
from database.db import SessionLocal, init_db
from database.models import ActivityLog, Inventory, Joiner
from services import stage_service
from services.scheduler import start_scheduler

init_db()
start_scheduler()
inject_theme()

st.title("Dashboard")

render_outlook_connect_section()
st.write("")

_CHIP_COLORS = {
    "amber": "#B45309",
    "blue": "#1D4ED8",
    "indigo": "#4338CA",
    "purple": "#7E22CE",
    "violet": "#6D28D9",
    "teal": "#0F766E",
    "green": "#15803D",
    "orange": "#C2410C",
    "red": "#B91C1C",
    "gray": "#4B5563",
}


def stage_chip(stage: str) -> str:
    color = _CHIP_COLORS.get(config.STAGE_COLORS.get(stage, "gray"), "#4B5563")
    return stage_badge_html(stage.replace("_", " "), color)


def _joiner_dict(j: Joiner) -> dict:
    return dict(
        id=j.id,
        name=j.full_name,
        email=j.candidate_email,
        designation=j.designation,
        team_name=j.team_name,
        doj=j.doj.strftime("%d/%m/%Y") if j.doj else "",
        uan=j.uan or "",
    )


session = SessionLocal()
try:
    last_sync = (
        session.query(ActivityLog)
        .filter(ActivityLog.event_type == "sheet_sync", ActivityLog.joiner_id.is_(None))
        .order_by(ActivityLog.timestamp.desc())
        .first()
    )
    if last_sync and last_sync.tone == "danger":
        st.error(f"Sheet sync failed — {last_sync.details}")
    elif last_sync and last_sync.tone == "warn":
        st.warning(last_sync.details)

    recent_syncs = (
        session.query(ActivityLog)
        .filter(ActivityLog.event_type == "sheet_sync", ActivityLog.tone == "ok")
        .order_by(ActivityLog.timestamp.desc())
        .limit(2)
        .all()
    )
    if len(recent_syncs) == 2:
        gap = recent_syncs[0].timestamp - recent_syncs[1].timestamp
        if gap > timedelta(minutes=config.SHEET_POLL_MINUTES * 2):
            st.info(
                f"The app looks like it was offline from {recent_syncs[1].timestamp.strftime('%d/%m %H:%M')} "
                f"to {recent_syncs[0].timestamp.strftime('%d/%m %H:%M')} — sheet sync and scheduled sends have "
                f"caught up automatically now that it's running again."
            )

    low_stock_items = session.query(Inventory).filter(Inventory.quantity <= Inventory.threshold).all()
    if low_stock_items:
        labels = [
            "Onboarding kit" if item.item_type == "kit" else f"T-shirt ({item.size})" for item in low_stock_items
        ]
        st.warning(f"Low stock: {', '.join(labels)} — check the Inventory page.")

    all_joiners = session.query(Joiner).all()

    active = [j for j in all_joiners if j.current_stage not in ("COMPLETED", "DROPPED")]
    bg_pending = [j for j in all_joiners if j.current_stage == "NEW"]
    db_pending = [j for j in all_joiners if j.current_stage == "OFFER_CONFIRMED"]
    form11_due = [j for j in all_joiners if j.current_stage == "FORM11_DUE"]

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Active joiners", len(active))
    kpi2.metric("BG pending", len(bg_pending))
    kpi3.metric("DB pending", len(db_pending))
    kpi4.metric("Form 11 due", len(form11_due))

    st.write("")
    st.subheader("Candidates")

    filter_options = ["All", "New", "BG sent", "Confirmed", "Onboarding", "Joined", "Form 11 due", "Dropped"]
    filter_to_stages = {
        "All": None,
        "New": ["NEW"],
        "BG sent": ["BG_SENT", "BG_RECEIVED"],
        "Confirmed": ["OFFER_CONFIRMED", "DB_SENT", "DB_RECEIVED"],
        "Onboarding": ["ONBOARDING"],
        "Joined": ["JOINED", "FORMS_PENDING"],
        "Form 11 due": ["FORM11_DUE", "COMPLETED"],
        "Dropped": ["DROPPED"],
    }

    selected_filter = st.pills("Filter", options=filter_options, default="All", label_visibility="collapsed")
    selected_filter = selected_filter or "All"
    stages_to_show = filter_to_stages[selected_filter]

    visible = [j for j in all_joiners if stages_to_show is None or j.current_stage in stages_to_show]
    visible.sort(key=lambda j: j.doj or j.created_at)

    st.write("")

    if not visible:
        st.info("No candidates match this filter yet.")

    for j in visible:
        with st.container(border=True):
            col_name, col_desig, col_doj, col_stage, col_action = st.columns([2.5, 1.5, 1.3, 1.5, 2.2])
            with col_name:
                if st.button(j.full_name, key=f"open_{j.id}", use_container_width=True):
                    st.session_state["selected_joiner_id"] = j.id
                    st.switch_page("pages/3_Candidate_Detail.py")
            with col_desig:
                st.write(j.designation)
            with col_doj:
                st.write(j.doj.strftime("%d/%m/%Y") if j.doj else "-")
            with col_stage:
                st.markdown(stage_chip(j.current_stage), unsafe_allow_html=True)

            with col_action:
                stage = j.current_stage
                if stage == "NEW":
                    if st.button("Send BG →", key=f"action_{j.id}", use_container_width=True):
                        show_email_preview("bg_verification", _joiner_dict(j))
                elif stage == "BG_SENT":
                    if st.button("Mark BG received", key=f"action_{j.id}", use_container_width=True):
                        stage_service.mark_bg_received(j.id)
                        st.rerun()
                elif stage == "BG_RECEIVED":
                    st.caption("Awaiting HR")
                elif stage == "OFFER_CONFIRMED":
                    if st.button("Send DB form →", key=f"action_{j.id}", use_container_width=True):
                        show_email_preview("db_form", _joiner_dict(j))
                elif stage == "DB_SENT":
                    if st.button("Mark DB received", key=f"action_{j.id}", use_container_width=True):
                        stage_service.mark_db_received(j.id)
                        st.rerun()
                elif stage == "DB_RECEIVED":
                    if st.button("View details →", key=f"action_{j.id}", use_container_width=True):
                        st.session_state["selected_joiner_id"] = j.id
                        st.switch_page("pages/3_Candidate_Detail.py")
                elif stage == "ONBOARDING":
                    if st.button("View schedule →", key=f"action_{j.id}", use_container_width=True):
                        st.switch_page("pages/5_Scheduled.py")
                elif stage == "JOINED":
                    if st.button("Day-of checklist →", key=f"action_{j.id}", use_container_width=True):
                        st.session_state["selected_joiner_id"] = j.id
                        st.switch_page("pages/3_Candidate_Detail.py")
                elif stage == "FORMS_PENDING":
                    if st.button("Send forms →", key=f"action_{j.id}", use_container_width=True):
                        st.session_state["selected_joiner_id"] = j.id
                        st.switch_page("pages/3_Candidate_Detail.py")
                elif stage == "FORM11_DUE":
                    if st.button("Send Form 11 →", key=f"action_{j.id}", use_container_width=True):
                        show_email_preview("form11", _joiner_dict(j))
                elif stage == "COMPLETED":
                    st.caption("Done")
                elif stage == "DROPPED":
                    st.caption("Dropped" + (f" — {j.dropped_reason}" if j.dropped_reason else ""))
finally:
    session.close()
