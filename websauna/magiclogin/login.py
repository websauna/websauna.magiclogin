"""Passwordless login with email or SMS functionality."""

# Standard Library
import json
import logging
import random
import string
import time

# Pyramid
from pyramid.httpexceptions import HTTPFound

# Websauna
from websauna.system.core import messages
from websauna.system.core.redis import get_redis
from websauna.system.http import Request
from websauna.system.mail import send_templated_mail
from websauna.system.user.events import UserCreated
from websauna.system.user.models import User
from websauna.system.user.utils import get_login_service
from websauna.utils.time import now


#: Under which hset we store user login data
LOGIN_VERIFICATION_REDIS_HKEY = "login_verification_token"


EMAIL_TOKEN_LENGTH = 16


logger = logging.getLogger(__name__)


def rand_string(length=5):
    """http://stackoverflow.com/a/23728630/315168"""
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))


def set_verification_token(request, token_type, user_id, next_url=None):
    redis = get_redis(request.registry)

    email_token_expiration_time = int(request.registry.settings.get("magiclink.email_token_expiration_seconds", 3600))

    token = rand_string(length=EMAIL_TOKEN_LENGTH)
    expires = time.time() + email_token_expiration_time

    data = {
        "token_type": token_type,
        "expires": expires,
        "token": token,
        "email": user_id,
        "next_url": next_url,
    }

    redis.hset(LOGIN_VERIFICATION_REDIS_HKEY, token, json.dumps(data))
    return token, data


def get_or_create_email_user(request: Request, email: str) -> User:
    """Fetch existing user or create new based on email."""
    dbsession = request.dbsession

    u = dbsession.query(User).filter_by(email=email).first()
    if u is not None:
        u.first_login = False
        return u

    u = User(email=email)
    u.registration_source = "email"
    u.activated_at = now()
    u.first_login = True

    dbsession.add(u)
    dbsession.flush()

    request.registry.notify(UserCreated(request, u))
    return u


def verify_email_login(request: Request, token: str):
    """Verify email login token."""

    redis = get_redis(request.registry)

    def fail(msg="Sign in link invalid. Please try again."):
        messages.add(request, kind="error", msg=msg, msg_id="msg-bad-email-token")
        return HTTPFound(request.route_url("login"))

    # Hackety hacky by our Russian friends again?
    if len(token) != EMAIL_TOKEN_LENGTH:
        logger.warn("Bad token: %s", token)
        return fail()

    token_data = redis.hget(LOGIN_VERIFICATION_REDIS_HKEY, token)
    if not token_data:
        return fail()

    # Allow use the code only once, then erase
    redis.hdel(LOGIN_VERIFICATION_REDIS_HKEY, token)

    data = json.loads(token_data.decode("utf-8"))

    # Only verify email tokens in this view
    assert data["token_type"] == "email"

    if time.time() > data["expires"]:
        return fail("Sign in link expired. Please try again.")

    email = data["email"]

    # Create new user or get existing user based on this email
    user = get_or_create_email_user(request, email)
    login_service = get_login_service(request)

    # Returns HTTPRedirect taking user to post-login page
    return login_service.authenticate_user(user, login_source="email")


def start_email_login(request: Request, email: str):
    request.session["email"] = email
    token, data = set_verification_token(request, "email", email)
    verify_link = request.route_url("verify_email_login", token=token)
    verify_minutes = int(int(request.registry.settings.get("magiclink.email_token_expiration_seconds", 300)) / 60)
    logger.info("Sending email login verification email to %s", email)
    send_templated_mail(request, [email], "magiclogin/email/verify_email", dict(verify_link=verify_link, verify_minutes=verify_minutes))
