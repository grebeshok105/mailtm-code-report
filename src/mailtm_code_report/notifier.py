from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import asdict

from .scanner import CodeFinding


class NotificationError(RuntimeError):
    pass


def notify_findings(findings: list[CodeFinding], mode: str) -> None:
    if mode == "none" or not findings:
        return
    if mode == "telegram":
        send_telegram(findings)
        return
    if mode == "webhook":
        send_webhook(findings)
        return
    raise NotificationError(f"Unknown notification mode: {mode}")


def send_telegram(findings: list[CodeFinding]) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise NotificationError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")

    text = "\n\n".join(
        f"{finding.account}\n{finding.subject}\nCodes: {', '.join(finding.codes)}"
        for finding in findings
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    _post(url, body, "application/x-www-form-urlencoded")


def send_webhook(findings: list[CodeFinding]) -> None:
    url = os.environ.get("CODE_REPORT_WEBHOOK_URL")
    if not url:
        raise NotificationError("CODE_REPORT_WEBHOOK_URL is required")
    payload = json.dumps({"findings": [asdict(finding) for finding in findings]}).encode("utf-8")
    _post(url, payload, "application/json")


def _post(url: str, body: bytes, content_type: str) -> None:
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": content_type, "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15):
        pass
