import os
from dotenv import load_dotenv
load_dotenv()

# Email
SENDER_EMAIL = "mokshaprada.p@zintlr.com"
SENDER_PHONE = "(+91) 6366940993"
HR_ADMIN_EMAIL = "hradmin@zintlr.com"
NISHA_EMAIL = os.getenv("NISHA_EMAIL", "")   # Set in .env once confirmed

# SMTP (Outlook sending via an app password) — set in .env once IT enables SMTP
# AUTH for the mailbox and you generate an app password. Preferred over Graph
# when set, since it needs no Azure app registration at all.
SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME", SENDER_EMAIL)
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")

# Microsoft Graph (Outlook sending) — set in .env once the Azure App Registration is done.
# Only used as a fallback if SMTP_APP_PASSWORD isn't set.
GRAPH_CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "")
GRAPH_TENANT_ID = os.getenv("GRAPH_TENANT_ID", "")
GRAPH_TOKEN_CACHE_PATH = "graph_token_cache.json"
GRAPH_SCOPES = ["Mail.Send", "User.Read"]

# Standard signature appended to every email template. Centralized so the phone
# number/contact details can never drift between templates.
SIGNATURE_BLOCK = (
    "Thanks & Regards,<br/>"
    "Moksha Prada .P<br/>"
    "Admin Ops<br/>"
    f"{SENDER_PHONE}<br/>"
    "Zintlr Pvt. Ltd."
)

# Designations
DESIGNATIONS = [
    "SDR", "AE", "BDR", "CS", "Ops",
    "Engineering", "Product", "Marketing", "Finance", "Other"
]
DESIGNATIONS_REQUIRING_SIM = ["AE", "SDR", "BDR", "Ops", "CS"]

DESIGNATION_TO_TEAM = {
    "SDR": "Sales Team",
    "AE": "Sales Team",
    "BDR": "Sales Team",
    "CS": "Customer Success Team",
    "Ops": "Operations Team",
    "Engineering": "Engineering Team",
    "Product": "Product Team",
    "Marketing": "Marketing Team",
    "Finance": "Finance Team",
    "Other": "team",
}

# Stage chip colours (Section 15)
STAGE_COLORS = {
    "NEW": "amber",
    "BG_SENT": "blue",
    "BG_RECEIVED": "indigo",
    "OFFER_CONFIRMED": "purple",
    "DB_SENT": "violet",
    "DB_RECEIVED": "violet",
    "ONBOARDING": "teal",
    "JOINED": "green",
    "FORMS_PENDING": "orange",
    "FORM11_DUE": "red",
    "COMPLETED": "gray",
    "DROPPED": "gray",
}

# Inventory
INVENTORY_THRESHOLD = 3
TSHIRT_SIZES = ["S", "M", "L", "XL", "XXL"]

# Scheduler
SHEET_POLL_MINUTES = 5
SCHEDULER_CHECK_MINUTES = 15

# Dates
FORM11_OFFSET_DAYS = 15
JOINING_OFFER_OFFSET_DAYS = -2   # DOJ minus 2

# Paths
DB_PATH = "database/onboarding.db"
# Lives under static/ so Streamlit can serve generated PDFs directly for inline
# preview (browsers block PDFs embedded as base64 data: URIs in an iframe).
GENERATED_DIR = "static/generated"
BACKUP_DIR = "backups"
LOG_FILE = "logs/activity.log"
STATIC_ATTACHMENTS_DIR = "static/static_attachments"
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "")

# Google Sheet column names (exact)
SHEET_COLUMNS = {
    "name": "Full_Name",
    "email": "Candidate_Email",
    "designation": "Designation",
    "doj": "DOJ",
    "ready_for_onboarding": "Ready_For_Onboarding",  # checkbox HR ticks when a row is complete
    "bg_result": "BG_Result",  # dropdown: In Progress / Passed / Dropped
    "bg_sent": "BG_Sent",
    "bg_sent_date": "BG_Sent_Date",
    "db_sent": "DB_Form_Sent",
    "db_sent_date": "DB_Form_Sent_Date",
    "agreement_signed": "Agreement_Signed",
    "laptop_assigned": "Laptop_Assigned",
    "sim_assigned": "SIM_Assigned",
    "kit_ready": "Kit_Ready_For_Handover",
    "tshirt_size": "Tshirt_Size_Ready",
    "status_note": "Status_Note",
}

# Document links (final)
LINKS = {
    "bg_form": "https://docs.google.com/forms/d/1kd71EEmJNP1cg6xfjKJwV1sIxENVn79ZBk1OMeXTa6U/viewform?edit_requested=true",
    "db_form": "https://docs.google.com/forms/d/e/1FAIpQLScHqWf0FGPLMjs-h9Kh-QcJaWOkh1ILgObQTSP8Jmi_t5zDvg/viewform",
    "zstory": "https://drive.google.com/file/d/1X6bH2H3xm29mKs2BhOU66Q96jiuWFSEM/view?usp=drive_link",
    "zvalues": "https://drive.google.com/file/d/1GOwPZCOWBvlYepfMGjbNWGFRapJkiH5T/view?usp=sharing",
    "leadership_video": "https://m.youtube.com/watch?v=eSvLFPFXjc8",
    "office_map": "https://maps.app.goo.gl/xk3x3pLLh4cusysNA",
    "mbti_test": "https://www.16personalities.com/free-personality-test",
    "insurance_form": "https://forms.gle/jTe9J6fpRSjpUHpR6",
}

# Static, non-personalized attachment files (same file sent to every candidate)
STATIC_ATTACHMENTS = {
    "form11_reference": f"{STATIC_ATTACHMENTS_DIR}/form11_reference_form.pdf",
    "obligation": f"{STATIC_ATTACHMENTS_DIR}/zintlr_obligations.pdf",
}
