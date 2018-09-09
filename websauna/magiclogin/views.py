# Standard Library
import logging

# Pyramid
import colander
import deform
from pyramid import httpexceptions
from pyramid.settings import aslist

# Websauna
from websauna.magiclogin.requirelogin import get_login_state
from websauna.system.core.route import simple_route
from websauna.system.core.sitemap import include_in_sitemap
from websauna.system.form.schema import CSRFSchema
from websauna.system.form.throttle import throttled_view
from websauna.system.http import Request
from websauna.system.user.utils import get_login_service
from websauna.system.user.models import User
from websauna.system.core import messages

from .login import start_email_login
from .login import verify_email_login


logger = logging.getLogger('websauna.magic')


class AskEmailSchema(CSRFSchema):
    """Form for getting user email."""

    email = colander.SchemaNode(
        colander.String(),
        title="Email address",
        validator=colander.Email(),
        widget=deform.widget.TextInputWidget(type='email', template="textinput_placeholder", placeholder="yourname@example.com")
    )


@simple_route("/login", route_name="login", renderer='magiclogin/login.html')
@include_in_sitemap(False)
def login(request: Request):
    """Replace the defaut login view with this simplified version."""
    settings = request.registry.settings
    social_logins = aslist(settings.get("websauna.social_logins", []))
    login_slogan = request.registry.settings.get("magiclogin.login_slogan")
    return locals()


@simple_route("/login-email", route_name="login_email", renderer='magiclogin/login_email.html', decorator=throttled_view(setting="magiclogin.login_email_throttle"))
@include_in_sitemap(False)
def login_email(request: Request):
    """Ask user email to start email sign in process."""
    schema = AskEmailSchema().bind(request=request)
    button = deform.Button(name='confirm', title="Email me a link to sign in", css_class="btn btn-primary btn-block")
    form = deform.Form(schema, buttons=[button])

    # User submitted this form
    if request.method == "POST":
        if 'confirm' in request.POST:
            try:

                # Where to go after user clicks the link in the email.
                # This is signaled us through Redis, set by the view that draw Sign in with email link.
                # Set by save_login_state()
                state = get_login_state(request)
                if state:
                    next_url = state.get("next_url")
                    extras = state.get("extras")
                else:
                    next_url = None  # Defaults to the referrer page
                    extras = None

                appstruct = form.validate(request.POST.items())
                start_email_login(request, appstruct["email"], next_url=next_url, extras=extras)
                return httpexceptions.HTTPFound(request.route_url("login_email_sent"))
            except deform.ValidationFailure as e:
                # Render a form version where errors are visible next to the fields,
                # and the submitted values are posted back
                rendered_form = e.render()
        else:
            # We don't know which control caused form submission
            raise httpexceptions.HTTPInternalServerError("Unknown form button pressed")
    else:
        # Render a form with initial values
        rendered_form = form.render()

    return locals()


@simple_route("/login-email-sent", route_name="login_email_sent", renderer='magiclogin/login_email_sent.html')
@include_in_sitemap(False)
def login_email_sent(request: Request):
    email = request.session.get("email")
    return locals()


@simple_route("/verify-email-login/{token}", route_name="verify_email_login", decorator=throttled_view(setting="magiclogin.login_email_throttle"))
@include_in_sitemap(False)
def _verify_email_login(request):
    """Confirm email login token."""
    token = request.matchdict["token"]
    return verify_email_login(request, token)


@simple_route("/login-to-continue", route_name="login_to_continue", renderer='magiclogin/login_to_continue.html')
@include_in_sitemap(False)
def login_to_continue(request):
    """require_login() intersitital"""

    state = get_login_state(request)

    if state:
        msg = state.get("msg")
    else:
        # Bots banging the door
        msg = ""

    settings = request.registry.settings
    social_logins = aslist(settings.get("websauna.social_logins", []))
    login_slogan = request.registry.settings.get("magiclogin.login_slogan")
    return locals()


@simple_route('/easy-dev-login', route_name="easy_dev_login", renderer='magiclogin/easy_dev_login.html', require_csrf=False)
@include_in_sitemap(False)
def easy_dev_login(request: Request):
    """A hacky login that only asks for username.

    USE ONLY IN DEVELOPMENT MODE!
    """
    allow = request.registry.settings.get("magiclogin.easy_dev_login")

    host = request.host.split(":")[0]

    logger.debug("websauna.magiclogin.views.easy_dev_login : request={0}".format(request))
    logger.debug("websauna.magiclogin.views.easy_dev_login : host={0}".format(host))
    logger.debug("websauna.magiclogin.views.easy_dev_login : allow={0}".format(allow))

    if ((allow is None) or (allow != "true") or (host != "localhost")):
        # exit quietly
        return httpexceptions.HTTPNotFound()

    logger.debug("websauna.magiclogin.views.easy_dev_login : allowing passwordless login")

    # Process form
    if request.method == "POST":
        username = request.params.get('username', None)
        logger.debug("websauna.magiclogin.views.easy_dev_login : username={0}".format(username))
        login_service = get_login_service(request)
        user = request.dbsession.query(User).filter_by(username=username).first()
        try:
            return login_service.authenticate_user(user, login_source="easy_dev_login")
        except Exception as e:
            logger.exception("Authentication failure")
            messages.add(request, msg="Invalid Authentication", msg_id="msg-authentication-failure", kind="error")
            return {}
    elif request.user:
        # Already logged in
        pass
    else:
        # HTTP get, display login form
        return locals()
