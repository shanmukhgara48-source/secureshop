"""Authenticated shopping actions and order pages."""

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for

from auth import login_required, wants_fragment
from db import get_cart_count, get_db
from validation import FORM_LIMITS, cart_quantity

bp = Blueprint("customer", __name__)


def cart_rows():
    return (
        get_db()
        .execute(
            "SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.stock, p.category "
            "FROM cart_items c JOIN products p ON p.id = c.product_id WHERE c.user_id = ? ORDER BY c.id",
            (g.user["id"],),
        )
        .fetchall()
    )


def cart_feedback(message, success=True, status=200):
    if wants_fragment():
        count = get_cart_count(g.user["id"])
        return render_template(
            "customer/cart_result.html", message=message, success=success, cart_count=count
        ), status
    flash(message, "success" if success else "error")
    return redirect(url_for("customer.cart"), code=303)


@bp.get("/profile")
@login_required
def profile():
    order_count = (
        get_db()
        .execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (g.user["id"],))
        .fetchone()[0]
    )
    return render_template("customer/profile.html", order_count=order_count)


@bp.get("/cart")
@login_required
def cart():
    rows = cart_rows()
    return render_template(
        "customer/cart.html", items=rows, total=sum(row["price"] * row["quantity"] for row in rows)
    )


@bp.post("/cart/add")
@login_required
def cart_add():
    product_id = request.form.get("product_id", type=int)
    quantity = cart_quantity(request.form.get("quantity"))
    if product_id is None or product_id < 1 or quantity is None:
        return cart_feedback("Choose a valid product and quantity (1–99).", False, 400)
    connection = get_db()
    with connection:
        connection.execute("BEGIN IMMEDIATE")
        product = connection.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if product is None:
            return cart_feedback("This product is no longer available.", False, 404)
        existing = connection.execute(
            "SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (g.user["id"], product_id),
        ).fetchone()
        combined = quantity + (existing["quantity"] if existing else 0)
        if combined > min(product["stock"], FORM_LIMITS["quantity_max"]):
            return cart_feedback(
                "That quantity is not available. Please choose fewer items.", False, 400
            )
        connection.execute(
            "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = excluded.quantity",
            (g.user["id"], product_id, combined),
        )
    return cart_feedback("Added to your cart.")


@bp.post("/cart/remove")
@login_required
def cart_remove():
    item_id = request.form.get("item_id", type=int)
    if item_id is None:
        abort(400)
    connection = get_db()
    with connection:
        result = connection.execute(
            "DELETE FROM cart_items WHERE id = ? AND user_id = ?", (item_id, g.user["id"])
        )
    if result.rowcount == 0:
        abort(404)
    flash("Item removed.", "success")
    return redirect(url_for("customer.cart"), code=303)


@bp.post("/checkout")
@login_required
def checkout():
    connection = get_db()
    with connection:
        # Take the write lock before checking stock and constructing the order.
        connection.execute("BEGIN IMMEDIATE")
        rows = cart_rows()
        if not rows:
            flash("Your cart is empty. Add a product first.", "error")
            return redirect(url_for("customer.cart"), code=303)
        if any(row["quantity"] > row["stock"] for row in rows):
            flash("An item no longer has enough stock. Remove it before checkout.", "error")
            return redirect(url_for("customer.cart"), code=303)
        total = sum(row["price"] * row["quantity"] for row in rows)
        order = connection.execute(
            "INSERT INTO orders (user_id, total, status) VALUES (?, ?, ?)",
            (g.user["id"], total, "Placed"),
        )
        order_id = order.lastrowid
        for row in rows:
            connection.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, row["product_id"], row["quantity"], row["price"]),
            )
            connection.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (row["quantity"], row["product_id"]),
            )
        connection.execute("DELETE FROM cart_items WHERE user_id = ?", (g.user["id"],))
    flash("Demo order placed. No payment was taken.", "success")
    return redirect(url_for("customer.order_detail", order_id=order_id), code=303)


@bp.get("/orders")
@login_required
def orders():
    rows = (
        get_db()
        .execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (g.user["id"],))
        .fetchall()
    )
    return render_template("customer/orders.html", orders=rows)


@bp.get("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    connection = get_db()
    # INTENTIONAL A01 - detail checks login but omits order ownership in this lab baseline.
    order = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if order is None:
        abort(404)
    owner = connection.execute(
        "SELECT username FROM users WHERE id = ?", (order["user_id"],)
    ).fetchone()
    items = connection.execute(
        "SELECT oi.quantity, oi.unit_price, p.name, p.category, p.id AS product_id FROM order_items oi "
        "JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ? ORDER BY oi.id",
        (order_id,),
    ).fetchall()
    return render_template("customer/order_detail.html", order=order, owner=owner, items=items)


@bp.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("public.home"), code=303)
