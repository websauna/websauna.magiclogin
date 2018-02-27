# Standard Library
import json
import typing as t

# Pyramid
import jinja2
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response

# Websauna
from websauna.system.core.route import get_config_route
from websauna.system.http import Request
from websauna.system.user.events import Login
from websauna.system.user.interfaces import IUser
from websauna.system.user.loginservice import DefaultLoginService


def save_login_state(request: Request, msg: t.Optional[str]=None):
    """Capture original POST/GET request before user was redirected to login page."""

    # TODO: This flattens NestedMultiDict to a normal dict
    params = dict(request.params.items())

    if not msg:
        msg = request.registry.get("websauna.magiclogin.default_proceed_login_message", "Please sign in to continue")

    # Allow raw HTML serialization
    markup = isinstance(msg, jinja2.Markup)

    saved_state = {
        "url": request.url,
        "method": request.method,
        "params": params,
        "msg": msg,
        "markup": markup,
    }
    request.session["proceed_to_login"] = json.dumps(saved_state).encode("utf-8")


def get_login_state(request: Request, remove=False):
    data = request.session.get("proceed_to_login")
    if data:

        if remove:
            del request.session["proceed_to_login"]

        data = data.decode("utf-8")

        data = json.loads(data)

        # Fix raw HTML markup
        if data.get("markup"):
            data["msg"] = jinja2.Markup(data["msg"])

        return data

    return None


def pop_login_state(request: Request):
    """Fetches the action state before login proceed interfered and marks is consumed."""
    return get_login_state(request, remove=True)


def proceed_to_login(context, request, msg):
    save_login_state(request, msg)
    return HTTPFound(request.route_url("login_to_continue"))


def require_login(msg=None):
    """Automatically prompt user to login for views that require login.

    If the view is POST endpoint, POST content is captured for the view.

    To use this decorator you need to enable custom login handler:

    :param msg: Message shown in interstitial page to the user
    """

    def outer(view: t.Callable[[object, Request], Response]):

        def inner(context, request):
            if not request.user:
                return proceed_to_login(context, request, msg=msg)
            else:
                return view(context, request)

        return inner

    return outer


class DeferredActionLoginService(DefaultLoginService):
    """Login service will perform the post-login action that was saved before login."""

    def do_post_login_actions(self, user: IUser, headers: dict, location: str=None):
        """Override what happens after login."""
        request = self.request

        self.update_login_data(user)

        e = Login(request, user)
        request.registry.notify(e)

        # Where this user was going before he or she hit login button
        login_state = get_login_state(request)
        if login_state:
            location = login_state["url"]
        else:
            # Only greet user if he/she was not continuing action
            self.greet_user(user)
            location = get_config_route(request, 'websauna.login_redirect')

        return HTTPFound(location)
