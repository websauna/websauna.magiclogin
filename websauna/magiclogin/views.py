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
                appstruct = form.validate(request.POST.items())
                start_email_login(request, appstruct["email"])
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
