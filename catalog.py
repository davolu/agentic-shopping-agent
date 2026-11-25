"""A small made-up product catalogue for the shopping-agent demo.

Prices are stored in cents so we never have to fight floating-point money.
This is not a real store.
"""

CATALOG = [
    {
        "id": "nb-spiral",
        "name": "Spiral Notebook",
        "price_cents": 650,
        "tags": ["notebook", "stationery"],
    },
    {
        "id": "nb-hardcover",
        "name": "Hardcover Notebook",
        "price_cents": 1200,
        "tags": ["notebook", "stationery"],
    },
    {
        "id": "pens",
        "name": "Gel Pens (pack of 4)",
        "price_cents": 425,
        "tags": ["stationery"],
    },
    {
        "id": "lamp",
        "name": "Desk Lamp",
        "price_cents": 2200,
        "tags": ["desk"],
    },
    {
        "id": "notes",
        "name": "Sticky Notes",
        "price_cents": 350,
        "tags": ["stationery"],
    },
]


def money(cents: int) -> str:
    """Format cents as a dollar string, for example 1200 -> $12.00."""
    return f"${cents / 100:.2f}"
