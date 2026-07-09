import os
from datetime import date, datetime

import config
from database.db import SessionLocal
from database.models import ActivityLog, Joiner
from services import stage_service

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_REQUIRED_COLUMNS = [
    config.SHEET_COLUMNS["name"],
    config.SHEET_COLUMNS["email"],
    config.SHEET_COLUMNS["designation"],
    config.SHEET_COLUMNS["doj"],
    config.SHEET_COLUMNS["ready_for_onboarding"],
    config.SHEET_COLUMNS["bg_result"],
]


class SheetSyncError(Exception):
    pass


def _get_worksheet():
    if not os.path.exists(config.CREDENTIALS_PATH):
        raise SheetSyncError("credentials.json not found — Google Sheets isn't connected yet.")
    if not config.GOOGLE_SHEET_URL:
        raise SheetSyncError("No Google Sheet URL configured in .env.")

    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_file(config.CREDENTIALS_PATH, scopes=_SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(config.GOOGLE_SHEET_URL)
    return sheet.sheet1


def _is_checked(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().upper() in ("TRUE", "YES", "1")


def _parse_date(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _log_system_event(session, details: str, tone: str):
    session.add(ActivityLog(event_type="sheet_sync", joiner_id=None, details=details, tone=tone))
    session.commit()


def _create_joiner_from_sheet(session, name: str, email: str, designation: str, doj: date, row_index: int):
    from datetime import timedelta

    team_name = config.DESIGNATION_TO_TEAM.get(designation, "team")
    sim_required = designation in config.DESIGNATIONS_REQUIRING_SIM
    form11_due_date = doj + timedelta(days=config.FORM11_OFFSET_DAYS)

    joiner = Joiner(
        full_name=name,
        candidate_email=email,
        designation=designation,
        team_name=team_name,
        doj=doj,
        current_stage="NEW",
        sim_required=sim_required,
        form11_due_date=form11_due_date,
        sheet_row_index=row_index,
    )
    session.add(joiner)
    session.commit()
    session.refresh(joiner)

    session.add(
        ActivityLog(
            event_type="joiner_added",
            joiner_id=joiner.id,
            details=f"New joiner detected from HR sheet: {joiner.full_name} ({joiner.designation})",
            tone="ok",
        )
    )
    session.commit()
    return joiner


def sync_from_sheet() -> dict:
    """Poll the HR sheet: pick up candidates marked Ready_For_Onboarding, and apply
    BG_Result outcomes (Passed/Dropped). Never raises — failures are logged and
    surfaced to the Dashboard instead of crashing the app."""
    result = {"new_joiners": 0, "error": None, "missing_columns": []}

    session = SessionLocal()
    try:
        try:
            worksheet = _get_worksheet()
            rows = worksheet.get_all_records()
        except SheetSyncError as e:
            result["error"] = str(e)
            _log_system_event(session, result["error"], "warn")
            return result
        except Exception as e:
            result["error"] = f"Sheet sync failed: {e}"
            _log_system_event(session, result["error"], "danger")
            return result

        if not rows:
            _log_system_event(session, "Sheet sync ran — sheet is empty.", "info")
            return result

        header = list(rows[0].keys())
        missing = [c for c in _REQUIRED_COLUMNS if c not in header]
        if missing:
            result["missing_columns"] = missing
            result["error"] = f"Sheet is missing expected column(s): {', '.join(missing)}"
            _log_system_event(session, result["error"], "danger")
            return result

        for idx, row in enumerate(rows, start=2):  # row 1 is the header
            email = str(row.get(config.SHEET_COLUMNS["email"], "")).strip()
            if not email:
                continue

            ready = row.get(config.SHEET_COLUMNS["ready_for_onboarding"])
            bg_result = str(row.get(config.SHEET_COLUMNS["bg_result"], "")).strip()

            joiner = session.query(Joiner).filter(Joiner.candidate_email == email).first()

            if joiner is None:
                if _is_checked(ready):
                    name = str(row.get(config.SHEET_COLUMNS["name"], "")).strip()
                    designation = str(row.get(config.SHEET_COLUMNS["designation"], "")).strip()
                    doj = _parse_date(row.get(config.SHEET_COLUMNS["doj"]))
                    if name and designation and doj:
                        _create_joiner_from_sheet(session, name, email, designation, doj, idx)
                        result["new_joiners"] += 1
                continue

            if bg_result == "Passed" and joiner.current_stage == "BG_RECEIVED":
                stage_service.simulate_offer_confirmation(joiner.id)
            elif bg_result == "Dropped" and joiner.current_stage not in ("COMPLETED", "DROPPED"):
                stage_service.mark_dropped(joiner.id, reason="Background check result: Dropped (via HR sheet)")

        _log_system_event(
            session,
            f"Sheet sync completed — {result['new_joiners']} new joiner(s) detected.",
            "ok",
        )
    finally:
        session.close()

    return result


def update_sheet_row(candidate_email: str, column_key: str, value) -> bool:
    """Write a single status value back to the candidate's row. Silently
    returns False on any failure (missing credentials, row/column not found,
    API error) rather than raising — sheet writes must never break a send."""
    try:
        worksheet = _get_worksheet()
        column_name = config.SHEET_COLUMNS.get(column_key)
        if not column_name:
            return False
        cell = worksheet.find(candidate_email)
        if not cell:
            return False
        header_row = worksheet.row_values(1)
        if column_name not in header_row:
            return False
        col_idx = header_row.index(column_name) + 1
        worksheet.update_cell(cell.row, col_idx, value)
        return True
    except Exception:
        return False
