# Websauna
from websauna.magiclogin.tests import requireloginexamples
from websauna.magiclogin.tests.utils import login
from websauna.magiclogin.tests.utils import peek_token
from websauna.system.core.redis import get_redis


def test_login_actions_get_email(dbsession, browser, web_server, test_request):
    """See that login actions are correctly executed when user hits example page and does GET action."""

    redis = get_redis(test_request)

    requireloginexamples._was_logged_in = None

    b = browser
    b.visit(web_server + "/require_login_example_page")

    assert b.is_element_present_by_css("#heading-require-login-example")

    b.find_by_css("#btn-get-example").click()

    assert b.is_element_present_by_css("#panel-magic-login")

    # Move to email sign in
    b.find_by_css("#nav-sign-in-by-email").click()

    b.fill("email", "foobar@example.com")
    b.find_by_css("button[name='confirm']").click()

    assert b.is_element_present_by_css("#panel-magic-login-email-sent")
    b.visit("{}/verify-email-login/{}".format(web_server, peek_token(redis)["token"]))

    # User lands after post login actions
    assert not b.is_element_present_by_css("#msg-you-are-logged-in")
    assert b.is_element_present_by_css("#msg-example-get-view-success")

    assert requireloginexamples._was_logged_in is False


def test_already_logged_actions_get(dbsession, browser, web_server, test_request):
    """Already logged in goes directly to GET page."""

    requireloginexamples._was_logged_in = None

    login(browser, test_request, web_server)

    b = browser
    b.visit(web_server + "/require_login_example_page")
    b.find_by_css("#btn-get-example").click()

    assert b.is_element_present_by_css("#msg-example-get-view-success")

    assert requireloginexamples._was_logged_in is True


def test_login_actions_post_email(dbsession, browser, web_server, test_request):
    """See that login actions are correctly executed when user hits example page and does POST action."""

    redis = get_redis(test_request)

    requireloginexamples._was_logged_in = None
    requireloginexamples._captured_post_params = None

    b = browser
    b.visit(web_server + "/require_login_example_page")

    assert b.is_element_present_by_css("#heading-require-login-example")

    b.find_by_css("#btn-post-example").click()

    assert b.is_element_present_by_css("#panel-magic-login")

    # Move to email sign in
    b.find_by_css("#nav-sign-in-by-email").click()

    b.fill("email", "foobar@example.com")
    b.find_by_css("button[name='confirm']").click()

    assert b.is_element_present_by_css("#panel-magic-login-email-sent")
    b.visit("{}/verify-email-login/{}".format(web_server, peek_token(redis)["token"]))

    # User lands after post login actions
    assert not b.is_element_present_by_css("#msg-you-are-logged-in")
    assert b.is_element_present_by_css("#msg-example-post-view-success")

    assert requireloginexamples._was_logged_in is False
    assert requireloginexamples._captured_post_params["test_value"] == "88"


def test_already_logged_actions_post(dbsession, browser, web_server, test_request):
    """Already logged in goes directly to POST page."""

    requireloginexamples._was_logged_in = None
    requireloginexamples._captured_post_params = None

    login(browser, test_request, web_server)

    b = browser
    b.visit(web_server + "/require_login_example_page")

    b.find_by_css("#btn-post-example").click()

    assert b.is_element_present_by_css("#msg-example-post-view-success")

    assert requireloginexamples._was_logged_in is True
    assert requireloginexamples._captured_post_params["test_value"] == "88"
