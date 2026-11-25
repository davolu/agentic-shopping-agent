# Shopping Agent (Stripe test mode)

A small, beginner-friendly Python shopping agent. It searches a made-up catalogue, builds a cart, and **will not pay until you type YES**. Payments use Stripe **test mode** only. No real money moves.

This is the companion code for the Agentic AI Hub tutorial *AI Agents Can Now Spend Your Money. Here's How It Actually Works*.

## What it does

1. Reads a request such as `Buy me a notebook under 15 dollars`.
2. Searches five fake products and keeps the ones under the budget.
3. Builds a cart (the hardcover notebook at $12.00) and prints the total.
4. Stops and waits for `YES`. Anything else cancels, and no payment is sent.
5. After `YES`, creates a Stripe PaymentIntent in test mode.

## What you need

- Python 3.10 or newer
- A Stripe **test** secret key. You do not need a live Stripe account or a bank.

Stripe's official command-line tool can create a 7-day anonymous test sandbox:

```bash
# Install the Stripe CLI from https://docs.stripe.com/stripe-cli
stripe sandbox create --email you@example.com
```

Copy the secret key into a local `.env` file. Do not commit that file. Do not use a live key. The sandbox expires after 7 days unless you claim it. This demo never claims a sandbox, and you should not claim one under a country that is not where you do business.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and paste your TEST secret key. Never paste a live key.
```

## Run it

The request is already the one from the video:

```bash
# First, see a cancelled run (type n, or pass --approve no)
python shopping_agent.py --approve no

# A successful test payment (official test method pm_card_visa)
python shopping_agent.py --approve YES --scenario success

# A generic decline (pm_card_chargeDeclined)
python shopping_agent.py --approve YES --scenario decline

# 3-D Secure: the payment stays at requires_action (pm_card_authenticationRequired)
python shopping_agent.py --approve YES --scenario 3ds
```

If you omit `--approve`, the agent waits for you to type the answer yourself.

The official test PaymentMethods used here are listed in [Stripe's testing docs](https://docs.stripe.com/testing):

| Scenario | PaymentMethod | What you should see |
| --- | --- | --- |
| Success | `pm_card_visa` | `status: succeeded` |
| Generic decline | `pm_card_chargeDeclined` | `card_declined` / `generic_decline` |
| 3-D Secure | `pm_card_authenticationRequired` | `status: requires_action` |

Those stand in for the test cards `4242 4242 4242 4242`, `4000 0000 0000 0002`, and `4000 0000 0000 3220`. Using PaymentMethod tokens keeps raw card numbers out of server-side code.

## Safety

- Test mode only. The program exits if it sees a live key.
- Never print, log, or commit your key. Never open `.env` on camera.
- This catalogue is fake. A real storefront will often block, stall, or cancel an agent checkout.

## License

Apache License 2.0. See `LICENSE`.
