import base64
import mimetypes
import os
import smtplib
import threading
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

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


def _split_addresses(value: str) -> list[str]:
    return [addr.strip() for addr in (value or "").split(",") if addr.strip()]


def send_via_smtp(to: str, cc: str, subject: str, body_html: str, attachments: list[str] | None = None):
    """Send one email via Outlook's SMTP AUTH endpoint using a mailbox app
    password. No Azure app registration needed — just IT enabling SMTP AUTH
    for the mailbox and an app password generated in the M365 account portal."""
    import config

    if not config.SMTP_APP_PASSWORD:
        return False, "SMTP_APP_PASSWORD not set in .env yet."

    to_list = _split_addresses(to)
    cc_list = _split_addresses(cc)

    msg = MIMEMultipart()
    msg["From"] = config.SMTP_USERNAME
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))

    for path in attachments or []:
        with open(path, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(path))
        part["Content-Disposition"] = f'attachment; filename="{os.path.basename(path)}"'
        msg.attach(part)

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_APP_PASSWORD)
            server.sendmail(config.SMTP_USERNAME, to_list + cc_list, msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


def send_via_graph(to: str, cc: str, subject: str, body_html: str, attachments: list[str] | None = None):
    """Send one email via Microsoft Graph, using the Outlook account connected
    through the device-code sign-in flow. Works without desktop Outlook."""
    from services import graph_auth

    token = graph_auth.get_access_token_silent()
    if not token:
        return False, 'Outlook is not connected — go to the Dashboard and click "Connect Outlook".'

    message = {
        "subject": subject,
        "body": {"contentType": "HTML", "content": body_html},
        "toRecipients": [{"emailAddress": {"address": addr}} for addr in _split_addresses(to)],
        "ccRecipients": [{"emailAddress": {"address": addr}} for addr in _split_addresses(cc)],
    }

    file_attachments = []
    for path in attachments or []:
        with open(path, "rb") as f:
            content = f.read()
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        file_attachments.append(
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": os.path.basename(path),
                "contentType": content_type,
                "contentBytes": base64.b64encode(content).decode("ascii"),
            }
        )
    if file_attachments:
        message["attachments"] = file_attachments

    try:
        resp = requests.post(
            "https://graph.microsoft.com/v1.0/me/sendMail",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"message": message, "saveToSentItems": "true"},
            timeout=30,
        )
        if resp.status_code == 202:
            return True, None
        return False, f"Graph API error {resp.status_code}: {resp.text[:300]}"
    except requests.RequestException as e:
        return False, str(e)


def _pick_send_function():
    import config
    from services import graph_auth

    if config.SMTP_APP_PASSWORD:
        return send_via_smtp
    if config.GRAPH_CLIENT_ID and graph_auth.get_connected_account():
        return send_via_graph
    return send_via_outlook


def send_email(
    to: str,
    cc: str,
    subject: str,
    body_html: str,
    attachment_paths: list[str] | None = None,
    joiner_id: int | None = None,
    template_key: str | None = None,
):
    """Send an email with one automatic retry after 30 seconds on failure, logging the outcome.
    Prefers SMTP (app password) if configured, then Microsoft Graph if connected via the
    device-code flow, otherwise falls back to the desktop Outlook COM automation."""
    send_fn = _pick_send_function()
    success, error = send_fn(to, cc, subject, body_html, attachment_paths)

    if not success:
        time.sleep(30)
        success, error = send_fn(to, cc, subject, body_html, attachment_paths)

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
