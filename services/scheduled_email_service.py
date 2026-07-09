from datetime import datetime

from database.db import SessionLocal
from database.models import ActivityLog, Joiner, ScheduledEmail
from services import email_service, pdf_service, stage_service, template_engine

TEMPLATE_EMAIL_NUMBER = {
    "preonboard_story": 1,
    "preonboard_culture": 2,
    "preonboard_leadership": 3,
    "preonboard_joining": 4,
}


def schedule_email(joiner_id: int, template_key: str, scheduled_for: datetime):
    """Create or reschedule the pending send for this candidate + template.
    Only one not-yet-sent row can exist per joiner+template at a time."""
    session = SessionLocal()
    try:
        existing = (
            session.query(ScheduledEmail)
            .filter(
                ScheduledEmail.joiner_id == joiner_id,
                ScheduledEmail.template_key == template_key,
                ScheduledEmail.status == "scheduled",
            )
            .first()
        )
        if existing:
            existing.scheduled_for = scheduled_for
        else:
            session.add(
                ScheduledEmail(
                    joiner_id=joiner_id,
                    email_number=TEMPLATE_EMAIL_NUMBER.get(template_key),
                    template_key=template_key,
                    scheduled_for=scheduled_for,
                    status="scheduled",
                )
            )
        session.commit()
    finally:
        session.close()


def cancel_scheduled_email(scheduled_email_id: int):
    session = SessionLocal()
    try:
        row = session.get(ScheduledEmail, scheduled_email_id)
        if row and row.status == "scheduled":
            row.status = "cancelled"
            session.commit()
    finally:
        session.close()


def _send_one(session, row: ScheduledEmail) -> bool:
    """Render and send a single scheduled email. Returns True if it sent."""
    joiner = session.get(Joiner, row.joiner_id)
    if not joiner:
        row.status = "cancelled"
        return False

    context = dict(
        designation=joiner.designation,
        team_name=joiner.team_name,
        doj=joiner.doj.strftime("%d/%m/%Y") if joiner.doj else "",
        uan=joiner.uan or "",
    )
    rendered = template_engine.render_template(
        row.template_key, to_addr=joiner.candidate_email, name=joiner.full_name, **context
    )
    attachment_paths = (
        pdf_service.resolve_attachments(rendered.attachment_keys, name=joiner.full_name, **context)
        if rendered.attachment_keys
        else []
    )
    full_cc = ", ".join(filter(None, [rendered.mandatory_cc, rendered.additional_cc]))

    success, error = email_service.send_email(
        to=rendered.to_addr,
        cc=full_cc,
        subject=rendered.subject,
        body_html=rendered.body_html,
        attachment_paths=attachment_paths,
        joiner_id=joiner.id,
        template_key=row.template_key,
    )
    if success:
        row.status = "sent"
        row.sent_at = datetime.utcnow()
        return True

    row.status = "failed"
    session.add(
        ActivityLog(
            event_type="scheduled_email_failed",
            joiner_id=joiner.id,
            details=f"Scheduled {row.template_key} email failed to send: {error}",
            tone="danger",
        )
    )
    return False


def process_due_scheduled_emails():
    """Poll for scheduled emails whose time has come and send them. Never
    raises — called from the background scheduler, same pattern as sheet_sync."""
    session = SessionLocal()
    sent_pairs = []
    try:
        due = (
            session.query(ScheduledEmail)
            .filter(ScheduledEmail.status == "scheduled", ScheduledEmail.scheduled_for <= datetime.utcnow())
            .all()
        )
        for row in due:
            try:
                if _send_one(session, row):
                    sent_pairs.append((row.joiner_id, row.template_key))
            except Exception as e:
                row.status = "failed"
                session.add(
                    ActivityLog(
                        event_type="scheduled_email_failed",
                        joiner_id=row.joiner_id,
                        details=f"Scheduled {row.template_key} email failed to send: {e}",
                        tone="danger",
                    )
                )
        session.commit()
    finally:
        session.close()

    for joiner_id, template_key in sent_pairs:
        stage_service.advance_stage_after_send(joiner_id, template_key)
