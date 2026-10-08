"""Exercise public HTTP and database contracts without touching the live lab.

Run from the project directory: python -m unittest discover -v
These are business/security regression tests, not a security scanner. The
existing replay helper remains the deliberate-weakness comparison tool.
"""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import check_password_hash

from app import create_app
from catalogue import product_image
from seed import reset_database

ORIGIN = "http://127.0.0.1:8080"
TABLES = ("users", "products", "cart_items", "orders", "order_items")


class Page(HTMLParser):
    """Read form tokens and semantic markers without depending on page copy."""

    def __init__(self, response):
        super().__init__(convert_charrefs=True)
        self.csrf = None
        self.order_ids = []
        self.errors = []
        self._error_depth = 0
        self._error_parts = []
        self.feed(response.get_data(as_text=True))

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "meta" and attrs.get("name") == "csrf-token":
            self.csrf = attrs.get("content")
        if tag == "input" and attrs.get("name") == "csrf_token":
            self.csrf = attrs.get("value")
        if attrs.get("data-order-id"):
            self.order_ids.append(int(attrs["data-order-id"]))
        classes = attrs.get("class", "").split()
        if self._error_depth:
            self._error_depth += 1
        elif attrs.get("role") == "alert" or "notice-error" in classes:
            self._error_depth = 1
            self._error_parts = []

    def handle_endtag(self, tag):
        if self._error_depth:
            self._error_depth -= 1
            if self._error_depth == 0:
                self.errors.append(" ".join("".join(self._error_parts).split()))

    def handle_data(self, data):
        if self._error_depth:
            self._error_parts.append(data)


class SecureShopTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="secureshop-tests-")
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "shop.db"
        reset_database(self.database)
        self.config = {
            "TESTING": True,
            "DATABASE": str(self.database),
            "SECRET_KEY": "temporary-test-signing-key-" * 3,
        }
        self.app = create_app(self.config)
        self.client = self.app.test_client()

    def query(self, statement, parameters=()):
        with closing(sqlite3.connect(self.database)) as connection:
            return connection.execute(statement, parameters).fetchall()

    def change(self, statement, parameters=()):
        with closing(sqlite3.connect(self.database)) as connection, connection:
            connection.execute(statement, parameters)

    def state(self):
        # The table identifiers below are fixed test constants, never user input.
        return {table: self.query(f"SELECT * FROM {table} ORDER BY id") for table in TABLES}

    def get(self, path, client=None):
        return (client or self.client).get(path, base_url=ORIGIN)

    def post(self, path, data=None, client=None, ajax=False):
        client = client or self.client
        token = Page(self.get("/products", client)).csrf
        self.assertTrue(token, "The page must provide a real CSRF token.")
        headers = {"X-Requested-With": "XMLHttpRequest"} if ajax else {}
        return client.post(
            path, data={**(data or {}), "csrf_token": token}, headers=headers, base_url=ORIGIN
        )

    def login(self, username="customer_a", password="CustomerA!2026", client=None, admin=False):
        path = "/admin/login" if admin else "/login"
        response = self.post(path, {"username": username, "password": password}, client)
        self.assertEqual(response.status_code, 302)
        return response

    def register(self, **overrides):
        values = {
            "username": "lab_learner",
            "email": "learner@example.invalid",
            "password": "LocalLearner!2026",
        }
        values.update(overrides)
        return self.post("/register", values)

    def test_registration_ignores_role_and_hashes_password(self):
        self.assertEqual(self.register(role="admin").status_code, 302)
        role, password_hash = self.query(
            "SELECT role, password_hash FROM users WHERE username = ?", ("lab_learner",)
        )[0]
        self.assertEqual(role, "customer")
        self.assertNotEqual(password_hash, "LocalLearner!2026")
        self.assertTrue(check_password_hash(password_hash, "LocalLearner!2026"))
        self.login("lab_learner", "LocalLearner!2026")
        self.assertEqual(self.get("/admin/users").status_code, 403)

    def test_registration_requires_valid_synthetic_account_fields(self):
        invalid = (
            {"email": "learner@example.com"},
            {"email": "missing-domain"},
            {"username": "ab"},
            {"username": "two words"},
            {"password": "short"},
            {"password": "x" * 129},
        )
        before = self.state()
        for values in invalid:
            with self.subTest(fields=tuple(values)):
                self.assertEqual(self.register(**values).status_code, 400)
                self.assertEqual(self.state(), before)

    def test_registration_rejects_duplicate_username_case_insensitively(self):
        before = self.state()
        self.assertEqual(self.register(username="CUSTOMER_A").status_code, 400)
        self.assertEqual(self.state(), before)

    def test_unknown_user_and_wrong_password_have_generic_login_errors(self):
        responses = [
            self.post("/login", {"username": username, "password": "WrongPassword!2026"})
            for username in ("customer_a", "missing_account")
        ]
        self.assertTrue(all(response.status_code == 400 for response in responses))
        errors = [Page(response).errors for response in responses]
        self.assertTrue(errors[0], "Login failures must display an accessible error.")
        self.assertEqual(errors[0], errors[1])
        with self.client.session_transaction(base_url=ORIGIN) as session:
            self.assertNotIn("user_id", session)

    def test_admin_management_requires_admin_role(self):
        paths = ("/admin/products", "/admin/products/new", "/admin/products/1/edit", "/admin/users")
        self.assertEqual(self.get("/admin/login").status_code, 200)
        for path in paths:
            with self.subTest(anonymous_path=path):
                response = self.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers["Location"], "/admin/login")
        self.login()
        before = self.state()
        for path in paths:
            with self.subTest(customer_path=path):
                self.assertEqual(self.get(path).status_code, 403)
        for path in ("/admin/products/new", "/admin/products/1/edit", "/admin/products/1/delete"):
            with self.subTest(customer_post=path):
                self.assertEqual(self.post(path, {"name": "Ignored"}).status_code, 403)
        with self.client.session_transaction(base_url=ORIGIN) as session:
            session["role"] = "admin"
        self.assertEqual(self.get("/admin/products").status_code, 403)
        self.assertEqual(self.state(), before)

    def test_admin_product_create_edit_delete_and_user_listing(self):
        self.login("admin", "AdminDemo!2026", admin=True)
        values = {
            "name": "Lab tray",
            "description": "Synthetic desk accessory.",
            "price": "12.50",
            "category": "Study",
            "stock": "5",
        }
        self.assertEqual(self.post("/admin/products/new", values).status_code, 303)
        product_id, price, stock = self.query(
            "SELECT id, price, stock FROM products WHERE name = ?", ("Lab tray",)
        )[0]
        self.assertEqual((price, stock), (1250, 5))
        values.update(name="Campus tray", price="15.75", stock="7")
        self.assertEqual(self.post(f"/admin/products/{product_id}/edit", values).status_code, 303)
        self.assertEqual(
            self.query("SELECT name, price, stock FROM products WHERE id = ?", (product_id,)),
            [("Campus tray", 1575, 7)],
        )
        self.assertEqual(self.post(f"/admin/products/{product_id}/delete").status_code, 303)
        self.assertEqual(self.query("SELECT id FROM products WHERE id = ?", (product_id,)), [])
        response = self.get("/admin/users")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for username, password_hash in self.query("SELECT username, password_hash FROM users"):
            self.assertIn(username, html)
            self.assertNotIn(password_hash, html)

    def test_admin_cannot_delete_referenced_product(self):
        self.login("admin", "AdminDemo!2026", admin=True)
        before = self.state()
        self.assertEqual(self.post("/admin/products/1/delete").status_code, 409)
        self.assertEqual(self.state(), before)

    def test_missing_or_invalid_csrf_rejects_post_without_mutation(self):
        self.login("admin", "AdminDemo!2026", admin=True)
        before = self.state()
        paths = (
            "/register",
            "/login",
            "/admin/login",
            "/cart/add",
            "/cart/remove",
            "/checkout",
            "/logout",
            "/admin/products/new",
            "/admin/products/1/edit",
            "/admin/products/1/delete",
        )
        values = {
            "username": "csrf_learner",
            "email": "csrf@example.invalid",
            "password": "LocalCsrf!2026",
            "name": "CSRF tray",
            "description": "Synthetic test product.",
            "price": "15.00",
            "category": "Study",
            "stock": "3",
            "product_id": "1",
            "quantity": "1",
            "item_id": "1",
        }
        for path in paths:
            for token in (None, "invalid"):
                with self.subTest(path=path, token="missing" if token is None else "invalid"):
                    data = dict(values)
                    if token is not None:
                        data["csrf_token"] = token
                    response = self.client.post(path, data=data, base_url=ORIGIN)
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(self.state(), before)

    def test_mutations_require_post(self):
        self.login("admin", "AdminDemo!2026", admin=True)
        before = self.state()
        for path in (
            "/cart/add",
            "/cart/remove",
            "/checkout",
            "/logout",
            "/admin/products/1/delete",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.get(path).status_code, 405)
        self.assertEqual(self.state(), before)

    def test_cart_add_and_remove_are_owner_scoped(self):
        self.login()
        other = self.app.test_client()
        self.login("customer_b", "CustomerB!2026", client=other)
        self.assertEqual(
            self.post("/cart/add", {"product_id": "1", "quantity": "2"}, ajax=True).status_code, 200
        )
        self.assertEqual(
            self.post(
                "/cart/add", {"product_id": "2", "quantity": "1"}, client=other, ajax=True
            ).status_code,
            200,
        )
        own_id = self.query("SELECT id FROM cart_items WHERE user_id = ?", (1,))[0][0]
        foreign_id = self.query("SELECT id FROM cart_items WHERE user_id = ?", (2,))[0][0]
        before = self.state()
        self.assertEqual(self.post("/cart/remove", {"item_id": str(foreign_id)}).status_code, 404)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.post("/cart/remove", {"item_id": str(own_id)}).status_code, 303)
        self.assertEqual(
            self.query("SELECT user_id, product_id, quantity FROM cart_items"), [(2, 2, 1)]
        )

    def test_cart_rejects_invalid_quantities_and_excess_stock(self):
        self.login()
        before = self.state()
        for quantity in ("0", "-1", "100", "not-a-number", "36"):
            with self.subTest(quantity=quantity):
                response = self.post(
                    "/cart/add", {"product_id": "1", "quantity": quantity}, ajax=True
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self.state(), before)
        self.assertEqual(
            self.post("/cart/add", {"product_id": "9999", "quantity": "1"}, ajax=True).status_code,
            404,
        )
        self.assertEqual(self.state(), before)
        self.assertEqual(
            self.post("/cart/add", {"product_id": "1", "quantity": "1"}, ajax=True).status_code, 200
        )
        self.assertEqual(
            self.post("/cart/add", {"product_id": "1", "quantity": "35"}, ajax=True).status_code,
            400,
        )
        self.assertEqual(
            self.query("SELECT quantity FROM cart_items WHERE user_id = ?", (1,)), [(1,)]
        )

    def test_checkout_uses_stored_money_and_clears_only_owner_cart(self):
        self.login()
        other = self.app.test_client()
        self.login("customer_b", "CustomerB!2026", client=other)
        self.post(
            "/cart/add", {"product_id": "1", "quantity": "2", "price": "1", "total": "1"}, ajax=True
        )
        self.post("/cart/add", {"product_id": "2", "quantity": "1"}, client=other, ajax=True)
        response = self.post("/checkout", {"price": "1", "total": "1"})
        self.assertEqual(response.status_code, 303)
        order_id, total = self.query(
            "SELECT id, total FROM orders WHERE user_id = ? ORDER BY id DESC", (1,)
        )[0]
        self.assertEqual(total, 49800)
        self.assertEqual(
            self.query(
                "SELECT quantity, unit_price FROM order_items WHERE order_id = ?", (order_id,)
            ),
            [(2, 24900)],
        )
        self.assertEqual(self.query("SELECT stock FROM products WHERE id = ?", (1,)), [(33,)])
        self.assertEqual(
            self.query("SELECT user_id, product_id, quantity FROM cart_items"), [(2, 2, 1)]
        )
        self.assertIn(order_id, Page(self.get("/orders")).order_ids)
        before = self.state()
        self.assertEqual(self.post("/checkout").status_code, 303)
        self.assertEqual(
            self.state(), before, "An empty-cart repeat must not create a duplicate order."
        )

    def test_checkout_insufficient_stock_preserves_orders_cart_and_stock(self):
        self.login()
        self.post("/cart/add", {"product_id": "1", "quantity": "2"}, ajax=True)
        self.change("UPDATE products SET stock = ? WHERE id = ?", (1, 1))
        before = self.state()
        response = self.post("/checkout")
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.state(), before)

    def test_order_history_shows_only_logged_in_users_orders(self):
        self.login()
        self.assertEqual(set(Page(self.get("/orders")).order_ids), {1, 2, 3})
        other = self.app.test_client()
        self.login("customer_b", "CustomerB!2026", client=other)
        self.assertEqual(set(Page(self.get("/orders", other)).order_ids), {4, 5, 6})

    def test_local_host_debug_and_cookie_contract(self):
        self.assertFalse(self.app.debug)
        self.assertTrue(self.app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(self.app.config["SESSION_COOKIE_SAMESITE"], "Lax")
        self.assertFalse(self.app.config["SESSION_COOKIE_SECURE"])
        self.assertTrue(self.app.config["WTF_CSRF_ENABLED"])
        self.assertEqual(self.app.config["SECRET_KEY"], self.config["SECRET_KEY"])
        self.assertEqual(self.get("/").status_code, 200)
        self.assertEqual(self.client.get("/", base_url="http://localhost:8080").status_code, 400)
        response = self.login()
        cookies = "\n".join(response.headers.getlist("Set-Cookie"))
        self.assertIn("HttpOnly", cookies)
        self.assertIn("SameSite=Lax", cookies)
        self.assertNotIn("; Secure", cookies)
        with patch(
            "app.local_secret",
            side_effect=AssertionError("Explicit test keys must skip local key creation."),
        ):
            configured_debug = create_app({**self.config, "DEBUG": True})
        self.assertFalse(configured_debug.debug)

    def test_money_display_preserves_exact_paise_including_large_integers(self):
        formatter = self.app.jinja_env.filters["money"]
        examples = (
            (0, "₹0.00"),
            (1, "₹0.01"),
            (99, "₹0.99"),
            (100, "₹1.00"),
            (24900, "₹249.00"),
            (99_999_999, "₹999,999.99"),
            (9_007_199_254_740_993, "₹90,071,992,547,409.93"),
        )
        for paise, expected in examples:
            with self.subTest(paise=paise):
                self.assertEqual(formatter(paise), expected)

    def test_product_illustrations_use_known_local_paths_and_category_fallback(self):
        self.assertEqual(
            product_image({"name": "Everyday notebook", "category": "Study"}),
            "img/products/notebook.svg",
        )
        for category in ("Study", "Carry", "Everyday", "Tech"):
            with self.subTest(category=category):
                product = {"name": "New campus product", "category": category}
                self.assertEqual(product_image(product), f"img/products/{category.lower()}.svg")
        self.assertEqual(
            product_image({"name": "New campus product", "category": "Seasonal"}),
            "img/products/study.svg",
        )
        for name, category in self.query("SELECT name, category FROM products"):
            image = Path(product_image({"name": name, "category": category}))
            self.assertFalse(image.is_absolute())
            self.assertEqual(image.parent.as_posix(), "img/products")
            self.assertEqual(image.suffix, ".svg")

    def test_authentication_throttle_is_isolated_between_apps(self):
        for _ in range(5):
            response = self.post(
                "/login", {"username": "customer_a", "password": "WrongPassword!2026"}
            )
            self.assertEqual(response.status_code, 400)
        blocked = self.post("/login", {"username": "customer_a", "password": "CustomerA!2026"})
        self.assertEqual(blocked.status_code, 400)
        second_app = create_app({**self.config, "SECRET_KEY": "another-temporary-test-key-" * 3})
        self.login(client=second_app.test_client())


if __name__ == "__main__":
    unittest.main()
