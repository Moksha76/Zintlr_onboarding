from datetime import date, datetime

import streamlit as st

import config
from components.email_preview import show_email_preview
from database.db import SessionLocal, init_db
from database.models import ActivityLog, Inventory, Joiner
from services import stage_service
from services.scheduler import start_scheduler

init_db()
start_scheduler()

TEMPLATE_LABELS = {
    "bg_verification": "Send BG",
    "db_form": "Send DB form",
    "preonboard_story": "Send Pre-onboarding: Story",
    "preonboard_culture": "Send Pre-onboarding: Culture",
    "preonboard_leadership": "Send Pre-onboarding: Leadership",
    "preonboard_joining": "Send Pre-onboarding: Joining",
    "mbti": "Send MBTI",
    "insurance": "Send Insurance",
    "form11": "Send Form 11",
    "obligation": "Send Obligation",
}


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


def _decrement_inventory(session, item_type: str, size: str | None = None):
    query = session.query(Inventory).filter(Inventory.item_type == item_type)
    if size:
        query = query.filter(Inventory.size == size)
    inv = query.first()
    if inv and inv.quantity > 0:
        inv.quantity -= 1
        session.commit()


def _on_checkbox_change(joiner_id: int, field: str, timestamp_field: str, key: str):
    new_value = st.session_state[key]
    stage_service.update_checklist_field(joiner_id, field, new_value, timestamp_field)


def _on_kit_change(joiner_id: int, key: str):
    new_value = st.session_state[key]
    stage_service.update_checklist_field(joiner_id, "kit_handed_over", new_value, "kit_handed_over_at")
    if new_value:
        session = SessionLocal()
        try:
            _decrement_inventory(session, "kit")
        finally:
            session.close()


def _on_tshirt_change(joiner_id: int, size_key: str, key: str):
    new_value = st.session_state[key]
    size = st.session_state.get(size_key)
    stage_service.update_checklist_field(joiner_id, "tshirt_handed_over", new_value, "tshirt_handed_over_at")
    if new_value and size:
        session = SessionLocal()
        try:
            joiner = session.get(Joiner, joiner_id)
            joiner.tshirt_size = size
            session.commit()
            _decrement_inventory(session, "tshirt", size)
        finally:
            session.close()


def _on_asset_tag_change(joiner_id: int, key: str):
    session = SessionLocal()
    try:
        joiner = session.get(Joiner, joiner_id)
        joiner.laptop_asset_tag = st.session_state[key]
        session.commit()
    finally:
        session.close()


def _on_tshirt_size_change(joiner_id: int, key: str):
    session = SessionLocal()
    try:
        joiner = session.get(Joiner, joiner_id)
        joiner.tshirt_size = st.session_state[key]
        session.commit()
    finally:
        session.close()


st.title("Candidate Detail")

if st.button("← Back to Dashboard"):
    st.switch_page("pages/1_Dashboard.py")

joiner_id = st.session_state.get("selected_joiner_id")

if not joiner_id:
    st.info("Select a candidate from the Dashboard to view details.")
    st.stop()

session = SessionLocal()
try:
    joiner = session.get(Joiner, joiner_id)
    if not joiner:
        st.error("Candidate not found.")
        st.stop()

    days_to_doj = (joiner.doj - date.today()).days if joiner.doj else None
    doj_text = joiner.doj.strftime("%d/%m/%Y") if joiner.doj else "-"
    if days_to_doj is not None:
        if days_to_doj > 0:
            doj_text += f"  ·  {days_to_doj} day(s) until joining"
        elif days_to_doj == 0:
            doj_text += "  ·  Joining today"
        else:
            doj_text += f"  ·  Joined {-days_to_doj} day(s) ago"

    st.header(joiner.full_name)
    st.write(f"{joiner.candidate_email}  ·  {joiner.designation}  ·  {doj_text}")
    st.markdown(f"**Stage:** {joiner.current_stage}")

    main_col, side_col = st.columns([2.2, 1])

    with main_col:
        st.subheader("Send an email")
        enabled_stages_map = stage_service.TEMPLATE_ENABLED_STAGES
        cols = st.columns(3)
        for i, (template_key, label) in enumerate(TEMPLATE_LABELS.items()):
            if template_key.startswith("preonboard_"):
                continue  # sent via the Scheduled flow (Phase 5), not a direct button here
            allowed_stages = enabled_stages_map.get(template_key)
            is_enabled = allowed_stages is None or joiner.current_stage in allowed_stages
            with cols[i % 3]:
                if st.button(label, key=f"send_{template_key}", disabled=not is_enabled):
                    show_email_preview(template_key, _joiner_dict(joiner))

        st.divider()
        st.subheader("Stage actions")
        action_cols = st.columns(4)
        with action_cols[0]:
            if st.button("Mark BG received", disabled=joiner.current_stage != "BG_SENT"):
                stage_service.mark_bg_received(joiner.id)
                st.rerun()
        with action_cols[1]:
            if st.button(
                "Simulate HR offer confirmation (test)", disabled=joiner.current_stage != "BG_RECEIVED"
            ):
                stage_service.simulate_offer_confirmation(joiner.id)
                st.rerun()
        with action_cols[2]:
            if st.button("Mark DB received", disabled=joiner.current_stage != "DB_SENT"):
                stage_service.mark_db_received(joiner.id)
                st.rerun()
        with action_cols[3]:
            can_mark_joined = joiner.current_stage == "ONBOARDING" and joiner.doj and joiner.doj <= date.today()
            if st.button("Mark joined", disabled=not can_mark_joined):
                stage_service.mark_joined(joiner.id)
                st.rerun()

        if joiner.current_stage not in ("COMPLETED", "DROPPED"):
            with st.expander("Drop this candidate (test-only override)"):
                reason = st.text_input("Reason (optional)", key="drop_reason")
                if st.button("Mark as Dropped"):
                    stage_service.mark_dropped(joiner.id, reason)
                    st.rerun()

        with st.expander("Delete this candidate permanently"):
            st.warning(
                "This permanently erases the candidate and all their history (emails, activity, "
                "schedule) — it cannot be undone. Use this for test/mistake entries only. For a "
                "real candidate who didn't proceed, use \"Drop\" above instead so the record is kept."
            )
            confirm_name = st.text_input(
                f"Type the candidate's full name to confirm: {joiner.full_name}", key="delete_confirm_name"
            )
            if st.button("Delete permanently", disabled=confirm_name != joiner.full_name):
                stage_service.delete_candidate(joiner.id)
                st.session_state.pop("selected_joiner_id", None)
                st.success("Candidate deleted.")
                st.switch_page("pages/1_Dashboard.py")

        st.divider()
        st.subheader("Day-of-joining checklist")

        st.checkbox(
            "Employee agreement signed",
            value=joiner.agreement_signed,
            key=f"agreement_{joiner.id}",
            on_change=_on_checkbox_change,
            args=(joiner.id, "agreement_signed", "agreement_signed_at", f"agreement_{joiner.id}"),
        )

        st.checkbox(
            "Laptop assigned",
            value=joiner.laptop_assigned,
            key=f"laptop_{joiner.id}",
            on_change=_on_checkbox_change,
            args=(joiner.id, "laptop_assigned", "laptop_assigned_at", f"laptop_{joiner.id}"),
        )
        if joiner.laptop_assigned:
            st.text_input(
                "Laptop asset tag",
                value=joiner.laptop_asset_tag or "",
                key=f"asset_tag_{joiner.id}",
                on_change=_on_asset_tag_change,
                args=(joiner.id, f"asset_tag_{joiner.id}"),
            )

        if joiner.sim_required:
            st.checkbox(
                "SIM assigned",
                value=joiner.sim_assigned,
                key=f"sim_{joiner.id}",
                on_change=_on_checkbox_change,
                args=(joiner.id, "sim_assigned", "sim_assigned_at", f"sim_{joiner.id}"),
            )

        st.checkbox(
            "Kit handed over",
            value=joiner.kit_handed_over,
            key=f"kit_{joiner.id}",
            on_change=_on_kit_change,
            args=(joiner.id, f"kit_{joiner.id}"),
        )

        st.selectbox(
            "T-shirt size",
            options=["S", "M", "L", "XL"],
            index=["S", "M", "L", "XL"].index(joiner.tshirt_size) if joiner.tshirt_size in ["S", "M", "L", "XL"] else 1,
            key=f"tshirt_size_{joiner.id}",
            on_change=_on_tshirt_size_change,
            args=(joiner.id, f"tshirt_size_{joiner.id}"),
        )
        st.checkbox(
            "T-shirt handed over",
            value=joiner.tshirt_handed_over,
            key=f"tshirt_{joiner.id}",
            on_change=_on_tshirt_change,
            args=(joiner.id, f"tshirt_size_{joiner.id}", f"tshirt_{joiner.id}"),
        )

        st.divider()
        st.subheader("Other onboarding steps")
        st.caption(
            "Tracked here for your records. HR notifications for these will be wired up once the "
            "Google Sheets sync (Phase 4) and email sending are ready."
        )

        other_items = [
            ("Teams & Outlook access set up", "teams_outlook_done", "teams_outlook_done_at"),
            ("zNexus onboarding done", "znexus_done", "znexus_done_at"),
            ("Zintlr internal tool onboarding done", "zintlr_tool_done", "zintlr_tool_done_at"),
            ("Scrut onboarding done", "scrut_done", "scrut_done_at"),
            ("Salary account discussed", "salary_account_discussed", "salary_account_discussed_at"),
            ("Biometric access done", "biometric_access_done", "biometric_access_done_at"),
        ]
        for label, field, ts_field in other_items:
            st.checkbox(
                label,
                value=getattr(joiner, field),
                key=f"{field}_{joiner.id}",
                on_change=_on_checkbox_change,
                args=(joiner.id, field, ts_field, f"{field}_{joiner.id}"),
            )

    with side_col:
        st.subheader("Candidate info")
        st.write(f"**Email:** {joiner.candidate_email}")
        st.write(f"**Designation:** {joiner.designation}")
        st.write(f"**Team:** {joiner.team_name or '-'}")
        st.write(f"**DOJ:** {doj_text}")
        st.write(f"**SIM required:** {'Yes' if joiner.sim_required else 'No'}")
        st.write(f"**UAN:** {joiner.uan or '-'}")

        st.divider()
        st.subheader("HR sheet sync")
        if joiner.sheet_row_index:
            st.caption(f"Added from the HR sheet (row {joiner.sheet_row_index}). Status updates sync automatically.")
        else:
            st.caption("Added manually via Add Joiner — not linked to a sheet row.")

        st.divider()
        st.subheader("Scheduled emails")
        st.caption("Will show the pre-onboarding schedule once Phase 5 is built.")

    st.divider()
    st.subheader("Activity timeline")
    logs = (
        session.query(ActivityLog)
        .filter(ActivityLog.joiner_id == joiner.id)
        .order_by(ActivityLog.timestamp.desc())
        .all()
    )
    if not logs:
        st.caption("No activity yet.")
    for log in logs:
        tone_emoji = {"ok": "🟢", "warn": "🟠", "danger": "🔴", "info": "⚪"}.get(log.tone, "⚪")
        st.write(f"{tone_emoji} {log.timestamp.strftime('%d/%m/%Y %H:%M')} — {log.details}")
finally:
    session.close()
