This is a Python package for magiclogin, an addon for `Websauna framework <https://websauna.org>`_.

To run this package you need Python 3.4+, PostgresSQL and Redis.

Features
========

Passwordless login with OAuth and email link options.

Installation
============

Setup OAuth credential in ``development.ini`` and ``development-secrets.ini`` according to Websauna documentation.

Example ``development.ini``::

    websauna.social_logins =
        facebook
        google

Example ``development-secrets.ini``::

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


Local development mode
----------------------

Activate the virtual environment of your Websauna application.

Then::

    cd magiclogin  # This is the folder with setup.py file
    pip install -e .


Settings
========

* magiclogin.email_token_expiration_seconds = 300

Running the development website
===============================

Local development machine
-------------------------

Example (OSX / Homebrew)::

    psql create magiclogin_dev
    ws-sync-db websauna/magiclogin/conf/development.ini
    ws-pserve websauna/magiclogin/conf/development.ini --reload

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