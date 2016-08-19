import random
import logging
import json
import time

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response

from pyramid_sms.utils import normalize_us_phone_number
from pyramid_sms.outgoing import send_templated_sms

from websauna.system.core.redis import get_redis
from websauna.system.http import Request


LOGIN_VERIFICATION_REDIS_HKEY = "login_verification_token"


logger = logging.getLogger(__name__)


class SMSTokenVerifyException(Exception):
    """Token verification fails for a reason or another."""


def set_verification_token(request, token_type, phone_number, next_url=None):
    redis = get_redis(request.registry)

    email_token_expiration_time = int(request.registry.settings.get("smslogin.email_token_expiration_time", 300))

    token = 10000000 + random.randint(0, 80000000)
    expires = time.time() + email_token_expiration_time

    if token_type == "phone_number":
        manual_code = 1000 + random.randint(0, 8999)
    else:
        manual_code = None

    data = {
        "token_type": token_type,
        "expires": expires,
        "token": token,
        "next_url": next_url,
        "phone_number": phone_number,
        "manual_code": str(manual_code),
    }

    request.session["phone_number"] = phone_number

    redis.hset(LOGIN_VERIFICATION_REDIS_HKEY, phone_number, json.dumps(data))
    return token, data


def prepare_phone_verification(request: Request, phone_number: str, next_url=None) -> str:
    """Set up a phone verification process for the session in the request.

    :param request:
    :param phone_number:
    :param next_url: Optional recorded next URL where the user should land after login.
    :return: The manual code the user needs to enter
    """
    phone_number = normalize_us_phone_number(phone_number)
    token, data = set_verification_token(request, "phone_number", phone_number, next_url=next_url)
    context = dict(manual_code=data["manual_code"])
    send_templated_sms(request, "login/sms/phone_verification.txt", context, phone_number,)
    return data["manual_code"]


def verify_token(request: Request, manual_code: str):
    """Verify SMS login token.

    :param request:
    :param token: Code entered by the user
    :param exception: Use this factory to produce an exception if validation fails with an error message.
    :return: Verified phone number
    """

    redis = get_redis(request.registry)

    phone_number = request.session.get("phone_number")
    if not phone_number:
        raise SMSTokenVerifyException("Please enter phone number first.")

    token_data = redis.hget(LOGIN_VERIFICATION_REDIS_HKEY, phone_number)
    if not token_data:
        raise SMSTokenVerifyException("No SMS login in process for current user.")

    # Allow use the code only once, then erase
    redis.hdel(LOGIN_VERIFICATION_REDIS_HKEY, phone_number)

    data = json.loads(token_data.decode("utf-8"))

    # Only phone number tokens in this view
    if data["token_type"] != "phone_number":
        raise SMSTokenVerifyException('token type mismatch, must be phone, was {token_type}'.format(**data))

    if time.time() > data["expires"]:
        raise SMSTokenVerifyException("Login link expired. Please try again.")

    if str(data["manual_code"]) != manual_code:
        raise SMSTokenVerifyException("The verification code did not match. Please try again.")

    phone_number = data["phone_number"]

    return phone_number






