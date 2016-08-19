"""An example py.test functional test case."""
import json

from sqlalchemy.orm.session import Session

import transaction
from splinter.driver import DriverAPI
from websauna.system.core.redis import get_redis
from websauna.system.user.models import User


def peek_token(redis):
    keys = redis.hkeys("login_verification_token")
    token_data = redis.hget("login_verification_token", keys[0])
    token_data = json.loads(token_data.decode("utf-8"))
    return token_data


def test_email_login(web_server:str, browser:DriverAPI, dbsession:Session, test_request):
    """See that we can sign up / sign in through email login."""

    # Reset login key status before proceeding
    redis = get_redis(test_request)
    redis.delete("login_verification_token")

    b = browser
    b.visit(web_server + "/login")

    assert b.is_element_present_by_css("#panel-magic-login")

    # Move to email sign in
    b.find_by_css("#nav-sign-in-by-email").click()

    b.fill("email", "foobar@example.com")
    b.find_by_css("button[name='confirm']").click()

    assert b.is_element_present_by_css("#panel-magic-login-email-sent")
    b.visit("{}/verify-email-login/{}".format(web_server, peek_token(redis)["token"]))
    assert b.is_element_present_by_css("#msg-you-are-logged-in")

    # Check we created a sane user
    with transaction.manager:
        u = dbsession.query(User).first()
        assert u.email  == "foobar@example.com"
        assert u.first_login

    #
    # Do it again so we capture both new user and old user flows
    #

    b.find_by_css("#nav-logout").click()
    b.visit(web_server + "/login-email")
    b.fill("email", "foobar@example.com")
    b.find_by_css("button[name='confirm']").click()

    assert b.is_element_present_by_css("#panel-magic-login-email-sent")
    b.visit("{}/verify-email-login/{}".format(web_server, peek_token(redis)["token"]))
    assert b.is_element_present_by_css("#msg-you-are-logged-in")

    # Check the user is still sane
    with transaction.manager:
        u = dbsession.query(User).first()
        assert u.email == "foobar@example.com"
        assert not u.first_login


def test_email_login_bad_token(web_server:str, browser:DriverAPI, dbsession:Session):
    """Crap token provides meaningful user error message.   """
    b = browser
    b.visit(web_server + "/verify-email-login/xxx")
    assert b.is_element_present_by_css("#msg-bad-email-token")
