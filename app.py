"""SecureShop faculty lab. Direct execution always binds to loopback:8080."""

import os
import secrets
from pathlib import Path

from flask import Flask, g, render_template, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException

from auth import csrf, load_user
from db import close_db, get_db

ROOT = Path(__file__).resolve().parent


def local_secret():
    directory = ROOT / ".instance"
    directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / "session.key"
    if not path.exists():
        try:
            with path.open("x", encoding="ascii") as file:
                path.chmod(0o600)
                file.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    value = path.read_text(encoding="ascii").strip()
    if len(value) < 64:
        raise RuntimeError("Local signing key is invalid.")
    return value


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECURESHOP_SECRET_KEY") or local_secret(),
        DATABASE=str(ROOT / "shop.db"),
        DEBUG=False,
        SESSION_COOKIE_NAME="secureshop_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,  # Lab uses plain HTTP on loopback only.
        TRUSTED_HOSTS=["127.0.0.1"],
        MAX_CONTENT_LENGTH=64 * 1024,
        MAX_FORM_MEMORY_SIZE=16 * 1024,
        WTF_CSRF_TIME_LIMIT=3600,
    )
    if test_config:
        app.config.update(test_config)
    app.config["DEBUG"] = False
    app.jinja_env.autoescape = True
    app.teardown_appcontext(close_db)
    app.before_request(load_user)
    csrf.init_app(app)

    @app.after_request
    def finish_response(response):
        # Prevent browser reuse of private pages after logout; this is a cache directive.
        if g.get("user") is not None or request.path in ("/login", "/register", "/admin/login"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.template_filter("money")
    def money(paise):
        return f"₹{int(paise) / 100:,.2f}"

    @app.context_processor
    def navigation_state():
        count = 0
        if g.get("user") is not None:
            count = get_db().execute(
                "SELECT COALESCE(SUM(quantity), 0) FROM cart_items WHERE user_id = ?", (g.user["id"],)
            ).fetchone()[0]
        return {"cart_count": count, "has_admin": "admin.products" in app.view_functions}

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template("error.html", code=400, message="The form expired or could not be verified. Reload the page and try again."), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {400: "Please check your request.", 401: "Please sign in to continue.",
                    403: "You do not have permission to view this page.", 404: "We could not find that page.",
                    405: "That action requires a different request method.", 413: "That request is too large."}
        return render_template("error.html", code=error.code, message=messages.get(error.code, "The request could not be completed.")), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.error("Request failed (%s)", type(error).__name__)
        return render_template("error.html", code=500, message="Something went wrong. Please try again."), 500

    from routes.public import bp as public_bp
    from routes.customer import bp as customer_bp
    from routes.admin import bp as admin_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8080, debug=False, use_reloader=False, threaded=False)
