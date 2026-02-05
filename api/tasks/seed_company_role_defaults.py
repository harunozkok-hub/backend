
from models import Permission, CompanyRolePermission, UserRole
from defaults.permissions import DEFAULT_ROLE_MODULES

def ensure_company_role_defaults(db: None, company_id: int) -> None:
    # If defaults already exist for this company, don't duplicate
    has_any = (
        db.query(CompanyRolePermission.id)
        .filter(CompanyRolePermission.company_id == company_id)
        .first()
        is not None
    )
    if has_any:
        return

    # Map module -> permission_id
    perm_rows = db.query(Permission.id, Permission.module).all()
    perm_id_by_module = {m: pid for pid, m in perm_rows}

    # Insert defaults for each role
    for role, modules in DEFAULT_ROLE_MODULES.items():
        for module in modules:
            pid = perm_id_by_module.get(module)
            if not pid:
                # catalog missing => seed_permission_catalog not run
                # skip safely, or raise if you prefer strict
                continue
            db.add(
                CompanyRolePermission(
                    company_id=company_id,
                    role=role,
                    permission_id=pid,
                )
            )

    db.flush()
