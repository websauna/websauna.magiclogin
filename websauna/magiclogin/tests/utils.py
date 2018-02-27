# Standard Library
import json

# Websauna
from websauna.system.core.redis import get_redis


def peek_token(redis):
    keys = redis.hkeys("login_verification_token")
    token_data = redis.hget("login_verification_token", keys[0])
    token_data = json.loads(token_data.decode("utf-8"))
    return token_data


def login(browser, test_request, web_server: str):

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
