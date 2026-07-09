from datetime import datetime

import config

_scheduler = None


def start_scheduler():
    """Idempotent — safe to call from every page. Only actually starts once
    per running process, since Streamlit re-executes page scripts on every
    interaction but keeps modules (and this module-level flag) cached."""
    global _scheduler
    if _scheduler is not None:
        return

    from apscheduler.schedulers.background import BackgroundScheduler

    from services import sheet_sync

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        sheet_sync.sync_from_sheet,
        "interval",
        minutes=config.SHEET_POLL_MINUTES,
        id="sheet_sync",
        next_run_time=datetime.now(),  # run once immediately on startup, then every N minutes
    )
    _scheduler.start()
