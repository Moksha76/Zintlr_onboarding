import threading
from datetime import datetime

import config

_scheduler = None
_lock = threading.Lock()


def start_scheduler():
    """Idempotent and thread-safe — safe to call from every page. Streamlit can
    trigger multiple near-simultaneous script runs (e.g. multiple browser tabs,
    rapid reruns), so a plain "if _scheduler is None" check can race; a lock
    plus a final defensive catch make this safe to call from anywhere."""
    global _scheduler

    with _lock:
        if _scheduler is not None and _scheduler.running:
            return

        from apscheduler.schedulers.background import BackgroundScheduler

        from services import backup_service, scheduled_email_service, sheet_sync

        _scheduler = BackgroundScheduler()
        _scheduler.add_job(
            sheet_sync.sync_from_sheet,
            "interval",
            minutes=config.SHEET_POLL_MINUTES,
            id="sheet_sync",
            replace_existing=True,
            next_run_time=datetime.now(),  # run once immediately on startup, then every N minutes
        )
        _scheduler.add_job(
            scheduled_email_service.process_due_scheduled_emails,
            "interval",
            minutes=config.SHEET_POLL_MINUTES,
            id="scheduled_email_check",
            replace_existing=True,
            next_run_time=datetime.now(),
        )
        _scheduler.add_job(
            backup_service.backup_database,
            "interval",
            minutes=1440,  # once a day; the job itself skips if today's backup already exists
            id="daily_backup",
            replace_existing=True,
            next_run_time=datetime.now(),  # attempt on every startup too, in case the laptop was off at the usual time
        )
        try:
            _scheduler.start()
        except Exception:
            pass  # already running somehow — fine, that's the desired end state
