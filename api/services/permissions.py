from sqlalchemy.orm import Session
from collections import defaultdict
from models import APIUser, Permission, CompanyRolePermission, UserPermissionOverride

def get_effective_permission_modules(db: Session, user_model: APIUser) -> list[str]:
    # 1) base permissions from company role defaults
    base_module = {
        module
        for (module,) in (
            db.query(Permission.module)
            .join(CompanyRolePermission, CompanyRolePermission.permission_id == Permission.id)
            .filter(
                CompanyRolePermission.company_id == user_model.company_id,
                CompanyRolePermission.role == user_model.role,
            )
            .all()
        )
    }

    # 2) apply per-user overrides
    overrides = (
        db.query(Permission.module, UserPermissionOverride.allowed)
        .join(Permission, Permission.id == UserPermissionOverride.permission_id)
        .filter(UserPermissionOverride.user_id == user_model.id)
        .all()
    )

    for module, allowed in overrides:
        if allowed:
            base_module.add(module)
        else:
            base_module.discard(module)

    return sorted(base_module)


def attach_effective_permissions_for_company_users(db: Session, users: list[APIUser]) -> None:
    if not users:
        return

    company_id = users[0].company_id
    user_ids = [u.id for u in users]
    roles = list({u.role for u in users})

    # 1) Load role defaults for the roles we actually have in this company
    role_defaults: dict = defaultdict(set)  # role -> set[module]
    rows = (
        db.query(CompanyRolePermission.role, Permission.module)
        .join(Permission, Permission.id == CompanyRolePermission.permission_id)
        .filter(
            CompanyRolePermission.company_id == company_id,
            CompanyRolePermission.role.in_(roles),
        )
        .all()
    )
    for role, module in rows:
        role_defaults[role].add(module)

    # 2) Load overrides for all these users
    overrides_by_user: dict = defaultdict(list)  # user_id -> list[(module, allowed)]
    ov_rows = (
        db.query(UserPermissionOverride.user_id, Permission.module, UserPermissionOverride.allowed)
        .join(Permission, Permission.id == UserPermissionOverride.permission_id)
        .filter(UserPermissionOverride.user_id.in_(user_ids))
        .all()
    )
    for user_id, module, allowed in ov_rows:
        overrides_by_user[user_id].append((module, allowed))

    # 3) Compute and attach
    for u in users:
        perms = set(role_defaults.get(u.role, set()))
        for module, allowed in overrides_by_user.get(u.id, []):
            if allowed:
                perms.add(module)
            else:
                perms.discard(module)
        u.permissions = sorted(perms)
