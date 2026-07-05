import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

import config
from services.template_engine import render_document

LETTERHEAD_FOOTER = (
    "Zintlr Private Limited<br/>"
    "No. 7, 7th Cross, Hebbal Ganganagara Layout, Ganganagar, RT Nagar, Bengaluru - 560032<br/>"
    "hr@zintlr.com | +91 83107 60719"
)

_styles = getSampleStyleSheet()
_body_style = ParagraphStyle(
    "DocBody",
    parent=_styles["Normal"],
    fontSize=11,
    leading=16,
    spaceAfter=10,
)
_footer_style = ParagraphStyle(
    "DocFooter",
    parent=_styles["Normal"],
    fontSize=8,
    leading=11,
    textColor="#555555",
)


def _draw_footer(canvas, doc):
    canvas.saveState()
    footer = Paragraph(LETTERHEAD_FOOTER, _footer_style)
    width, height = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, 1.2 * cm)
    canvas.restoreState()


def render_text_to_pdf(body_text: str, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    story = []
    for paragraph in body_text.split("\n\n"):
        text = paragraph.strip().replace("\n", "<br/>")
        if text:
            story.append(Paragraph(text, _body_style))
        story.append(Spacer(1, 4))
    doc.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)


def generate_declaration_pdf(name: str) -> str:
    """Render the BG declaration document template for `name` and save it as a PDF."""
    body_text = render_document("bg_declaration", name=name)
    name_slug = name.lower().replace(" ", "_").strip()
    output_path = os.path.join(config.GENERATED_DIR, f"declaration_{name_slug}.pdf")
    os.makedirs(config.GENERATED_DIR, exist_ok=True)
    render_text_to_pdf(body_text, output_path)
    return output_path


def resolve_attachments(attachment_keys: list[str], name: str | None = None) -> list[str]:
    """Turn logical attachment keys from an email template into real file paths."""
    paths = []
    for key in attachment_keys:
        if key == "declaration":
            paths.append(generate_declaration_pdf(name))
        elif key in config.STATIC_ATTACHMENTS:
            paths.append(config.STATIC_ATTACHMENTS[key])
        else:
            raise ValueError(f"Unknown attachment key '{key}'")
    return paths
