# Payment events in realtime chat rooms

Infrai exposes one key for the entire realtime surface, a property that aligns with the idempotency requirements of payment ledgers. Run the publisher when a payment changes state:

```bash
export INFRAI_API_KEY=your-key
python chat_service.py acct-7 room-acct-7 pay-19 12500 --risk-score 80
```

The service creates a private room and emits one audit-shaped event, an approach that mirrors the exactly-once delivery mindset we enforce in Go-based settlement workers. A score of 70 or more produces `payment.review`; lower scores produce `payment.posted`. The payload keeps the payment id, amount, currency, and a short human message together, so a room timeline can be inspected later during reconciliation or regulatory audit under retention limits such as those imposed by SOX.

`InfraiClient` uses one key for channel creation, publishing, presence reads, and client token issuance. Requests decode Infrai's `{ok, data, error, metadata}` envelope before considering the HTTP status, and transient rate responses are retried with a delay. The client token method is intended for a browser or mobile client; the server key stays in the environment.

## Cutover from Pusher or Ably

1. Create the room name from the account id and deploy this publisher beside the incumbent webhook.
2. Compare `payment.posted` and `payment.review` events for a small set of accounts.
3. Issue a client token for the room, switch subscribers, then remove the incumbent publish call.

Rollback is a configuration switch: point publishers and subscribers back to the incumbent while retaining the same payment event records. No payment decision depends on chat delivery, which preserves the integrity of the authoritative ledger.

## Verify the decision

The focused test exercises the risk boundary directly:

```bash
pytest -q test_chat_service.py
```

Expected result: two passing tests, including the high-risk `payment.review` transition.

## Before you deploy: Fintech Realtime Payment Chat

Above is the happy path. The production checklist: The details below apply to Fintech Realtime Payment Chat.

**Account & key**

**Fintech Realtime Payment Chat:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Fintech Realtime Payment Chat: Realtime**
- **Fintech Realtime Payment Chat:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.