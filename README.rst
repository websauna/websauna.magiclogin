This is a Python package for magiclogin, an addon for `Websauna framework <https://websauna.org>`_.

To run this package you need Python 3.4+, PostgresSQL and Redis.

Installation
============

Local development mode
-----------------------

Activate the virtual environment of your Websauna application.

Then::

    cd magiclogin  # This is the folder with setup.py file
    pip install -e .

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