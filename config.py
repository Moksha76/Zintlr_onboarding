import os
from dotenv import load_dotenv
load_dotenv()

# Email
SENDER_EMAIL = "mokshaprada.p@zintlr.com"
HR_ADMIN_EMAIL = "hradmin@zintlr.com"
NISHA_EMAIL = os.getenv("NISHA_EMAIL", "")   # Set in .env once confirmed

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

# Inventory
INVENTORY_THRESHOLD = 3

# Scheduler
SHEET_POLL_MINUTES = 5
SCHEDULER_CHECK_MINUTES = 15

# Dates
FORM11_OFFSET_DAYS = 15
JOINING_OFFER_OFFSET_DAYS = -2   # DOJ minus 2

# Paths
DB_PATH = "database/onboarding.db"
GENERATED_DIR = "generated"
BACKUP_DIR = "backups"
LOG_FILE = "logs/activity.log"
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "")

# Google Sheet column names (exact — confirm with Nisha before Phase 4)
SHEET_COLUMNS = {
    "name": "Full_Name",
    "email": "Candidate_Email",
    "designation": "Designation",
    "doj": "DOJ",
    "offer_letter": "Offer_Letter_Issued",
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
    "insurance_form": "https://docs.google.com/forms/d/e/1FAIpQLSch5srG7kKHIk11pO54yKCKKObOInq6noOd4vawSPNsCDnGjg/viewform",
}
