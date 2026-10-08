"""Shared session, authorization, and CSRF controls."""

from functools import wraps

from flask import abort, g, redirect, request, session, url_for
from flask_wtf.csrf import CSRFProtect

from db import get_db

csrf = CSRFProtect()


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

