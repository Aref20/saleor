# Payment Architecture

Last updated: 2026-07-19 (post upstream sync to Core 3.23.18)

## Overview

The store supports two payment methods, both implemented as **built-in Core gateway
plugins** on Saleor's legacy Payments API:

| Method | Plugin ID | Code |
|---|---|---|
| HyperPay (cards: VISA/MASTER/MADA/AMEX, Apple Pay) | `saleor.payments.hyperpay` (see `consts.PLUGIN_ID`) | `saleor/payment/gateways/hyperpay/` |
| Cash on Delivery | `app.saleor.cash-on-delivery` | `saleor/payment/gateways/cash_on_delivery/` |

## Architecture decision: legacy plugin vs Transactions API

Upstream is migrating toward the Transactions API + external Payment Apps. Decision for
this synchronization cycle:

- **Keep both gateways as legacy-API built-in plugins.** Verified facts: Saleor 3.23.18
  still ships the legacy plugin payment interface (`BasePlugin.authorize_payment`,
  `capture_payment`, `confirm_payment`, `refund_payment`, `void_payment`,
  `process_payment`, `PaymentData`/`GatewayResponse` dataclasses) and still ships its own
  legacy built-in gateways (stripe/braintree/razorpay/authorize_net, deprecated but
  functional). The checkout `checkoutPaymentCreate` → `checkoutComplete` flow remains
  supported.
- Rewriting to a Transaction/Payment App during the sync would violate the sync safety
  rules (broad Core changes, unverifiable without live HyperPay credentials).
- **Forward path (documented, not executed):** extract HyperPay into a standalone Saleor
  Payment App speaking the Transactions API (`transactionInitialize` /
  `transactionProcess` webhooks) before upgrading to a Core version that drops the
  legacy Payments API (upstream signals 3.24+ deprecations). COD can migrate to a
  "manual" TransactionFlowStrategy app at the same time.

## HyperPay flow (Copy-and-Pay widget)

1. Storefront calls `checkoutPaymentCreate` (gateway `saleor.payments.hyperpay`).
2. Core plugin `process_payment` → `POST /v1/checkouts` (test or live host by plugin
   config) with entity id, amount, currency, brands, `merchantTransactionId`, customer
   e-mail and addresses. Never from the browser; the Access Token
   (`ConfigurationTypeField.SECRET`) exists only server-side.
3. Response: `action_required=True` + `action_required_data.checkout_id`. The storefront
   renders the HyperPay widget (`paymentWidgets.js?checkoutId=...`) from the configured
   HyperPay origin only, then the shopper is redirected back to
   `shopperResultUrl`.
4. Storefront then triggers confirmation; plugin `confirm` calls
   `GET /v1/checkouts/{id}/payment` **server-side** and maps the result code
   (regex `SUCCESS_CODES_PATTERN`) to success/failure. A successful gateway status is
   additionally validated against the local payment: **amount and currency must match**
   (added during sync; see `_find_amount_mismatch`) — a tampered or mixed-up callback
   cannot mark a payment paid for the wrong amount.
5. Capture/refund/void go through the back-office endpoint
   (`/v1/payments/{id}` with `paymentType` CP/RF/RV).
6. Order completion only follows a verified transaction outcome (`checkoutComplete`
   consumes the confirmed payment; a browser redirect parameter alone never completes
   an order).

Idempotency / duplicate handling: `merchantTransactionId` is a UUID generated per
payment attempt; HyperPay dedupes on it. Saleor's payment/transaction records dedupe
on the gateway transaction id at the mutation layer. Status polling (`confirm`) is
read-only and safe to retry.

Error handling: API failures return `GatewayResponse(is_success=False, error=...)`;
requests use a 30s timeout; logging never includes the access token (only result codes
and descriptions).

## Cash on Delivery flow

- `process_payment`/`authorize` succeed locally (no external call), producing an AUTH
  transaction; **auto-capture is off by default** — the order stays unpaid/pending until
  staff captures on delivery from the Dashboard.
- Eligibility: plugin is channel-configurable (Saleor plugin-per-channel configuration);
  currency allow-list via "Supported currencies". Storefront must additionally hide COD
  for digital-only checkouts (no shipping) — enforced storefront-side and by staff
  workflow, since the legacy gateway API has no shipping-required hook.
- Refund/void mark the local payment state accordingly (no external calls).
- COD can never silently mark an order as fully paid: capture is an explicit staff
  action.

## Test coverage

- `saleor/payment/gateways/hyperpay/tests/test_hyperpay.py` — unit tests for authorize,
  capture, refund, void, process_payment (auto + manual capture), client token, and
  confirm (success, amount mismatch, currency mismatch, missing checkout id).
- `saleor/payment/gateways/cash_on_delivery/tests/test_cash_on_delivery.py` — DB-backed
  tests routing real `gateway.authorize/capture/refund/void` calls through the plugin
  (fixtures re-pointed at the COD plugin id during sync — previously they targeted the
  dummy gateway, which 3.23.18's stricter accessibility check rejects).

## Credentials

- HyperPay Entity ID + Access Token: entered by staff in Dashboard plugin configuration
  (secret field), stored via Saleor's plugin configuration storage. Separate test/live
  hosts switch on the "Test mode" boolean. No credentials in the repository.
- Storefront receives only the public `checkout_id` and test-mode flag.
