import threading
import time

from database.db import SessionLocal
from database.models import EmailLog


def send_via_outlook(to: str, cc: str, subject: str, body_html: str, attachments: list[str] | None = None):
    """Send one email through the local Outlook desktop app via COM automation.

    Only works on Windows with Outlook installed and signed in.
    """
    try:
        import win32com.client
    except ImportError:
        return False, "Outlook is not available on this machine (pywin32/Outlook desktop required)."

    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = to
        mail.CC = cc
        mail.Subject = subject
        mail.HTMLBody = body_html
        for path in attachments or []:
            mail.Attachments.Add(path)
        mail.Send()
        return True, None
    except Exception as e:
        return False, str(e)


def send_email(
    to: str,
    cc: str,
    subject: str,
    body_html: str,
    attachment_paths: list[str] | None = None,
    joiner_id: int | None = None,
    template_key: str | None = None,
):
    """Send an email with one automatic retry after 30 seconds on failure, logging the outcome."""
    success, error = send_via_outlook(to, cc, subject, body_html, attachment_paths)

    if not success:
        time.sleep(30)
        success, error = send_via_outlook(to, cc, subject, body_html, attachment_paths)

    session = SessionLocal()
    try:
        from datetime import datetime

        session.add(
            EmailLog(
                joiner_id=joiner_id,
                template_key=template_key,
                to_addr=to,
                cc_addr=cc,
                subject=subject,
                sent_at=datetime.utcnow() if success else None,
                status="sent" if success else "failed",
                error_msg=error,
            )
        )
        session.commit()
    finally:
        session.close()

    return success, error


def send_low_stock_alert(item_label: str, quantity: int, threshold: int):
    """Notify HR by email that an inventory item has hit its reorder point.
    Fires in a background thread so the action that triggered it (e.g. a
    checklist click) never blocks waiting on Outlook's retry."""
    import config

    subject = f"Low stock alert — {item_label}"
    body_html = (
        f"<p>{item_label} is running low: <b>{quantity}</b> left "
        f"(reorder threshold: {threshold}).</p><p>Please restock soon.</p>"
    )
    threading.Thread(
        target=send_email,
        kwargs=dict(to=config.SENDER_EMAIL, cc="", subject=subject, body_html=body_html),
        daemon=True,
    ).start()
