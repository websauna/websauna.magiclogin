This is a Python package for magiclogin, an addon for `Websauna framework <https://websauna.org>`_.

To run this package you need Python 3.4+, PostgresSQL and Redis.

Features
========

* Passwordless login with OAuth and email link options.

* Throttle protection against brute forcing and spam

* Interstitial page to require user to login and then continue what ever HTTP GET/POST action user was performing

Screenshots

.. image:: https://github.com/websauna/websauna.magiclogin/raw/master/screenshots/login.png
    :width: 400px

.. image:: https://github.com/websauna/websauna.magiclogin/raw/master/screenshots/email.png
    :width: 400px

Installation
============

Setup OAuth credential in ``development.ini`` and ``development-secrets.ini`` according to Websauna documentation.

Example ``development.ini``::

    websauna.social_logins =
        facebook
        google

Example ``development-secrets.ini`` bits::

    [facebook]
    class = authomatic.providers.oauth2.Facebook
    consumer_key = xxx
    consumer_secret = yyy
    scope = user_about_me, email
    mapper = websauna.system.user.social.FacebookMapper

    [google]
    class = websauna.system.user.googleoauth.Google
    consumer_key = xxx
    consumer_secret = yyy
    mapper = websauna.system.user.social.GoogleMapper
    scope = profile email

Copy bits from ``demo.py`` to your application initializer.

Settings
========

Available INI settings::

    # Throttle email login endpoints to this window
    magiclogin.login_email_throttle = 50/3600

    # How fast email login link dies
    magiclogin.email_token_expiration_seconds = 300

    # Text shown on the login panel
    magiclogin.login_slogan = Your login text goes here

You might also have long, secure, sessions in production::

    # Set session length to one year
    redis.sessions.cookie_max_age = 31536000
    redis.sessions.cookie_secure = True
    redis.sessions.cookie_httponly = True

Running the development website
===============================

Local development machine
-------------------------

Example (OSX / Homebrew)::

    createdb magiclogin_dev
    ws-sync-db websauna/magiclogin/conf/development.ini
    ws-pserve websauna/magiclogin/conf/development.ini --reload


You can visit::

    http://localhost:6543/login

    http://localhost:6543/require_login_example_page

Running the test suite
======================

First create test database::

    # Create database used for unit testing
    psql create magiclogin_test

Install test and dev dependencies (run in the folder with ``setup.py``)::

    pip install -e ".[dev,test]"

Run test suite using py.test running::

    py.test

More information
================

Please see https://websauna.org/