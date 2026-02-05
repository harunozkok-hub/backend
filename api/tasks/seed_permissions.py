from sqlalchemy.orm import Session
from database import SessionLocal
from models import Permission
from defaults.permissions import ALL_MODULES

def seed_permission_catalog(db: Session | None = None, *, commit: bool | None = None) -> None:
    """
    Seeds the Permission catalog.

    - If db is None: opens its own session and commits (startup/script safe)
    - If db is provided: flushes by default (caller controls commit)
    """
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        existing = {m for (m,) in db.query(Permission.module).all()}
        missing = [m for m in ALL_MODULES if m not in existing]
        if not missing:
            return

        for m in missing:
            db.add(Permission(module=m, label=m.replace("_", " ").title()))

        # default behavior:
        # - own session => commit
        # - external session => flush
        if commit is None:
            commit = own_session

        if commit:
            db.commit()
        else:
            db.flush()

    finally:
        if own_session:
            db.close()
