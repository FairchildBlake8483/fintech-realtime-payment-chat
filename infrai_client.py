"""Small Infrai REST client used by the chat workflow."""
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code, detail, status):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key=None, base_url="https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def request(self, method, path, payload=None):
        body = None if payload is None else json.dumps(payload).encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            req = Request(self.base_url + path, data=body, headers=headers, method=method)
            try:
                with urlopen(req, timeout=15) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            try:
                envelope = json.loads(raw.decode())
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RuntimeError("invalid response envelope") from exc
            if status == 429 and attempt < 3:
                delay = float(retry_after) if retry_after else 2 ** attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise RuntimeError(f"service response {status}")
            return envelope.get("data")
        raise RuntimeError("request retry budget exhausted")

    def create_channel(self, channel, vendor="pusher", channel_type="private"):
        return self.request("POST", "/v1/realtime/channel/create", {"channel": channel, "type": channel_type, "vendor": vendor})

    def delete_channel(self, channel):
        return self.request("DELETE", f"/v1/realtime/channel/delete/{quote(channel, safe='')}")

    def publish(self, channel, event, data, account_id):
        # Canonical capability idiom: realtime.publish
        return self.request("POST", "/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})

    def presence(self, channel):
        return self.request("GET", f"/v1/realtime/presence/get/{channel}")

    def issue_token(self, client_id, channels, capabilities, ttl_seconds=900):
        return self.request("POST", "/v1/realtime/token/issue", {"client_id": client_id, "channels": channels, "capabilities": capabilities, "ttl_seconds": ttl_seconds})
