import json
from dataclasses import dataclass, field

from jinja2 import Template

import config
from database.db import SessionLocal
from database.models import EmailTemplate


@dataclass
class RenderedEmail:
    template_key: str
    subject: str
    body_html: str
    to_addr: str
    mandatory_cc: str
    additional_cc: str
    attachment_keys: list = field(default_factory=list)


def _base_context(name: str | None = None, **extra):
    context = dict(extra)
    context["links"] = config.LINKS
    context["signature"] = config.SIGNATURE_BLOCK
    if name:
        context["name"] = name
        context["name_slug"] = name.lower().replace(" ", "_").strip()
    return context


def render_template(template_key: str, to_addr: str = "", **context) -> RenderedEmail:
    """Render an email template with the given context.

    context typically includes: name, designation, team_name, doj, uan,
    bg_deadline_date, bg_deadline_time.
    """
    session = SessionLocal()
    try:
        template = (
            session.query(EmailTemplate)
            .filter(EmailTemplate.template_key == template_key, EmailTemplate.active.is_(True))
            .order_by(EmailTemplate.version.desc())
            .first()
        )
        if template is None:
            raise ValueError(f"No active template found for key '{template_key}'")

        full_context = _base_context(**context)
        rendered_subject = Template(template.subject).render(**full_context)
        rendered_body = Template(template.body_html).render(**full_context)
        attachment_keys = json.loads(template.attachments_json) if template.attachments_json else []

        return RenderedEmail(
            template_key=template_key,
            subject=rendered_subject,
            body_html=rendered_body,
            to_addr=to_addr,
            mandatory_cc=config.HR_ADMIN_EMAIL,
            additional_cc=template.cc_default or "",
            attachment_keys=attachment_keys,
        )
    finally:
        session.close()


def render_document(document_key: str, **context) -> str:
    """Render a plain-text document template (e.g. the BG declaration) to a string."""
    from database.models import DocumentTemplate

    session = SessionLocal()
    try:
        document = (
            session.query(DocumentTemplate)
            .filter(DocumentTemplate.document_key == document_key, DocumentTemplate.active.is_(True))
            .order_by(DocumentTemplate.version.desc())
            .first()
        )
        if document is None:
            raise ValueError(f"No active document template found for key '{document_key}'")

        full_context = _base_context(**context)
        return Template(document.body_text).render(**full_context)
    finally:
        session.close()
