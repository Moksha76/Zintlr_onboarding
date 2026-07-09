import os

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

import config
from services.template_engine import render_document

LETTERHEAD_TITLE = "ZINTLR"
LETTERHEAD_SUBTITLE = "Private Limited"
LETTERHEAD_CIN = "CIN: U72900KA2022PTC165582"
LETTERHEAD_WEBSITE = "www.zintlr.com"
LETTERHEAD_LOCATION = "Bangaluru, India"
LETTERHEAD_PURPLE = "#4B3F91"
LETTERHEAD_GOLD = "#F0A93A"
LETTERHEAD_FOOTER = (
    "Zintlr Private Limited<br/>"
    "No. 7, 7th Cross, Hebbal Ganganagara Layout, Ganganagar, RT Nagar, Bengaluru - 560032<br/>"
    '<link href="mailto:hr@zintlr.com" color="blue"><u>hr@zintlr.com</u></link> | +91 83107 60719'
)
# Optional — drop a logo file here and it's picked up automatically, no code change needed.
LOGO_PATH = os.path.join("static", "logo.png")

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
    textColor="#333333",
    alignment=TA_CENTER,
)


def _draw_gradient_line(canvas, x1, x2, y, color_start, color_end, width=1.5):
    """A perfectly smooth native PDF gradient line (not hand-segmented, which can look choppy)."""
    canvas.saveState()
    path = canvas.beginPath()
    path.rect(x1, y - width / 2, x2 - x1, width)
    canvas.clipPath(path, stroke=0)
    canvas.linearGradient(x1, y, x2, y, [HexColor(color_start), HexColor(color_end)])
    canvas.restoreState()


def _draw_letterhead(canvas, doc):
    canvas.saveState()
    page_width, page_height = A4
    x = doc.leftMargin
    right_x = page_width - doc.rightMargin

    if os.path.exists(LOGO_PATH):
        logo_size = 1.3 * cm
        canvas.drawImage(
            LOGO_PATH,
            x,
            page_height - 2.1 * cm,
            width=logo_size,
            height=logo_size,
            preserveAspectRatio=True,
        )
        x += logo_size + 0.3 * cm

    canvas.setFont("Helvetica-Bold", 15)
    canvas.setFillColor(LETTERHEAD_PURPLE)
    canvas.drawString(x, page_height - 1.5 * cm, LETTERHEAD_TITLE)

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(LETTERHEAD_PURPLE)
    canvas.drawString(x, page_height - 1.95 * cm, LETTERHEAD_SUBTITLE)

    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor("#666666")
    canvas.drawRightString(right_x, page_height - 1.4 * cm, LETTERHEAD_CIN)
    canvas.drawRightString(right_x, page_height - 1.75 * cm, LETTERHEAD_WEBSITE)
    canvas.drawRightString(right_x, page_height - 2.1 * cm, LETTERHEAD_LOCATION)

    _draw_gradient_line(
        canvas, doc.leftMargin, right_x, page_height - 2.4 * cm, LETTERHEAD_PURPLE, LETTERHEAD_GOLD
    )

    footer = Paragraph(LETTERHEAD_FOOTER, _footer_style)
    footer_y = 1.0 * cm
    _, footer_height = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, footer_y)

    line_y = footer_y + footer_height + 0.2 * cm
    canvas.setStrokeColor("#999999")
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, line_y, right_x, line_y)

    canvas.restoreState()


def render_text_to_pdf(body_text: str, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=3.2 * cm,
        bottomMargin=2.8 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    story = []
    for paragraph in body_text.split("\n\n"):
        text = paragraph.strip().replace("\n", "<br/>")
        if text:
            story.append(Paragraph(text, _body_style))
        story.append(Spacer(1, 4))
    doc.build(story, onFirstPage=_draw_letterhead, onLaterPages=_draw_letterhead)


def generate_declaration_pdf(name: str, **extra) -> str:
    """Render the BG declaration document template for `name` and save it as a PDF.

    `extra` may include designation, team_name, doj, uan — same fields available
    to the email body — so the document template can reference them too.
    """
    body_text = render_document("bg_declaration", name=name, **extra)
    name_slug = name.lower().replace(" ", "_").strip()
    output_path = os.path.join(config.GENERATED_DIR, f"declaration_{name_slug}.pdf")
    os.makedirs(config.GENERATED_DIR, exist_ok=True)
    render_text_to_pdf(body_text, output_path)
    return output_path


def to_static_url(path: str) -> str:
    """Convert a file path under static/ into a URL Streamlit can serve directly,
    for reliable inline PDF preview (browsers block base64 data: URIs in an iframe)."""
    rel = os.path.relpath(path, "static")
    return f"app/static/{rel}"


def resolve_attachments(attachment_keys: list[str], name: str | None = None, **extra) -> list[str]:
    """Turn logical attachment keys from an email template into real file paths."""
    paths = []
    for key in attachment_keys:
        if key == "declaration":
            paths.append(generate_declaration_pdf(name, **extra))
        elif key in config.STATIC_ATTACHMENTS:
            paths.append(config.STATIC_ATTACHMENTS[key])
        else:
            raise ValueError(f"Unknown attachment key '{key}'")
    return paths
