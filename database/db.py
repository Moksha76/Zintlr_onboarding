import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from database.models import Base, EmailTemplate, Inventory

engine = create_engine(f"sqlite:///{config.DB_PATH}")
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# (template_key, display_name, subject, cc_default, attachments_json, body_html)
_EMAIL_TEMPLATES = [
    (
        "bg_verification",
        "BG Verification",
        "Zintlr Communications_Background Verification",
        "hradmin@zintlr.com, {{ nisha_email }}",
        json.dumps(["generated/declaration_{{ name_slug }}.pdf"]),
        """Hi {{ name }},

Hope you're doing well.

Please find attached the consent form that allows Zintlr to collect your information and carry out the background verification process. Kindly sign and share the scanned copy at your earliest convenience.

Also, please fill out the <a href="https://docs.google.com/forms/d/1kd71EEmJNP1cg6xfjKJwV1sIxENVn79ZBk1OMeXTa6U/viewform?edit_requested=true">Background Verification Link</a> by {{ bg_deadline_time }} on {{ bg_deadline_date }}.

Feel free to reach out if you have any questions or face any issues.

Thanks & Regards,
Moksha Prada .P
Admin Ops
(+91) 6366940993
Zintlr Pvt. Ltd.""",
    ),
    (
        "db_form",
        "Database Form",
        "Zintlr Communications_Database Form",
        "hradmin@zintlr.com",
        json.dumps([]),
        """Dear {{ name }},

On behalf of the Zintlr team, I would like to extend a warm welcome to you as our newest team member. We are thrilled to have you join our organization and look forward to your contributions.

As part of our onboarding process, Please fill out the <a href="https://docs.google.com/forms/d/e/1FAIpQLScHqWf0FGPLMjs-h9Kh-QcJaWOkh1ILgObQTSP8Jmi_t5zDvg/viewform">Database Form</a>. The form will only collect your basic and necessary details. All the information provided by you will be confidential and will only be used for administrative processes.

If you have any questions or need assistance, don't hesitate to reach out. We look forward to working with you and supporting your journey with us.

Thanks & Regards,
Moksha Prada .P
Admin Ops
(+91) 6366940993
Zintlr Pvt. Ltd.""",
    ),
    (
        "preonboard_story",
        "Pre-onboarding 1 — Our Story",
        "Zintlr Communications – Our Story, From Idea to Impact",
        "hradmin@zintlr.com",
        json.dumps([]),
        """Hi {{ name }},

Every company has a beginning—and this is ours. The Zintlr Story is a look into how an idea turned into a growing company, the milestones we've crossed, and the vision that drives us every day. We're so excited for you to be part of our next chapter - <a href="https://drive.google.com/file/d/1X6bH2H3xm29mKs2BhOU66Q96jiuWFSEM/view?usp=drive_link">ZStory</a>

Thanks & Regards,
Moksha Prada .P
Admin Ops
(+91) 6366940993
Zintlr Pvt. Ltd.""",
    ),
    (
        "preonboard_culture",
        "Pre-onboarding 2 — Our Culture & Values",
        "Zintlr Communications – Our Culture & Values",
        "hradmin@zintlr.com",
        json.dumps([]),
        """Hi {{ name }},

At Zintlr, our culture isn't just a set of words—it's the lens through which we operate every single day. From transparency to innovation, these values shape how we work, collaborate, and grow together. Sharing this with you as a glimpse into what we believe in and what you'll soon be a part of - <a href="https://drive.google.com/file/d/1GOwPZCOWBvlYepfMGjbNWGFRapJkiH5T/view?usp=sharing">zValues</a>.

Thanks & Regards,
Moksha Prada .P
Admin Ops
(+91) 6366940993
Zintlr Pvt. Ltd.""",
    ),
    (
        "preonboard_leadership",
        "Pre-onboarding 3 — Leadership Insights",
        "Zintlr Communications - Leadership Insights to Kickstart Your Journey",
        "hradmin@zintlr.com",
        json.dumps([]),
        """Hi {{ name }},

As part of your pre-onboarding process, please take a moment to watch this insightful video on leadership: <a href="https://m.youtube.com/watch?v=eSvLFPFXjc8">https://m.youtube.com/watch?v=eSvLFPFXjc8</a>

It offers valuable lessons that will help set the tone for your journey with us.

We're excited to have you on board and look forward to working together!

Thanks & Regards,
Moksha Prada .P
Admin Ops
(+91) 6366940993
Zintlr Pvt. Ltd.""",
    ),
    (
        "preonboard_joining",
        "Pre-onboarding 4 — Joining Offer and Details",
        "Zintlr Communications_Joining Offer and Joining Details",
        "hradmin@zintlr.com",
        json.dumps([]),
        """Dear {{ name }},

We are delighted to extend a warm welcome to you as the newest member of the {{ team_name }} at Zintlr Private Limited.

<strong>Company Address:</strong>
Zintlr Private Limited
Full Address: 3rd Floor, No. 38, GKR Vaishtadhama, 12th Cross, CBI Rd., Ganganagar, Bengaluru - 32
G-Map Link: <a href="https://maps.app.goo.gl/xk3x3pLLh4cusysNA">https://maps.app.goo.gl/xk3x3pLLh4cusysNA</a>

<strong>Dress Code:</strong>
Our company promotes a professional yet comfortable working environment. We follow a business semi-casual dress code, so please dress accordingly.

<strong>Office Timings and Hours:</strong>
Our office hours are from 09:00 AM to 06:00 PM, Monday through Friday. We expect you to be at the office by 09:30 AM and work 8 hours each day.

<strong>Joining Date & Time:</strong>
Please remember to join us on {{ doj }} at 10:00 AM.

We are excited to have you on board and look forward to seeing you on your first day. If you have any questions or need further assistance before joining, please do not hesitate to contact us.

Welcome to the team!

Thanks & Regards,
Moksha Prada .P
Admin Ops
(+91) 6366940993
Zintlr Pvt. Ltd.""",
    ),
    (
        "mbti",
        "MBTI Personality Assessment",
        "Zintlr Communications_MBTI Personality Assessment",
        "hradmin@zintlr.com",
        json.dumps([]),
        """Hi {{ name }},

As part of your onboarding, we'd like you to take a quick personality assessment. This is a fun, in-office activity that gives us a sense of how you naturally work, communicate, and collaborate.

Please complete the test here: <a href="https://www.16personalities.com/free-personality-test">https://www.16personalities.com/free-personality-test</a>

Once done, kindly share a screenshot of the result page that shows the personality bars.

It takes about 10–12 minutes. There are no right or wrong answers.

Thanks & Regards,
Moksha Prada .P
Admin Ops
(+91) 6366940993
Zintlr Pvt. Ltd.""",
    ),
    (
        "insurance",
        "Insurance Detail Collection",
        "Zintlr Communications_Insurance Detail Collection",
        "hradmin@zintlr.com",
        json.dumps([]),
        """Hi {{ name }},

To enrol you in the company's health insurance plan, please fill out the form below with your details and any dependents you wish to include:

<a href="https://docs.google.com/forms/d/e/1FAIpQLSch5srG7kKHIk11pO54yKCKKObOInq6noOd4vawSPNsCDnGjg/viewform">Insurance Detail Collection</a>

Kindly complete this within the next 5 working days so we can process your coverage on time.

Reach out if you have any questions.

Thanks & Regards,
Moksha Prada .P
Admin Ops
(+91) 6366940993
Zintlr Pvt. Ltd.""",
    ),
    (
        "form11",
        "Form 11 PF Declaration",
        "Zintlr Communications_Form 11 PF Declaration",
        "hradmin@zintlr.com",
        json.dumps(["generated/form11_{{ name_slug }}.pdf"]),
        """Hi {{ name }},

Now that you've been with us for 15 days, the next step in your onboarding is the Form 11 Provident Fund declaration. Please find the form attached.

Kindly fill in the required details, sign, and share back at your earliest convenience.

{% if not uan %}
If you have an existing UAN from a previous employer, please write it in the form before signing.
{% endif %}

Reach out if you need any clarification.

Thanks & Regards,
Moksha Prada .P
Admin Ops
(+91) 6366940993
Zintlr Pvt. Ltd.""",
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
        _seed_inventory(session)
    finally:
        session.close()
