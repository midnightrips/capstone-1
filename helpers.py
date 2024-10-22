"""Helper functions"""

from flask import session, redirect, flash, url_for

CURR_USER_KEY = "curr_user"

def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

def unauthorized():
    """Flash and redirect if unauthorized access."""
    flash("Access unauthorized.", "danger")