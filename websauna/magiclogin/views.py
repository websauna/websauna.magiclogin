from pyramid.settings import aslist
from websauna.system.http import Request
from websauna.system.core.route import simple_route


@simple_route("/login", route_name="login", renderer='magiclogin/login.html', append_slash=False)
def login(request:Request):
    """Replace the defaut login view with this simplified version."""

    settings = request.registry.settings
    social_logins = aslist(settings.get("websauna.social_logins", []))
    return locals()
