from models import UserRole

# All modules your app can protect (sidebar + route guards)
ALL_MODULES = [
    "catalog",
    "inventory",
    "orders",
    "production",
    "finance",
    "sales_stats",
    #"users",        
    #"invites",
    #"role_templates",
    #"profile",
    #"settings",
]

# Default template per role (per company)
DEFAULT_ROLE_MODULES: dict[UserRole, list[str]] = {
    UserRole.owner: ALL_MODULES,
    UserRole.admin: ALL_MODULES,
    UserRole.manager: ["catalog", "inventory", "orders", "production", "sales_stats"],
    UserRole.member: ["catalog", "inventory", "orders"],
    UserRole.viewer: ["catalog", "inventory"],
}
