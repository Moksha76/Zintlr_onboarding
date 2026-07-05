import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from database.models import Base, DocumentTemplate, EmailTemplate, Inventory

engine = create_engine(f"sqlite:///{config.DB_PATH}")
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# (template_key, display_name, subject, cc_default, attachments_json, body_html)
# cc_default holds only *additional* default CC beyond HR Admin, which is always
# mandatory (enforced in services/template_engine.py, not stored here).
# attachments_json holds logical attachment keys resolved by services/pdf_service.py:
#   "declaration"      -> generated, name-stamped BG declaration PDF
#   "form11_reference"  -> static reference Form 11 PDF (same file for everyone)
#   "obligation"        -> static Zintlr Obligations PDF (same file for everyone)
_EMAIL_TEMPLATES = [
    (
        "bg_verification",
        "BG Verification",
        "Zintlr Communications_Background Verification",
        "",
        json.dumps(["declaration"]),
        """Hi {{ name }},

Hope you're doing well.

Please find attached the consent form that allows Zintlr to collect your information and carry out the background verification process. Kindly sign and share the scanned copy at your earliest convenience.

Also, please fill out the <a href="{{ links.bg_form }}">Background Verification Link</a> by {{ bg_deadline_time }} on {{ bg_deadline_date }}.

Feel free to reach out if you have any questions or face any issues.

{{ signature }}""",
    ),
    (
        "db_form",
        "Database Form",
        "Zintlr Communications_Database Form",
        "",
        json.dumps([]),
        """Dear {{ name }},

On behalf of the Zintlr team, I would like to extend a warm welcome to you as our newest team member. We are thrilled to have you join our organization and look forward to your contributions.

As part of our onboarding process, Please fill out the <a href="{{ links.db_form }}">Database Form</a>. The form will only collect your basic and necessary details. All the information provided by you will be confidential and will only be used for administrative processes.

If you have any questions or need assistance, don't hesitate to reach out. We look forward to working with you and supporting your journey with us.

{{ signature }}""",
    ),
    (
        "preonboard_story",
        "Pre-onboarding 1 — Our Story",
        "Zintlr Communications – Our Story, From Idea to Impact",
        "",
        json.dumps([]),
        """Hi {{ name }},

Every company has a beginning—and this is ours. The Zintlr Story is a look into how an idea turned into a growing company, the milestones we've crossed, and the vision that drives us every day. We're so excited for you to be part of our next chapter - <a href="{{ links.zstory }}">ZStory</a>

{{ signature }}""",
    ),
    (
        "preonboard_culture",
        "Pre-onboarding 2 — Our Culture & Values",
        "Zintlr Communications – Our Culture & Values",
        "",
        json.dumps([]),
        """Hi {{ name }},

At Zintlr, our culture isn't just a set of words—it's the lens through which we operate every single day. From transparency to innovation, these values shape how we work, collaborate, and grow together. Sharing this with you as a glimpse into what we believe in and what you'll soon be a part of - <a href="{{ links.zvalues }}">zValues</a>.

{{ signature }}""",
    ),
    (
        "preonboard_leadership",
        "Pre-onboarding 3 — Leadership Insights",
        "Zintlr Communications - Leadership Insights to Kickstart Your Journey",
        "",
        json.dumps([]),
        """Hi {{ name }},

As part of your pre-onboarding process, please take a moment to watch this insightful video on leadership: <a href="{{ links.leadership_video }}">{{ links.leadership_video }}</a>

It offers valuable lessons that will help set the tone for your journey with us.

We're excited to have you on board and look forward to working together!

{{ signature }}""",
    ),
    (
        "preonboard_joining",
        "Pre-onboarding 4 — Joining Offer and Details",
        "Zintlr Communications_Joining Offer and Joining Details",
        "",
        json.dumps([]),
        """Dear {{ name }},

We are delighted to extend a warm welcome to you as the newest member of the {{ team_name }} at Zintlr Private Limited.

<strong>Company Address:</strong>
Zintlr Private Limited
Full Address: 3rd Floor, No. 38, GKR Vaishtadhama, 12th Cross, CBI Rd., Ganganagar, Bengaluru - 32
G-Map Link: <a href="{{ links.office_map }}">{{ links.office_map }}</a>

<strong>Dress Code:</strong>
Our company promotes a professional yet comfortable working environment. We follow a business semi-casual dress code, so please dress accordingly.

<strong>Office Timings and Hours:</strong>
Our office hours are from 09:00 AM to 06:00 PM, Monday through Friday. We expect you to be at the office by 09:30 AM and work 8 hours each day.

<strong>Joining Date & Time:</strong>
Please remember to join us on {{ doj }} at 10:00 AM.

We are excited to have you on board and look forward to seeing you on your first day. If you have any questions or need further assistance before joining, please do not hesitate to contact us.

Welcome to the team!

{{ signature }}""",
    ),
    (
        "mbti",
        "MBTI Personality Assessment",
        "Zintlr Communications_MBTI Personality Assessment",
        "",
        json.dumps([]),
        """Hi {{ name }},

As part of an activity being conducted in the office, we request you to complete a short personality assessment.

The assessment takes approximately 15 minutes to complete.

Assessment Link: <a href="{{ links.mbti_test }}">{{ links.mbti_test }}</a>

Once you have completed the assessment, kindly share a screenshot of the results page that displays the personality trait bars.

We request you to complete the assessment and share the screenshot at your earliest convenience.

Thank you for your participation!

{{ signature }}""",
    ),
    (
        "insurance",
        "Insurance Detail Collection",
        "Zintlr Communications_Insurance Detail Collection",
        "",
        json.dumps([]),
        """Dear {{ name }},

Greetings!

As part of your onboarding process, we request you to submit your health insurance details by completing the form below.

Health Insurance Details Form: <a href="{{ links.insurance_form }}">{{ links.insurance_form }}</a>

Kindly ensure that all the required information is filled in accurately to facilitate the activation of your health insurance.

If you have any questions or require any assistance while filling out the form, please feel free to reach out to the Admin Team.

Thank you for your cooperation.

{{ signature }}""",
    ),
    (
        "form11",
        "Form 11 PF Declaration",
        "Zintlr Communications_Form 11 PF Declaration",
        "",
        json.dumps(["form11_reference"]),
        """Hi {{ name }},

Please generate your UAN and PF numbers as per the instructions below:

<strong>Process for Employees to Generate UAN via UMANG App</strong>

<strong>Requirements:</strong>
Smartphone with UMANG App and AadhaarFaceRd App installed.
Aadhaar number.
Aadhaar-linked mobile number.

<strong>Steps:</strong>
Download and install UMANG & AadhaarFaceRd apps.
Open UMANG → EPFO Services → UAN Allotment & Activation.
Enter Aadhaar & Aadhaar-linked mobile number.
Verify with OTP.
Complete Face Authentication via AadhaarFaceRd app.
On successful verification, a new UAN will be allotted instantly.
UAN and system-generated password will be sent to the employee's registered mobile number via SMS.
Once allotted, the UAN is automatically activated and can be used immediately for PF-related services.

Please share your UAN details generated in the following form attached.

{{ signature }}""",
    ),
    (
        "obligation",
        "Obligation Document",
        "Zintlr Obligation Document",
        "",
        json.dumps(["obligation"]),
        """Dear {{ name }},

As part of your onboarding process, please find the attached Obligation Document for your reference.

This document outlines the key responsibilities, obligations, and terms applicable during your employment with the organization. We request you to go through the document carefully and familiarize yourself with its contents.

If you have any questions or require any clarification, please feel free to reach out.

We wish you a successful journey with Zintlr.

{{ signature }}""",
    ),
]

# (document_key, display_name, body_text)
_DOCUMENT_TEMPLATES = [
    (
        "bg_declaration",
        "BG Declaration Consent Form",
        """Dear {{ name }},

As part of the hiring process, Zintlr Private Limited conducts background verification to verify the accuracy of the information provided and to assess suitability for the position applied for. This verification process may include, but is not limited to, reviewing your educational qualifications, employment history, criminal records, references, and other relevant checks.

By signing this form, you authorize Zintlr Private Limited or its designated agents to:
1. Collect, verify, and process the information provided in your application.
2. Contact previous employers, educational institutions, and other organizations for confirmation of the information.
3. Access public or proprietary databases to obtain additional information relevant to the verification process.

Please note:
- The information collected will be handled in compliance with applicable data protection and privacy laws.
- The information will only be used for the purpose of evaluating your application and suitability for employment.

Applicant's Declaration:
I, {{ name }}, hereby give my consent to Zintlr Private Limited to conduct the necessary background verification as outlined above. I confirm that the information provided in my application is true and accurate to the best of my knowledge. I release Zintlr Private Limited and its representatives from any liability related to this process.

Signature: ____________________________
Full Name: ____________________________
Date: ____________________________""",
    ),
]


def _seed_email_templates(session):
    if session.query(EmailTemplate).count() > 0:
        return
    for template_key, display_name, subject, cc_default, attachments_json, body_html in _EMAIL_TEMPLATES:
        session.add(
            EmailTemplate(
                template_key=template_key,
                display_name=display_name,
                subject=subject,
                body_html=body_html,
                cc_default=cc_default,
                attachments_json=attachments_json,
                version=1,
                active=True,
            )
        )
    session.commit()


def _seed_document_templates(session):
    if session.query(DocumentTemplate).count() > 0:
        return
    for document_key, display_name, body_text in _DOCUMENT_TEMPLATES:
        session.add(
            DocumentTemplate(
                document_key=document_key,
                display_name=display_name,
                body_text=body_text,
                version=1,
                active=True,
            )
        )
    session.commit()


def _seed_inventory(session):
    if session.query(Inventory).count() > 0:
        return
    session.add(Inventory(item_type="kit", size=None, quantity=0, threshold=config.INVENTORY_THRESHOLD))
    for size in ["S", "M", "L", "XL"]:
        session.add(Inventory(item_type="tshirt", size=size, quantity=0, threshold=config.INVENTORY_THRESHOLD))
    session.commit()


def init_db():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    os.makedirs(config.GENERATED_DIR, exist_ok=True)
    os.makedirs(config.BACKUP_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)

    Base.metadata.create_all(engine)

    session = SessionLocal()
    try:
        _seed_email_templates(session)
        _seed_document_templates(session)
        _seed_inventory(session)
    finally:
        session.close()
