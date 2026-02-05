from models import Permission
from defaults.permissions import ALL_MODULES
from dependencies.deps import db_dependency

def seed_permission_catalog(db: db_dependency) -> None:
    existing = {m for (m,) in db.query(Permission.module).all()}

    to_add = [m for m in ALL_MODULES if m not in existing]
    if not to_add:
        return

    for m in to_add:
        db.add(Permission(module=m, label=m.replace("_", " ").title()))
    db.commit()