"""Shared session, authorization, and CSRF controls."""

import time
from functools import wraps

from flask import abort, current_app, g, redirect, request, session, url_for
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db
from validation import FORM_LIMITS, valid_password_length

csrf = CSRFProtect()
FAILED_LOGIN_LIMIT = 5
LOGIN_WINDOW_SECONDS = 60
# A missing account still incurs the same expensive password-verification work.
DUMMY_HASH = generate_password_hash("DummyValidationOnly!2026")


def init_auth(app):
    """Keep mutable authentication state specific to this app instance."""
    app.extensions["login_attempts"] = {}
    app.before_request(load_user)
    csrf.init_app(app)


def authenticate(username, password, required_role=None):
    """Public and admin logins share verification, limits, and generic failures."""
    attempts = current_app.extensions["login_attempts"]
    address = request.remote_addr or "local"
    now = time.monotonic()
    failures = [time_ for time_ in attempts.get(address, []) if now - time_ < LOGIN_WINDOW_SECONDS]
    attempts[address] = failures
    if len(failures) >= FAILED_LOGIN_LIMIT:
        return None

    user = None
    if len(username) <= FORM_LIMITS["username_max"]:
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    stored_hash = user["password_hash"] if user is not None else DUMMY_HASH
    valid_password = check_password_hash(stored_hash, password[: FORM_LIMITS["password_max"] + 1])
    valid_role = user is not None and (required_role is None or user["role"] == required_role)
    if valid_role and valid_password_length(password) and valid_password:
        attempts.pop(address, None)
        return user
    failures.append(now)
    return None


def wants_fragment():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def load_user():
    g.user = None
    user_id = session.get("user_id")
    if isinstance(user_id, int):
        g.user = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if g.user is None:
            session.clear()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            if wants_fragment():
                abort(401)
            return redirect(url_for("public.login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            if wants_fragment():
                abort(401)
            return redirect(url_for("admin.login"))
        # Database role is authoritative, even when a session carries a cached role.
        if g.user["role"] != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def establish_session(user):
    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]
