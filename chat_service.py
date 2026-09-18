from dataclasses import dataclass
from infrai_client import InfraiClient


@dataclass(frozen=True)
class PaymentEvent:
    account_id: str
    room: str
    payment_id: str
    amount: int
    currency: str
    risk_score: int


def notification_for(event: PaymentEvent) -> tuple[str, str]:
    if event.risk_score >= 70:
        return "payment.review", "Payment held for review"
    return "payment.posted", "Payment posted"


def publish_payment(event: PaymentEvent, client: InfraiClient):
    client.create_channel(event.room)
    try:
        name, message = notification_for(event)
        return client.publish(event.room, name, {"payment_id": event.payment_id, "amount": event.amount, "currency": event.currency, "message": message}, event.account_id)
    finally:
        client.delete_channel(event.room)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Publish an audit-friendly payment notification")
    parser.add_argument("account_id")
    parser.add_argument("room")
    parser.add_argument("payment_id")
    parser.add_argument("amount", type=int)
    parser.add_argument("--risk-score", type=int, default=0)
    args = parser.parse_args()
    event = PaymentEvent(args.account_id, args.room, args.payment_id, args.amount, "USD", args.risk_score)
    print(publish_payment(event, InfraiClient()))
