"""A beginner shopping agent that cannot pay until you type YES.

The flow is always the same:

  1. Read a request, such as "Buy me a notebook under 15 dollars".
  2. Search a made-up catalogue and show matching items.
  3. Build a cart with line items and a total.
  4. Stop and wait for a human to type YES.
  5. Only then send a Stripe PaymentIntent in TEST mode.

No real money moves. Never print or log your Stripe key.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from catalog import CATALOG, money

# Official Stripe test PaymentMethods. Prefer these over raw card numbers
# in server-side code. See https://docs.stripe.com/testing
TEST_METHODS = {
    "success": "pm_card_visa",
    "decline": "pm_card_chargeDeclined",
    "3ds": "pm_card_authenticationRequired",
}

DEFAULT_REQUEST = "Buy me a notebook under 15 dollars"


def load_secret_key() -> str:
    """Load STRIPE_SECRET_KEY from a local .env file. Never print it."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    for path in candidates:
        if path.is_file():
            load_dotenv(path)
            break
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        raise SystemExit(
            "STRIPE_SECRET_KEY is not set. Copy .env.example to .env "
            "and add a Stripe test key from `stripe sandbox create`."
        )
    if key.startswith("sk_live") or key.startswith("rk_live"):
        raise SystemExit("Refusing to run with a live key. This demo is test mode only.")
    return key


def parse_request(request: str) -> tuple[str, int]:
    """Pull a product word and a budget in cents out of a plain-English request."""
    text = request.lower()
    match = re.search(r"under\s+(\d+(?:\.\d+)?)\s+dollars?", text)
    if match:
        budget_cents = int(round(float(match.group(1)) * 100))
    else:
        budget_cents = 1500
    word = "notebook"
    for candidate in ("notebook", "lamp", "pens", "notes"):
        if candidate in text:
            word = candidate
            break
    return word, budget_cents


def search(request: str) -> list[dict]:
    """Return catalogue items that match the product word and sit under the budget."""
    word, budget_cents = parse_request(request)
    matches = []
    for item in CATALOG:
        haystack = " ".join([item["name"], *item["tags"]]).lower()
        if word in haystack and item["price_cents"] < budget_cents:
            matches.append(item)
    return matches


def build_cart(matches: list[dict]) -> list[dict]:
    """Pick the highest-priced match still under the budget.

    For "a notebook under 15 dollars" that is the hardcover notebook at $12.00,
    not the cheaper spiral. One line item, one total.
    """
    if not matches:
        return []
    chosen = max(matches, key=lambda item: item["price_cents"])
    return [dict(chosen)]


def cart_total(cart: list[dict]) -> int:
    return sum(item["price_cents"] for item in cart)


def print_matches(matches: list[dict], budget_cents: int) -> None:
    print(f"Matches under {money(budget_cents)}:")
    if not matches:
        print("  (none)")
        return
    for item in matches:
        print(f"  - {item['name']:<24} {money(item['price_cents'])}")
    print()


def print_cart(cart: list[dict]) -> None:
    print("Cart")
    for item in cart:
        print(f"  {item['name']:<24} {money(item['price_cents'])}")
    print("  ------------------------")
    print(f"  {'Total':<24} {money(cart_total(cart))}")
    print()


def ask_approval(prefilled: str | None) -> bool:
    """Hard stop. Only the exact word YES (any case) allows payment."""
    prompt = "Pay this cart? Type YES to pay, or anything else to cancel.\n> "
    if prefilled is None:
        answer = input(prompt)
    else:
        print(prompt + prefilled, flush=True)
        answer = prefilled
    return answer.strip().upper() == "YES"


def _clean_error(message: str | None) -> str:
    """Drop Stripe's extra note about claiming a sandbox. We never claim it."""
    if not message:
        return "The payment did not succeed."
    return re.sub(r"\s*\(This is an unclaimed Stripe sandbox\.[^)]*\)\s*", "", message).strip()


def pay(cart: list[dict], payment_method: str) -> dict:
    """Create and confirm a Stripe PaymentIntent in TEST mode."""
    import stripe

    stripe.api_key = load_secret_key()
    amount = cart_total(cart)
    print(f"Sending a test payment of {money(amount)}...")
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            payment_method=payment_method,
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            description="Shopping agent demo (Stripe test mode, no real money)",
        )
        return {
            "ok": intent.status == "succeeded",
            "status": intent.status,
            "id": intent.id,
            "amount": intent.amount,
            "currency": intent.currency,
            "next_action": intent.next_action.type if intent.next_action else None,
            "error_code": None,
            "decline_code": None,
            "message": None,
        }
    except stripe.CardError as exc:
        err = exc.error
        intent = err.payment_intent if err else None
        return {
            "ok": False,
            "status": intent.status if intent else "failed",
            "id": intent.id if intent else None,
            "amount": amount,
            "currency": "usd",
            "next_action": None,
            "error_code": err.code if err else None,
            "decline_code": getattr(err, "decline_code", None) if err else None,
            "message": _clean_error(err.message if err else str(exc)),
        }


def print_result(result: dict) -> None:
    print(f"Status: {result['status']}")
    if result.get("id"):
        print(f"Payment id: {result['id']}")
    print(f"Amount: {money(result['amount'])} {result['currency'].upper()}")
    if result["status"] == "succeeded":
        print("No real money moved. This is Stripe test mode.")
    elif result["status"] == "requires_action":
        print("The bank is asking: is this really you?")
        print("The payment will not succeed until 3-D Secure is completed.")
        if result.get("next_action"):
            print(f"Next action: {result['next_action']}")
    else:
        if result.get("error_code"):
            extra = f" ({result['decline_code']})" if result.get("decline_code") else ""
            print(f"Error: {result['error_code']}{extra}")
        if result.get("message"):
            print(result["message"])


def run(request: str, approve: str | None, payment_method: str) -> int:
    print(f"Request: {request}\n")
    _, budget_cents = parse_request(request)
    matches = search(request)
    print_matches(matches, budget_cents)
    cart = build_cart(matches)
    if not cart:
        print("Nothing to buy under that budget. No payment was sent.")
        return 1
    print_cart(cart)
    if not ask_approval(approve):
        print("Cancelled. No payment was sent.")
        return 0
    result = pay(cart, payment_method)
    print_result(result)
    return 0 if result["ok"] or result["status"] == "requires_action" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="A shopping agent that will not pay until you type YES.")
    parser.add_argument("--request", default=DEFAULT_REQUEST, help="The shopper's request in plain English.")
    parser.add_argument(
        "--approve",
        default=None,
        help="Pre-fill the approval answer (YES or NO). If omitted, the agent waits for you to type it.",
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(TEST_METHODS),
        default="success",
        help="Which official Stripe test PaymentMethod to use.",
    )
    parser.add_argument(
        "--payment-method",
        default=None,
        help="Override the test PaymentMethod id, for example pm_card_visa.",
    )
    args = parser.parse_args()
    method = args.payment_method or TEST_METHODS[args.scenario]
    return run(args.request, args.approve, method)


if __name__ == "__main__":
    sys.exit(main())
