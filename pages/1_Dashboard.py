import streamlit as st

import config
from components.email_preview import show_email_preview
from database.db import SessionLocal, init_db
from database.models import ActivityLog, Joiner
from services import stage_service
from services.scheduler import start_scheduler

init_db()
start_scheduler()

st.title("Dashboard")

_CHIP_COLORS = {
    "amber": "#F59E0B",
    "blue": "#3B82F6",
    "indigo": "#6366F1",
    "purple": "#A855F7",
    "violet": "#8B5CF6",
    "teal": "#14B8A6",
    "green": "#22C55E",
    "orange": "#F97316",
    "red": "#EF4444",
    "gray": "#6B7280",
}


def stage_chip(stage: str) -> str:
    color = _CHIP_COLORS.get(config.STAGE_COLORS.get(stage, "gray"), "#6B7280")
    return (
        f'<span style="background-color:{color}; color:white; padding:2px 10px; '
        f'border-radius:12px; font-size:0.8em; font-weight:600;">{stage}</span>'
    )


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

    st.divider()

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

    selected_filter = st.pills("Filter", options=filter_options, default="All")
    selected_filter = selected_filter or "All"
    stages_to_show = filter_to_stages[selected_filter]

    visible = [j for j in all_joiners if stages_to_show is None or j.current_stage in stages_to_show]
    visible.sort(key=lambda j: j.doj or j.created_at)

    if not visible:
        st.info("No candidates match this filter yet.")

    for j in visible:
        col_name, col_desig, col_doj, col_stage, col_action = st.columns([2.5, 1.5, 1.3, 1.5, 2.2])
        col_name.write(j.full_name)
        col_desig.write(j.designation)
        col_doj.write(j.doj.strftime("%d/%m/%Y") if j.doj else "-")
        col_stage.markdown(stage_chip(j.current_stage), unsafe_allow_html=True)

        with col_action:
            stage = j.current_stage
            if stage == "NEW":
                if st.button("Send BG →", key=f"action_{j.id}"):
                    show_email_preview("bg_verification", _joiner_dict(j))
            elif stage == "BG_SENT":
                if st.button("Mark BG received", key=f"action_{j.id}"):
                    stage_service.mark_bg_received(j.id)
                    st.rerun()
            elif stage == "BG_RECEIVED":
                st.caption("Awaiting HR")
            elif stage == "OFFER_CONFIRMED":
                if st.button("Send DB form →", key=f"action_{j.id}"):
                    show_email_preview("db_form", _joiner_dict(j))
            elif stage == "DB_SENT":
                if st.button("Mark DB received", key=f"action_{j.id}"):
                    stage_service.mark_db_received(j.id)
                    st.rerun()
            elif stage == "DB_RECEIVED":
                if st.button("View details →", key=f"action_{j.id}"):
                    st.session_state["selected_joiner_id"] = j.id
                    st.switch_page("pages/3_Candidate_Detail.py")
            elif stage == "ONBOARDING":
                if st.button("View schedule →", key=f"action_{j.id}"):
                    st.switch_page("pages/5_Scheduled.py")
            elif stage == "JOINED":
                if st.button("Day-of checklist →", key=f"action_{j.id}"):
                    st.session_state["selected_joiner_id"] = j.id
                    st.switch_page("pages/3_Candidate_Detail.py")
            elif stage == "FORMS_PENDING":
                if st.button("Send forms →", key=f"action_{j.id}"):
                    st.session_state["selected_joiner_id"] = j.id
                    st.switch_page("pages/3_Candidate_Detail.py")
            elif stage == "FORM11_DUE":
                if st.button("Send Form 11 →", key=f"action_{j.id}"):
                    show_email_preview("form11", _joiner_dict(j))
            elif stage == "COMPLETED":
                st.caption("Done")
            elif stage == "DROPPED":
                st.caption("Dropped" + (f" — {j.dropped_reason}" if j.dropped_reason else ""))
finally:
    session.close()
