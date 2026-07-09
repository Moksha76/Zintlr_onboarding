from datetime import datetime

from database.db import SessionLocal
from database.models import ActivityLog, EmailLog, Joiner, ScheduledEmail

# Section 9 — stage transitions triggered by a successful email send.
# "from" of None means the send never gates on / advances current_stage.
_SEND_TRANSITIONS = {
    "bg_verification": {"from": ["NEW"], "to": "BG_SENT", "timestamp_field": "bg_sent_at"},
    "db_form": {"from": ["OFFER_CONFIRMED"], "to": "DB_SENT", "timestamp_field": "db_sent_at"},
    "preonboard_story": {"from": ["DB_RECEIVED", "DB_SENT"], "to": "ONBOARDING", "timestamp_field": None},
    "preonboard_culture": {"from": ["ONBOARDING"], "to": "ONBOARDING", "timestamp_field": None},
    "preonboard_leadership": {"from": ["ONBOARDING"], "to": "ONBOARDING", "timestamp_field": None},
    "preonboard_joining": {"from": ["ONBOARDING"], "to": "ONBOARDING", "timestamp_field": None},
    "mbti": {"from": ["JOINED"], "to": "FORMS_PENDING", "timestamp_field": "mbti_sent_at"},
    "insurance": {"from": ["JOINED", "FORMS_PENDING"], "to": "FORMS_PENDING", "timestamp_field": "insurance_sent_at"},
    "form11": {"from": ["FORM11_DUE", "FORMS_PENDING"], "to": "COMPLETED", "timestamp_field": "form11_sent_at"},
    "obligation": {"from": None, "to": None, "timestamp_field": "obligation_sent_at"},
}

# Templates enabled per stage (Candidate Detail action buttons)
TEMPLATE_ENABLED_STAGES = {
    "bg_verification": ["NEW"],
    "db_form": ["OFFER_CONFIRMED"],
    "preonboard_story": ["DB_RECEIVED", "DB_SENT", "ONBOARDING"],
    "preonboard_culture": ["ONBOARDING"],
    "preonboard_leadership": ["ONBOARDING"],
    "preonboard_joining": ["ONBOARDING"],
    "mbti": ["JOINED", "FORMS_PENDING"],
    "insurance": ["JOINED", "FORMS_PENDING"],
    "form11": ["FORM11_DUE", "FORMS_PENDING"],
    "obligation": None,  # always available, manual send only
}


def advance_stage_after_send(joiner_id: int, template_key: str, extra_fields: dict | None = None):
    session = SessionLocal()
    try:
        joiner = session.get(Joiner, joiner_id)
        if not joiner:
            return
        for field, value in (extra_fields or {}).items():
            setattr(joiner, field, value)

        rule = _SEND_TRANSITIONS.get(template_key)
        if rule:
            if rule["timestamp_field"]:
                setattr(joiner, rule["timestamp_field"], datetime.utcnow())
            if rule["from"] is not None and joiner.current_stage in rule["from"]:
                joiner.current_stage = rule["to"]
                session.add(
                    ActivityLog(
                        event_type="stage_change",
                        joiner_id=joiner.id,
                        details=f"{template_key} sent — stage advanced to {rule['to']}",
                        tone="ok",
                    )
                )

        session.add(
            ActivityLog(
                event_type="email_sent",
                joiner_id=joiner.id,
                details=f"{template_key} email sent to {joiner.full_name}",
                tone="ok",
            )
        )
        candidate_email = joiner.candidate_email
        session.commit()
    finally:
        session.close()

    _sync_send_to_sheet(candidate_email, template_key)


def _sync_send_to_sheet(candidate_email: str, template_key: str):
    from services import sheet_sync

    today = datetime.utcnow().strftime("%d/%m/%Y")
    if template_key == "bg_verification":
        sheet_sync.update_sheet_row(candidate_email, "bg_sent", "Yes")
        sheet_sync.update_sheet_row(candidate_email, "bg_sent_date", today)
    elif template_key == "db_form":
        sheet_sync.update_sheet_row(candidate_email, "db_sent", "Yes")
        sheet_sync.update_sheet_row(candidate_email, "db_sent_date", today)


def mark_bg_received(joiner_id: int):
    _set_stage(joiner_id, from_stages=["BG_SENT"], to_stage="BG_RECEIVED", timestamp_field="bg_received_at")


def simulate_offer_confirmation(joiner_id: int):
    _set_stage(
        joiner_id, from_stages=["BG_RECEIVED"], to_stage="OFFER_CONFIRMED", timestamp_field="offer_confirmed_at"
    )


def mark_db_received(joiner_id: int):
    _set_stage(joiner_id, from_stages=["DB_SENT"], to_stage="DB_RECEIVED", timestamp_field="db_received_at")


def mark_joined(joiner_id: int):
    _set_stage(joiner_id, from_stages=["ONBOARDING"], to_stage="JOINED", timestamp_field=None)


def delete_candidate(joiner_id: int):
    """Permanently remove a candidate and all their records (email log,
    activity log, scheduled emails). Irreversible — for removing test/mistake
    entries, not for real candidates who didn't proceed (use mark_dropped)."""
    session = SessionLocal()
    try:
        session.query(EmailLog).filter(EmailLog.joiner_id == joiner_id).delete()
        session.query(ActivityLog).filter(ActivityLog.joiner_id == joiner_id).delete()
        session.query(ScheduledEmail).filter(ScheduledEmail.joiner_id == joiner_id).delete()
        joiner = session.get(Joiner, joiner_id)
        if joiner:
            session.delete(joiner)
        session.commit()
    finally:
        session.close()


def mark_dropped(joiner_id: int, reason: str = ""):
    session = SessionLocal()
    try:
        joiner = session.get(Joiner, joiner_id)
        if not joiner:
            return
        joiner.current_stage = "DROPPED"
        joiner.dropped_at = datetime.utcnow()
        joiner.dropped_reason = reason
        session.add(
            ActivityLog(
                event_type="stage_change",
                joiner_id=joiner.id,
                details=f"Candidate dropped" + (f": {reason}" if reason else ""),
                tone="danger",
            )
        )
        session.commit()
    finally:
        session.close()


def _set_stage(joiner_id: int, from_stages: list[str], to_stage: str, timestamp_field: str | None):
    session = SessionLocal()
    try:
        joiner = session.get(Joiner, joiner_id)
        if not joiner or joiner.current_stage not in from_stages:
            return
        joiner.current_stage = to_stage
        if timestamp_field:
            setattr(joiner, timestamp_field, datetime.utcnow())
        session.add(
            ActivityLog(
                event_type="stage_change",
                joiner_id=joiner.id,
                details=f"Stage advanced to {to_stage}",
                tone="ok",
            )
        )
        session.commit()
    finally:
        session.close()


_CHECKLIST_SHEET_COLUMN_KEYS = {
    "agreement_signed": "agreement_signed",
    "laptop_assigned": "laptop_assigned",
    "sim_assigned": "sim_assigned",
    "kit_handed_over": "kit_ready",
}


def update_checklist_field(joiner_id: int, field: str, value, timestamp_field: str | None = None):
    """Generic checklist checkbox updater. Auto-advances to FORMS_PENDING once
    the required day-of-joining items are all complete (Section 9)."""
    session = SessionLocal()
    try:
        joiner = session.get(Joiner, joiner_id)
        if not joiner:
            return
        setattr(joiner, field, value)
        if timestamp_field:
            setattr(joiner, timestamp_field, datetime.utcnow() if value else None)
        session.add(
            ActivityLog(
                event_type="checklist",
                joiner_id=joiner.id,
                details=f"{field} set to {value}",
                tone="info",
            )
        )

        required = [joiner.agreement_signed, joiner.laptop_assigned, joiner.kit_handed_over, joiner.tshirt_handed_over]
        if joiner.sim_required:
            required.append(joiner.sim_assigned)
        if all(required) and joiner.current_stage == "JOINED":
            joiner.current_stage = "FORMS_PENDING"
            session.add(
                ActivityLog(
                    event_type="stage_change",
                    joiner_id=joiner.id,
                    details="All day-of-joining items complete — stage advanced to FORMS_PENDING",
                    tone="ok",
                )
            )
        candidate_email = joiner.candidate_email
        tshirt_size = joiner.tshirt_size
        session.commit()
    finally:
        session.close()

    _sync_checklist_to_sheet(candidate_email, field, value, tshirt_size)


def _sync_checklist_to_sheet(candidate_email: str, field: str, value, tshirt_size: str | None):
    from services import sheet_sync

    if field == "tshirt_handed_over":
        if value and tshirt_size:
            sheet_sync.update_sheet_row(candidate_email, "tshirt_size", tshirt_size)
        return

    column_key = _CHECKLIST_SHEET_COLUMN_KEYS.get(field)
    if column_key:
        sheet_sync.update_sheet_row(candidate_email, column_key, "Yes" if value else "No")
