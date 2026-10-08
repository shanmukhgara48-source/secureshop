"""Public catalogue and account entry points."""

import re
import sqlite3
import time

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from auth import establish_session
from db import get_db

bp = Blueprint("public", __name__)
USERNAME = re.compile(r"[A-Za-z0-9_]{3,32}\Z", re.ASCII)
SYNTHETIC_EMAIL = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+invalid\Z",
    re.ASCII | re.IGNORECASE,
)
# Missing accounts still incur the same password-verification work.
DUMMY_HASH = generate_password_hash("DummyValidationOnly!2026")
FAILED_LOGINS = {}


def authenticate(username, password, required_role=None):
    """Verify credentials; public and admin entry points share the local throttle."""
    address = request.remote_addr or "local"
    now = time.monotonic()
    failures = [attempt for attempt in FAILED_LOGINS.get(address, []) if now - attempt < 60]
    FAILED_LOGINS[address] = failures
    if len(failures) >= 5:
        return None
    user = None
    if len(username) <= 32:
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    stored_hash = user["password_hash"] if user is not None else DUMMY_HASH
    valid_password = check_password_hash(stored_hash, password[:129])
    if (user is not None and 10 <= len(password) <= 128 and valid_password
            and (required_role is None or user["role"] == required_role)):
        FAILED_LOGINS.pop(address, None)
        return user
    failures.append(now)
    return None


def catalogue_categories():
    return [row["category"] for row in get_db().execute(
        "SELECT DISTINCT category FROM products ORDER BY category"
    ).fetchall()]


@bp.get("/")
def home():
    database = get_db()
    featured = database.execute("SELECT * FROM products ORDER BY id LIMIT 4").fetchall()
    product_count = database.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    return render_template("public/home.html", featured=featured,
                           categories=catalogue_categories(), product_count=product_count)


@bp.get("/products")
def products():
    items = get_db().execute("SELECT * FROM products ORDER BY id").fetchall()
    return render_template("public/catalogue.html", products=items,
                           categories=catalogue_categories(), query="",
                           is_search=False, result_count=len(items))


@bp.get("/products/<int:product_id>")
def product_detail(product_id):
    product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        abort(404)
    return render_template("public/product_detail.html", product=product)


@bp.get("/search")
def search():
    query = request.args.get("q", "")
    if len(query) > 120:
        abort(400)
    try:
        statement = f"SELECT * FROM products WHERE name LIKE '%{query}%' OR description LIKE '%{query}%' ORDER BY id"  # INTENTIONAL A03 - fix in remediation phase.
        # Normal execute accepts one statement; this lab endpoint only constructs a SELECT.
        items = get_db().execute(statement).fetchall()
    except sqlite3.Error:
        flash("That search could not be completed. Please try another search.", "error")
        items = []
    return render_template("public/catalogue.html", products=items,
                           categories=catalogue_categories(), query=query,
                           is_search=True, result_count=len(items))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user is not None:
        return redirect(url_for("public.products"))
    username = ""
    email = ""
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not USERNAME.fullmatch(username):
            error = "Use 3–32 letters, numbers, or underscores for your username."
        elif len(email) > 254 or not SYNTHETIC_EMAIL.fullmatch(email):
            error = "Use a synthetic email ending in .invalid, such as learner@example.invalid."
        elif not 10 <= len(password) <= 128:
            error = "Use a password between 10 and 128 characters."
        else:
            database = get_db()
            try:
                with database:
                    # Registration always creates a customer; no form role is accepted.
                    database.execute(
                        "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                        (username, email, generate_password_hash(password), "customer"),
                    )
            except sqlite3.IntegrityError:
                error = "That username or email is unavailable. Please choose another."
            else:
                flash("Your local account is ready. Sign in to start shopping.", "success")
                return redirect(url_for("public.login"))
    return render_template("public/register.html", username=username, email=email,
                           error=error), (400 if error else 200)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("public.products"))
    username = ""
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = authenticate(username, password)
        if user is not None:
            establish_session(user)
            flash("Welcome back. You're signed in to the local shop.", "success")
            return redirect(url_for("public.products"))
        error = "The username or password is incorrect."
    return render_template("public/login.html", username=username, error=error), (400 if error else 200)
