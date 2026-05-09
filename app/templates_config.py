from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def _user_perms(user):
    if user is None:
        return {"orders": False, "productions": False, "shipments": False}
    if user.is_admin:
        return {"orders": True, "productions": True, "shipments": True}
    return {
        "orders":      user.has_permission("can_access_orders"),
        "productions": user.has_permission("can_access_productions"),
        "shipments":   user.has_permission("can_access_shipments"),
    }


templates.env.globals["user_perms"] = _user_perms
