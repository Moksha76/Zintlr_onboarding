import os

from reportlab.lib.colors import Color, HexColor
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


def _draw_gradient_line(canvas, x1, x2, y, color_start, color_end, width=1.5, segments=80):
    c1, c2 = HexColor(color_start), HexColor(color_end)
    seg_width = (x2 - x1) / segments
    canvas.setLineWidth(width)
    for i in range(segments):
        t = i / (segments - 1)
        blended = Color(
            c1.red + (c2.red - c1.red) * t,
            c1.green + (c2.green - c1.green) * t,
            c1.blue + (c2.blue - c1.blue) * t,
        )
        canvas.setStrokeColor(blended)
        seg_x1 = x1 + i * seg_width
        canvas.line(seg_x1, y, seg_x1 + seg_width + 0.5, y)


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
    footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, 1.0 * cm)

    canvas.setStrokeColor("#999999")
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 1.8 * cm, right_x, 1.8 * cm)

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


def generate_declaration_pdf(name: str) -> str:
    """Render the BG declaration document template for `name` and save it as a PDF."""
    body_text = render_document("bg_declaration", name=name)
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
