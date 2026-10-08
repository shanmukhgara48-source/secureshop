"""Shared input limits used by server validation and HTML form hints."""

FORM_LIMITS = {
    "username_min": 3,
    "username_max": 32,
    "password_min": 10,
    "password_max": 128,
    "quantity_max": 99,
    "product_name_max": 80,
    "description_max": 500,
    "stock_max": 10_000,
    "email_max": 254,
    "search_max": 120,
}
MAX_PRICE_PAISE = 99_999_999


def valid_password_length(password):
    return FORM_LIMITS["password_min"] <= len(password) <= FORM_LIMITS["password_max"]


def cart_quantity(value):
    """Accept positive whole quantities within the per-product cart limit."""
    try:
        quantity = int(value)
    except (TypeError, ValueError):
        return None
    return quantity if 1 <= quantity <= FORM_LIMITS["quantity_max"] else None
