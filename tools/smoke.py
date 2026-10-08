"""Normal customer/admin demo journeys only; this changes the synthetic database."""

import sys
from uuid import uuid4

from replay import run_with_log


def require(result, status=200):
    if result.status != status:
        raise RuntimeError(f"Expected HTTP {status}, received {result.status}.")
    return result


def smoke(client, emit):
    suffix = uuid4().hex[:10]
    username = f"learner_{suffix}"
    password = "LocalSmoke!2026"
    emit("Functional test changes local synthetic data. Stop the server and reset before a scan.")
    require(client.get("/"))
    require(client.form_post("/register", {"username": username, "email": f"{username}@example.invalid",
                                          "password": password}, "/register"))
    client.login(username, password)
    emit("PASS register → login")
    search = require(client.get("/search?q=notebook"))
    if int(search.page().marker("data-result-count") or "0") < 1:
        raise RuntimeError("The ordinary notebook search returned no products.")
    require(client.get("/products/1"))
    require(client.form_post("/cart/add", {"product_id": "1", "quantity": "2"}, "/products/1"))
    cart = require(client.get("/cart"))
    if not cart.page().item_ids:
        raise RuntimeError("The cart did not contain the added product.")
    if cart.page().marker("data-cart-total") != "49800":
        raise RuntimeError("The seeded notebook cart total was not ₹498.00.")
    require(client.form_post("/cart/remove", {"item_id": cart.page().item_ids[0]}, "/cart"))
    if require(client.get("/cart")).page().item_ids:
        raise RuntimeError("Removing the cart item did not empty the cart.")
    require(client.form_post("/cart/add", {"product_id": "1", "quantity": "2"}, "/products/1"))
    emit("PASS search → product → add → cart → remove → add")
    order = require(client.form_post("/checkout", {}, "/cart"))
    order_id = order.page().marker("data-order-id")
    if not order_id or order.page().marker("data-order-owner") != username:
        raise RuntimeError("Checkout did not produce the customer's own order.")
    if order.page().marker("data-order-total") != "49800":
        raise RuntimeError("Checkout did not preserve the server-calculated ₹498.00 total.")
    history = require(client.get("/orders"))
    if order_id not in history.page().markers.get("data-order-id", []):
        raise RuntimeError("The new order did not appear in order history.")
    require(client.get("/profile"))
    logged_out = require(client.form_post("/logout", {}, "/profile"))
    if logged_out.page().marker("data-authenticated") != "false":
        raise RuntimeError("Logout did not clear the authenticated session.")
    emit("PASS checkout → own order → history → profile → logout")
    client.login("admin", "AdminDemo!2026", admin=True)
    before = set(require(client.get("/admin/products")).page().markers.get("data-product-id", []))
    values = {"name": f"Demo tray {suffix}", "description": "Synthetic admin smoke-test product.",
              "price": "12.50", "category": "Study", "stock": "5"}
    created = require(client.form_post("/admin/products/new", values, "/admin/products/new"))
    added = set(created.page().markers.get("data-product-id", [])) - before
    if len(added) != 1:
        raise RuntimeError("Admin create did not produce one product.")
    product_id = added.pop()
    values.update(name=f"Updated tray {suffix}", price="15.75", stock="7")
    edit_path = f"/admin/products/{product_id}/edit"
    require(client.form_post(edit_path, values, edit_path))
    edited = require(client.get(edit_path)).body
    if 'value="15.75"' not in edited or values["name"] not in edited:
        raise RuntimeError("The edited product values were not saved.")
    deleted = require(client.form_post(f"/admin/products/{product_id}/delete", {}, "/admin/products"))
    if product_id in deleted.page().markers.get("data-product-id", []):
        raise RuntimeError("Admin delete did not remove the new product.")
    users = require(client.get("/admin/users"))
    if username not in users.body:
        raise RuntimeError("The registered synthetic account is missing from the user list.")
    require(client.form_post("/logout", {}, "/profile"))
    emit("PASS admin login → create → edit → delete → user list → logout")
    emit("PASS complete normal demo journey; reset restores the original synthetic seed state.")


if __name__ == "__main__":
    sys.exit(run_with_log("smoke", smoke))
