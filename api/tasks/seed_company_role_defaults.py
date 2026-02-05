from sqlalchemy.orm import Session
from database import SessionLocal
from models import Permission, CompanyRolePermission
from defaults.permissions import DEFAULT_ROLE_MODULES

def ensure_company_role_defaults(db: Session | None = None, company_id: int = 0, *, commit: bool | None = None) -> None:
    """
    Ensure company has default role permissions.

    - If db is None: opens its own session and commits
    - If db is provided: flushes by default
    """
    if not company_id:
        raise ValueError("company_id is required")

    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        has_any = (
            db.query(CompanyRolePermission.id)
            .filter(CompanyRolePermission.company_id == company_id)
            .first()
            is not None
        )
        if has_any:
            return

        perm_rows = db.query(Permission.id, Permission.module).all()
        perm_id_by_module = {module: pid for pid, module in perm_rows}

        for role, modules in DEFAULT_ROLE_MODULES.items():
            for module in modules:
                pid = perm_id_by_module.get(module)
                if pid is None:
                    continue
                db.add(
                    CompanyRolePermission(
                        company_id=company_id,
                        role=role,
                        permission_id=pid,
                    )
                )

        if commit is None:
            commit = own_session

        if commit:
            db.commit()
        else:
            db.flush()

    finally:
        if own_session:
            db.close()
