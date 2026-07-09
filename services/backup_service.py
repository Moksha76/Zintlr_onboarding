import glob
import os
import shutil
from datetime import date

import config

_KEEP_BACKUPS = 30


def backup_database():
    """Copy the sqlite db into backups/ once per calendar day. Never raises —
    called from the background scheduler, and safe to call on every app
    startup since it skips if today's backup already exists."""
    try:
        if not os.path.exists(config.DB_PATH):
            return
        os.makedirs(config.BACKUP_DIR, exist_ok=True)

        today_str = date.today().strftime("%Y%m%d")
        dest = os.path.join(config.BACKUP_DIR, f"onboarding_{today_str}.db")
        if os.path.exists(dest):
            return

        shutil.copy2(config.DB_PATH, dest)
        _prune_old_backups()
    except Exception:
        pass


def _prune_old_backups():
    backups = sorted(glob.glob(os.path.join(config.BACKUP_DIR, "onboarding_*.db")))
    excess = len(backups) - _KEEP_BACKUPS
    for path in backups[:excess]:
        try:
            os.remove(path)
        except OSError:
            pass
