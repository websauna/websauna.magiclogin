# Pyramid
from pyramid.httpexceptions import HTTPFound

# Websauna
from websauna.magiclogin.requirelogin import pop_login_state
from websauna.magiclogin.requirelogin import require_login
from websauna.system.core import messages
from websauna.system.core.route import simple_route


# Exposed to testing
_get_url = 0
_was_logged_in = None
_captured_post_params = None


@simple_route("/example_view_get", route_name="example_view_get", decorator=require_login())
def example_view_get(request):
    """Demostrate require_login() decorator for GET views."""
    global _get_url
    global _was_logged_in

    _get_url = request.url

    login_state = pop_login_state(request)
    params = request.params or login_state

    _was_logged_in = login_state is None

    messages.add(request, kind="info", msg="Succesfully continued GET action after login, params {}".format(params), msg_id="msg-example-get-view-success")

    return HTTPFound(request.route_url("home"))


@simple_route("/example_view_post", route_name="example_view_post", decorator=require_login())
def example_view_post(request):
    """Demostrate require_login() decorator for POST views."""
    global _was_logged_in
    global _captured_post_params

    login_state = pop_login_state(request)
    params = login_state["params"] if login_state else request.POST

    _was_logged_in = login_state is None
    _captured_post_params = params.copy()

    messages.add(request, kind="info", msg="Succesfully continued POST action after login, params {}".format(params), msg_id="msg-example-post-view-success")

    return HTTPFound(request.route_url("home"))


@simple_route("/require_login_example_page", route_name="magic_login_example_page", renderer="requirelogin-example.html")
def require_login_example_page(request):
    return locals()
