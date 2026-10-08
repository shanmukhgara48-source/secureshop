"""SecureShop faculty lab. Direct execution always binds to loopback:8080."""

import os
import secrets
from pathlib import Path

from flask import Flask, g, render_template, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException, SecurityError

from auth import init_auth
from catalogue import collection_description, money, product_image, shop_date
from db import close_db, get_cart_count
from validation import FORM_LIMITS

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
        SECRET_KEY=os.environ.get("SECURESHOP_SECRET_KEY"),
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
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = local_secret()
    app.config["DEBUG"] = False
    app.jinja_env.autoescape = True
    app.teardown_appcontext(close_db)
    init_auth(app)
    app.add_template_filter(money, "money")
    app.add_template_filter(shop_date, "shop_date")

    @app.after_request
    def finish_response(response):
        # INTENTIONAL A05 - omit CSP framing protection, X-Frame-Options, and other security headers.
        # Prevent browser reuse of private pages after logout; this is a cache directive.
        if g.get("user") is not None or request.path in ("/login", "/register", "/admin/login"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.context_processor
    def navigation_state():
        count = get_cart_count(g.user["id"]) if g.get("user") is not None else 0
        return {
            "cart_count": count,
            "has_admin": "admin.products" in app.view_functions,
            "product_image": product_image,
            "collection_description": collection_description,
            "form_limits": FORM_LIMITS,
        }

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template(
            "error.html",
            code=400,
            message="The form expired or could not be verified. Reload the page and try again.",
        ), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        # Host rejection happens before a URL adapter exists; do not render navigation.
        if isinstance(error, SecurityError):
            return "Invalid host. Use http://127.0.0.1:8080.\n", 400
        messages = {
            400: "Please check your request.",
            401: "Please sign in to continue.",
            403: "You do not have permission to view this page.",
            404: "We could not find that page.",
            405: "That action requires a different request method.",
            413: "That request is too large.",
        }
        return render_template(
            "error.html",
            code=error.code,
            message=messages.get(error.code, "The request could not be completed."),
        ), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.error("Request failed (%s)", type(error).__name__)
        return render_template(
            "error.html", code=500, message="Something went wrong. Please try again."
        ), 500

    from routes.admin import bp as admin_bp
    from routes.customer import bp as customer_bp
    from routes.public import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8080, debug=False, use_reloader=False, threaded=False)
