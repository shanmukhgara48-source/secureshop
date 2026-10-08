"""Shared catalogue metadata and deterministic local presentation helpers."""

from datetime import datetime

CATEGORIES = ("Study", "Carry", "Everyday", "Tech")
COLLECTION_DESCRIPTIONS = {
    "Study": "Make room for your next idea.",
    "Carry": "A place for everything you take along.",
    "Everyday": "Small comforts, from morning to evening.",
    "Tech": "Give your everyday setup a little lift.",
}
PRODUCT_IMAGES = {
    "Everyday notebook": "notebook",
    "Desk organiser": "organiser",
    "Study lamp": "lamp",
    "Canvas tote": "tote",
    "Campus backpack": "backpack",
    "Travel pouch": "pouch",
    "Steel bottle": "bottle",
    "Kid's cap": "cap",
    "Ceramic mug": "mug",
    "USB-C cable": "cable",
    "Laptop stand": "stand",
    "Wireless mouse": "mouse",
}


def product_image(product):
    """Resolve only known local filenames; new products get a collection drawing."""
    illustration = PRODUCT_IMAGES.get(product["name"])
    if illustration is None:
        category = product["category"]
        illustration = category.lower() if category in CATEGORIES else "study"
    return f"img/products/{illustration}.svg"


def collection_description(category):
    return COLLECTION_DESCRIPTIONS.get(category, "Thoughtful essentials for your day.")


def money(paise):
    """Format integer paise exactly, without binary floating-point rounding."""
    amount = int(paise)
    rupees, remainder = divmod(abs(amount), 100)
    sign = "−" if amount < 0 else ""
    return f"{sign}₹{rupees:,}.{remainder:02d}"


def shop_date(value):
    """Show a readable date while retaining unknown values as escaped text."""
    try:
        date = datetime.fromisoformat(str(value))
    except ValueError:
        return str(value)
    return f"{date.day} {date:%b %Y}"
