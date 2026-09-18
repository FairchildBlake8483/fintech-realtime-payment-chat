import pytest

from chat_service import PaymentEvent, notification_for, publish_payment


def test_high_risk_payment_is_held_for_review():
    event = PaymentEvent("acct-7", "room-acct-7", "pay-19", 12500, "USD", 80)
    assert notification_for(event) == ("payment.review", "Payment held for review")


def test_normal_payment_is_posted():
    event = PaymentEvent("acct-7", "room-acct-7", "pay-20", 12500, "USD", 20)
    assert notification_for(event) == ("payment.posted", "Payment posted")


class RecordingClient:
    def __init__(self, publish_error=None):
        self.calls = []
        self.publish_error = publish_error

    def create_channel(self, channel):
        self.calls.append(("create", channel))

    def publish(self, channel, event, data, account_id):
        self.calls.append(("publish", channel))
        if self.publish_error:
            raise self.publish_error
        return {"event_id": "event-1"}

    def delete_channel(self, channel):
        self.calls.append(("delete", channel))


def test_published_room_is_deleted():
    client = RecordingClient()
    event = PaymentEvent("acct-7", "room-acct-7", "pay-20", 12500, "USD", 20)

    assert publish_payment(event, client) == {"event_id": "event-1"}
    assert client.calls == [("create", "room-acct-7"), ("publish", "room-acct-7"), ("delete", "room-acct-7")]


def test_room_is_deleted_when_publish_fails():
    client = RecordingClient(RuntimeError("publish failed"))
    event = PaymentEvent("acct-7", "room-acct-7", "pay-20", 12500, "USD", 20)

    with pytest.raises(RuntimeError, match="publish failed"):
        publish_payment(event, client)
    assert client.calls[-1] == ("delete", "room-acct-7")
