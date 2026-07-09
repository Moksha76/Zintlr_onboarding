from datetime import date, datetime

import streamlit as st

import config
from components.email_preview import show_email_preview
from components.theme import inject_theme, stage_badge_html
from database.db import SessionLocal, init_db
from database.models import ActivityLog, EmailTemplate, Inventory, Joiner, ScheduledEmail
from services import scheduled_email_service, stage_service
from services.scheduler import start_scheduler

init_db()
start_scheduler()
inject_theme()

_STAGE_BADGE_COLORS = {
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

    initials = "".join(part[0].upper() for part in joiner.full_name.split()[:2]) or "?"
    badge_color = _STAGE_BADGE_COLORS.get(config.STAGE_COLORS.get(joiner.current_stage, "gray"), "#4B5563")

    with st.container(border=True):
        hdr_avatar, hdr_info = st.columns([0.12, 0.88])
        with hdr_avatar:
            st.markdown(
                f'<div style="width:56px; height:56px; border-radius:50%; background:#4B3F91; '
                f'color:white; display:flex; align-items:center; justify-content:center; '
                f'font-weight:800; font-size:1.1em;">{initials}</div>',
                unsafe_allow_html=True,
            )
        with hdr_info:
            st.markdown(f"### {joiner.full_name}")
            st.caption(f"{joiner.candidate_email}  ·  {joiner.designation}  ·  {doj_text}")
            st.markdown(stage_badge_html(joiner.current_stage.replace("_", " "), badge_color), unsafe_allow_html=True)

    st.write("")

    main_col, side_col = st.columns([2.2, 1])

    with main_col:
        with st.container(border=True):
            st.subheader("Send an email")
            enabled_stages_map = stage_service.TEMPLATE_ENABLED_STAGES
            cols = st.columns(3)
            for i, (template_key, label) in enumerate(TEMPLATE_LABELS.items()):
                if template_key.startswith("preonboard_"):
                    continue  # sent via the Scheduled flow (Phase 5), not a direct button here
                allowed_stages = enabled_stages_map.get(template_key)
                is_enabled = allowed_stages is None or joiner.current_stage in allowed_stages
                with cols[i % 3]:
                    if st.button(
                        label, key=f"send_{template_key}", disabled=not is_enabled, use_container_width=True
                    ):
                        show_email_preview(template_key, _joiner_dict(joiner))

        st.write("")
        with st.container(border=True):
            st.subheader("Stage actions")
            action_cols = st.columns(4)
            with action_cols[0]:
                if st.button(
                    "Mark BG received", disabled=joiner.current_stage != "BG_SENT", use_container_width=True
                ):
                    stage_service.mark_bg_received(joiner.id)
                    st.rerun()
            with action_cols[1]:
                if st.button(
                    "Simulate HR offer confirmation (test)",
                    disabled=joiner.current_stage != "BG_RECEIVED",
                    use_container_width=True,
                ):
                    stage_service.simulate_offer_confirmation(joiner.id)
                    st.rerun()
            with action_cols[2]:
                if st.button(
                    "Mark DB received", disabled=joiner.current_stage != "DB_SENT", use_container_width=True
                ):
                    stage_service.mark_db_received(joiner.id)
                    st.rerun()
            with action_cols[3]:
                can_mark_joined = (
                    joiner.current_stage == "ONBOARDING" and joiner.doj and joiner.doj <= date.today()
                )
                if st.button("Mark joined", disabled=not can_mark_joined, use_container_width=True):
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

        st.write("")
        with st.container(border=True):
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
                index=["S", "M", "L", "XL"].index(joiner.tshirt_size)
                if joiner.tshirt_size in ["S", "M", "L", "XL"]
                else 1,
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

        st.write("")
        with st.container(border=True):
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
        with st.container(border=True):
            st.subheader("Candidate info")
            st.write(f"**Email:** {joiner.candidate_email}")
            st.write(f"**Designation:** {joiner.designation}")
            st.write(f"**Team:** {joiner.team_name or '-'}")
            st.write(f"**DOJ:** {doj_text}")
            st.write(f"**SIM required:** {'Yes' if joiner.sim_required else 'No'}")
            st.write(f"**UAN:** {joiner.uan or '-'}")

        st.write("")
        with st.container(border=True):
            st.subheader("HR sheet sync")
            if joiner.sheet_row_index:
                st.caption(
                    f"Added from the HR sheet (row {joiner.sheet_row_index}). Status updates sync automatically."
                )
            else:
                st.caption("Added manually via Add Joiner — not linked to a sheet row.")

        st.write("")
        with st.container(border=True):
            st.subheader("Scheduled emails")
            scheduled_rows = (
                session.query(ScheduledEmail)
                .filter(ScheduledEmail.joiner_id == joiner.id)
                .order_by(ScheduledEmail.scheduled_for)
                .all()
            )
            if not scheduled_rows:
                st.caption("No pre-onboarding emails scheduled yet — set them up on the Scheduled page.")
            else:
                display_names = {
                    t.template_key: t.display_name
                    for t in session.query(EmailTemplate).filter(EmailTemplate.active.is_(True)).all()
                }
                status_emoji = {"scheduled": "🕒", "sent": "🟢", "failed": "🔴", "cancelled": "⚪"}
                for row in scheduled_rows:
                    label = display_names.get(row.template_key, row.template_key)
                    when = row.scheduled_for.strftime("%d/%m/%Y %H:%M")
                    st.write(f"{status_emoji.get(row.status, '⚪')} {label} — {when} ({row.status})")
                    if row.status == "scheduled":
                        if st.button("Cancel", key=f"cancel_sched_{row.id}"):
                            scheduled_email_service.cancel_scheduled_email(row.id)
                            st.rerun()

    st.write("")
    with st.container(border=True):
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
