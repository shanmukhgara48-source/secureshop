"""Reset the local synthetic database. Stop the server before running this."""

from contextlib import closing
from pathlib import Path

from werkzeug.security import generate_password_hash

from db import connect, init_schema

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "shop.db"
DEMO_USERS = (
    (1, "customer_a", "customer.a@example.invalid", "CustomerA!2026", "customer"),
    (2, "customer_b", "customer.b@example.invalid", "CustomerB!2026", "customer"),
    (3, "admin", "admin@example.invalid", "AdminDemo!2026", "admin"),
)
PRODUCTS = (
    (1, "Everyday notebook", "A dotted notebook for lectures and quick ideas.", 24900, "Study", 35),
    (2, "Desk organiser", "Keep pens, cards, and small essentials within reach.", 39900, "Study", 22),
    (3, "Study lamp", "A compact desk lamp with a warm reading light.", 129900, "Study", 15),
    (4, "Canvas tote", "A lightweight cotton tote for your campus essentials.", 44900, "Carry", 30),
    (5, "Campus backpack", "A roomy everyday bag with a padded laptop sleeve.", 189900, "Carry", 18),
    (6, "Travel pouch", "A zip pouch for cables and small everyday things.", 34900, "Carry", 28),
    (7, "Steel bottle", "An insulated bottle for a long day on campus.", 69900, "Everyday", 40),
    (8, "Kid's cap", "A simple cotton cap with an adjustable strap.", 29900, "Everyday", 12),
    (9, "Ceramic mug", "A sturdy mug for study breaks.", 32900, "Everyday", 24),
    (10, "USB-C cable", "A braided charging cable for everyday use.", 29900, "Tech", 50),
    (11, "Laptop stand", "A folding aluminium stand for a clearer desk.", 99900, "Tech", 20),
    (12, "Wireless mouse", "A compact mouse with a quiet click.", 79900, "Tech", 25),
)


def reset_database(path=DATABASE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as connection, connection:
        connection.executescript("""
            DROP TABLE IF EXISTS order_items;
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS cart_items;
            DROP TABLE IF EXISTS products;
            DROP TABLE IF EXISTS users;
        """)
        init_schema(connection)
        connection.executemany(
            "INSERT INTO users (id, username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            [(uid, name, email, generate_password_hash(password), role, "2026-10-01 09:00:00")
             for uid, name, email, password, role in DEMO_USERS],
        )
        connection.executemany(
            "INSERT INTO products (id, name, description, price, category, stock) VALUES (?, ?, ?, ?, ?, ?)",
            PRODUCTS,
        )
        # IDs 1–3 belong to customer A; IDs 4–6 belong to customer B.
        for order_id, user_id, product_id in ((1, 1, 1), (2, 1, 4), (3, 1, 7), (4, 2, 2), (5, 2, 5), (6, 2, 10)):
            price = PRODUCTS[product_id - 1][3]
            connection.execute(
                "INSERT INTO orders (id, user_id, total, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (order_id, user_id, price, "Delivered", "2026-10-02 10:00:00"),
            )
            connection.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, product_id, 1, price),
            )
    path.chmod(0o600)


if __name__ == "__main__":
    reset_database()
    print("Reset shop.db: 2 customers, 1 admin, 12 products, 6 orders. Demo credentials are in README.md.")
