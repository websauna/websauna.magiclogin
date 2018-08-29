# Pyramid
import colander
import deform
from pyramid import httpexceptions
from pyramid.settings import aslist
# from pyramid.response import Response

# Websauna
from websauna.magiclogin.requirelogin import get_login_state
from websauna.system.core.route import simple_route
from websauna.system.core.sitemap import include_in_sitemap
from websauna.system.form.schema import CSRFSchema
from websauna.system.form.throttle import throttled_view
from websauna.system.http import Request
from websauna.system.user.utils import get_login_service
from websauna.system.user.models import User
from websauna.system.core.views import notfound
from websauna.system.core import messages

from .login import start_email_login
from .login import verify_email_login


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



@simple_route('/hacky-login', route_name="hacky_login", renderer='magiclogin/hacky_login.html', require_csrf=False)
@include_in_sitemap(False)
def hacky_login(request: Request):
    """A hacky login that only asks for username - a nice thing when doing development, but ..  DANGEROUS!  USE ONLY IN DEVELOPMENT MODE!
    """
    verbose =True
    # verbose=False

    allow = request.registry.settings.get("magiclogin.hacky_login")

    host=request.host.split(":")[0]

    if (verbose): print("websauna.magiclogin.views.hacky_login : request=",request)
    if (verbose): print("websauna.magiclogin.views.hacky_login : host=",   host)
    if (verbose): print("websauna.magiclogin.views.hacky_login : allow=",  allow)

    if ((allow==None) or (allow!="true") or (host!="localhost")):
        # exit quietly
        return httpexceptions.HTTPNotFound()

    if (verbose): print("websauna.magiclogin.views.hacky_login : allowing passwordless login")

    # Process form
    if request.method == "POST":
        username = request.params.get('username', None)
        if (verbose): print("websauna.magiclogin.views.hacky_login : username",username)
        login_service = get_login_service(request)
        user = request.dbsession.query(User).filter_by(username=username).first()
        try:
            return login_service.authenticate_user(user, login_source="hacky_login")
        except:
            messages.add(request, msg="Invalid Auth", msg_id="msg-authentication-failure", kind="error")
            return {}
    else:
        # HTTP get, display login form
        if request.user:
            # Already logged in
            # return HTTPFound(location=login_redirect_view)
            pass

        # Display login form
        return locals()

