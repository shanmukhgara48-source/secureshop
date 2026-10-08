"""Administrator login and local product/user management."""

import re
import sqlite3
from decimal import Decimal

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from auth import admin_required, authenticate, establish_session
from catalogue import CATEGORIES
from db import get_db
from validation import FORM_LIMITS, MAX_PRICE_PAISE

bp = Blueprint("admin", __name__, url_prefix="/admin")
PRICE = re.compile(r"[0-9]{1,6}(?:\.[0-9]{1,2})?\Z", re.ASCII)
STOCK = re.compile(r"[0-9]{1,5}\Z", re.ASCII)


def product_rows():
    return get_db().execute("SELECT * FROM products ORDER BY id").fetchall()


def product_values(product=None):
    if product is None:
        return {"name": "", "description": "", "price": "", "category": "Study", "stock": "0"}
    return {
        "name": product["name"],
        "description": product["description"],
        "price": f"{product['price'] // 100}.{product['price'] % 100:02d}",
        "category": product["category"],
        "stock": str(product["stock"]),
    }


def validate_product():
    values = {
        name: request.form.get(name, "").strip()
        for name in ("name", "description", "price", "category", "stock")
    }
    if not 1 <= len(values["name"]) <= FORM_LIMITS["product_name_max"]:
        return values, None, "Enter a product name between 1 and 80 characters."
    if len(values["description"]) > FORM_LIMITS["description_max"]:
        return values, None, "Keep the description within 500 characters."
    if values["category"] not in CATEGORIES:
        return values, None, "Choose one of the four campus collections."
    if not PRICE.fullmatch(values["price"]):
        return values, None, "Enter a positive rupee price with at most two decimal places."
    # Decimal avoids rounding money through binary floating-point values.
    price = int(Decimal(values["price"]) * 100)
    if not 1 <= price <= MAX_PRICE_PAISE:
        return values, None, "The price must be between ₹0.01 and ₹999,999.99."
    if not STOCK.fullmatch(values["stock"]) or int(values["stock"]) > FORM_LIMITS["stock_max"]:
        return values, None, "Stock must be a whole number between 0 and 10,000."
    data = (values["name"], values["description"], price, values["category"], int(values["stock"]))
    return values, data, None


@bp.route("/login", methods=["GET", "POST"])
def login():
    # The login form is the public exception; all management routes require admin.
    if g.user is not None:
        if g.user["role"] != "admin":
            abort(403)
        return redirect(url_for("admin.products"))
    username = ""
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        user = authenticate(username, request.form.get("password", ""), required_role="admin")
        if user is not None:
            establish_session(user)
            flash("You're signed in to the local administrator area.", "success")
            return redirect(url_for("admin.products"))
        error = "The username or password is incorrect."
    return render_template("admin/login.html", username=username, error=error), (
        400 if error else 200
    )


@bp.get("/products")
@admin_required
def products():
    return render_template("admin/products.html", products=product_rows(), error=None)


@bp.route("/products/new", methods=["GET", "POST"])
@admin_required
def new_product():
    values = product_values()
    error = None
    if request.method == "POST":
        values, data, error = validate_product()
        if error is None:
            connection = get_db()
            with connection:
                connection.execute(
                    "INSERT INTO products (name, description, price, category, stock) VALUES (?, ?, ?, ?, ?)",
                    data,
                )
            flash("Product added to the local catalogue.", "success")
            return redirect(url_for("admin.products"), code=303)
    return render_template(
        "admin/product_form.html", values=values, error=error, categories=CATEGORIES, product=None
    ), (400 if error else 200)


@bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    connection = get_db()
    product = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        abort(404)
    values = product_values(product)
    error = None
    if request.method == "POST":
        values, data, error = validate_product()
        if error is None:
            with connection:
                connection.execute(
                    "UPDATE products SET name = ?, description = ?, price = ?, category = ?, stock = ? WHERE id = ?",
                    (*data, product_id),
                )
            flash("Product updated. Existing orders keep their original prices.", "success")
            return redirect(url_for("admin.products"), code=303)
    return render_template(
        "admin/product_form.html",
        values=values,
        error=error,
        categories=CATEGORIES,
        product=product,
    ), (400 if error else 200)


@bp.post("/products/<int:product_id>/delete")
@admin_required
def delete_product(product_id):
    connection = get_db()
    if connection.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone() is None:
        abort(404)
    try:
        with connection:
            connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
    except sqlite3.IntegrityError:
        # Foreign-key restrictions protect cart contents and historical order items.
        error = (
            "This product is in a cart or previous order, so it cannot be deleted. Edit it instead."
        )
        return render_template("admin/products.html", products=product_rows(), error=error), 409
    flash("Product removed from the local catalogue.", "success")
    return redirect(url_for("admin.products"), code=303)


@bp.get("/users")
@admin_required
def users():
    rows = (
        get_db()
        .execute("SELECT id, username, email, role, created_at FROM users ORDER BY id")
        .fetchall()
    )
    return render_template("admin/users.html", users=rows)
