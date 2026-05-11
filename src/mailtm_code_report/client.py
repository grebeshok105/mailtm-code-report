from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class MailTmError(RuntimeError):
    pass


@dataclass(frozen=True)
class MailTmMessageSummary:
    id: str
    from_address: str
    subject: str
    intro: str
    seen: bool
    created_at: str


@dataclass(frozen=True)
class MailTmMessage:
    id: str
    from_address: str
    subject: str
    intro: str
    text: str
    html: str
    seen: bool
    created_at: str


class MailTmClient:
    def __init__(
        self,
        base_url: str = "https://api.mail.tm",
        timeout_seconds: float = 15.0,
        min_request_interval_seconds: float = 0.15,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.min_request_interval_seconds = min_request_interval_seconds
        self._token: str | None = None
        self._last_request_at = 0.0

    def login(self, address: str, password: str) -> None:
        response = self._request(
            "POST",
            "/token",
            data={"address": address, "password": password},
            authenticated=False,
        )
        token = response.get("token")
        if not isinstance(token, str) or not token:
            raise MailTmError(f"mail.tm did not return a token for {address}")
        self._token = token

    def list_messages(self, page: int = 1) -> list[MailTmMessageSummary]:
        response = self._request("GET", "/messages", query={"page": str(page)})
        items = response.get("hydra:member")
        if not isinstance(items, list):
            raise MailTmError("mail.tm returned an unexpected messages payload")
        return [self._parse_summary(item) for item in items if isinstance(item, dict)]

    def get_message(self, message_id: str) -> MailTmMessage:
        response = self._request("GET", f"/messages/{urllib.parse.quote(message_id)}")
        return self._parse_message(response)

    def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        self._respect_rate_limit()
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"

        body: bytes | None = None
        headers = {"Accept": "application/json"}
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if authenticated:
            if not self._token:
                raise MailTmError("mail.tm client is not authenticated")
            headers["Authorization"] = f"Bearer {self._token}"

        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise MailTmError(f"mail.tm HTTP {error.code}: {details}") from error
        except urllib.error.URLError as error:
            raise MailTmError(f"mail.tm request failed: {error.reason}") from error

        if not payload:
            return {}
        parsed = json.loads(payload)
        if not isinstance(parsed, dict):
            raise MailTmError("mail.tm returned a non-object JSON payload")
        return parsed

    def _respect_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_request_interval_seconds:
            time.sleep(self.min_request_interval_seconds - elapsed)
        self._last_request_at = time.monotonic()

    @staticmethod
    def _parse_summary(payload: dict[str, Any]) -> MailTmMessageSummary:
        sender = payload.get("from")
        from_address = ""
        if isinstance(sender, dict):
            from_address = str(sender.get("address") or "")
        return MailTmMessageSummary(
            id=str(payload.get("id") or ""),
            from_address=from_address,
            subject=str(payload.get("subject") or ""),
            intro=str(payload.get("intro") or ""),
            seen=bool(payload.get("seen")),
            created_at=str(payload.get("createdAt") or ""),
        )

    @classmethod
    def _parse_message(cls, payload: dict[str, Any]) -> MailTmMessage:
        summary = cls._parse_summary(payload)
        html = payload.get("html")
        if isinstance(html, list):
            html_text = "\n".join(str(part) for part in html)
        else:
            html_text = str(html or "")
        return MailTmMessage(
            id=summary.id,
            from_address=summary.from_address,
            subject=summary.subject,
            intro=summary.intro,
            text=str(payload.get("text") or ""),
            html=html_text,
            seen=summary.seen,
            created_at=summary.created_at,
        )
