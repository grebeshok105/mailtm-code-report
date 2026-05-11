#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, cast

ACCOUNTS_FILE = Path("accounts.txt")
API_BASE_URL = "https://api.mail.tm"
SCAN_EVERY_SECONDS = 15
MESSAGES_PER_ACCOUNT = 10
CODE_PATTERN = re.compile(r"(?<![A-Z0-9])(?:\d{4,8}|[A-Z0-9]{6,10})(?![A-Z0-9])", re.IGNORECASE)
CODE_CONTEXT_PATTERN = re.compile(
    r"(code|код|verification|verify|confirm|confirmation|otp|парол|подтвержд)",
    re.IGNORECASE,
)
TAG_PATTERN = re.compile(r"<[^>]+>")


def main() -> int:
    ensure_accounts_file()
    print("mail.tm code scanner")
    print(f"Аккаунты: {ACCOUNTS_FILE.resolve()}")
    print("Формат строк: email@domain:password")
    print("Остановить: Ctrl+C")
    print()

    seen: set[str] = set()
    while True:
        accounts = load_accounts()
        if not accounts:
            print("accounts.txt пустой. Добавь аккаунты и оставь скрипт запущенным.")
        for address, password in accounts:
            scan_account(address, password, seen)
        time.sleep(SCAN_EVERY_SECONDS)


def ensure_accounts_file() -> None:
    if ACCOUNTS_FILE.exists():
        return
    ACCOUNTS_FILE.write_text(
        "# Добавь mail.tm аккаунты сюда, по одному на строку:\n"
        "# email@domain:password\n"
        "# example@domain.mail.tm:password\n",
        encoding="utf-8",
    )


def load_accounts() -> list[tuple[str, str]]:
    accounts: list[tuple[str, str]] = []
    for line_number, raw_line in enumerate(ACCOUNTS_FILE.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            print(f"accounts.txt:{line_number}: пропуск — нужен формат email:password")
            continue
        address, password = line.split(":", 1)
        address = address.strip()
        password = password.strip()
        if not address or not password:
            print(f"accounts.txt:{line_number}: пропуск — email/password пустой")
            continue
        accounts.append((address, password))
    return accounts


def scan_account(address: str, password: str, seen: set[str]) -> None:
    try:
        token = login(address, password)
        messages_response = request_api("/messages", token)
        if isinstance(messages_response, list):
            messages = messages_response
        elif isinstance(messages_response, dict):
            messages = messages_response.get("hydra:member", [])
        else:
            print(f"{address}: mail.tm вернул неожиданный список писем")
            return
        if not isinstance(messages, list):
            print(f"{address}: mail.tm вернул неожиданный список писем")
            return
        found_any = False
        for message in messages[:MESSAGES_PER_ACCOUNT]:
            if not isinstance(message, dict):
                continue
            message_id = str(message.get("id") or "")
            if not message_id:
                continue
            full_message = request_dict(f"/messages/{urllib.parse.quote(message_id)}", token)
            codes = extract_codes(message_text(full_message))
            if not codes:
                continue
            found_any = True
            dedupe_key = f"{address}:{message_id}:{','.join(codes)}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            subject = str(full_message.get("subject") or "(без темы)")
            sender = full_message.get("from")
            from_address = ""
            if isinstance(sender, dict):
                from_address = str(sender.get("address") or "")
            print()
            print("=" * 60)
            print(f"АККАУНТ: {address}")
            print(f"КОДЫ: {', '.join(codes)}")
            print(f"ТЕМА: {subject}")
            print(f"ОТ: {from_address or 'unknown'}")
            print("=" * 60)
            print()
        if not found_any:
            print(f"{address}: кодов нет")
    except MailTmError as error:
        print(f"{address}: ошибка — {error}")


def login(address: str, password: str) -> str:
    response = request_dict(
        "/token",
        None,
        method="POST",
        payload={"address": address, "password": password},
    )
    token = response.get("token")
    if not isinstance(token, str) or not token:
        raise MailTmError("не удалось получить token")
    return token


def request_dict(
    path: str,
    token: str | None,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    parsed = request_api(path, token, method=method, payload=payload)
    if not isinstance(parsed, dict):
        raise MailTmError(f"{path}: ожидался JSON object, получен {type(parsed).__name__}")
    return parsed


def request_api(
    path: str,
    token: str | None,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | list[Any]:
    url = f"{API_BASE_URL}{path}"
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise MailTmError(f"HTTP {error.code}: {details}") from error
    except urllib.error.URLError as error:
        raise MailTmError(str(error.reason)) from error

    try:
        parsed = json.loads(raw) if raw else {}
    except json.JSONDecodeError as error:
        short_raw = raw[:200].replace("\n", " ")
        raise MailTmError(f"{path}: API вернул не JSON: {short_raw}") from error
    if not isinstance(parsed, (dict, list)):
        raise MailTmError(f"{path}: API вернул JSON {type(parsed).__name__}")
    return cast(dict[str, Any] | list[Any], parsed)


def message_text(message: dict[str, Any]) -> str:
    html_body = message.get("html")
    if isinstance(html_body, list):
        html_text = "\n".join(str(part) for part in html_body)
    else:
        html_text = str(html_body or "")
    return "\n".join(
        [
            str(message.get("subject") or ""),
            str(message.get("intro") or ""),
            str(message.get("text") or ""),
            html_text,
        ]
    )


def extract_codes(raw_text: str) -> list[str]:
    text = normalize_text(raw_text)
    candidates: list[tuple[int, str]] = []
    for match in CODE_PATTERN.finditer(text):
        code = match.group(0).strip()
        if not code or code.lower() in {"mailtm", "mailto"}:
            continue
        window = text[max(0, match.start() - 80) : min(len(text), match.end() + 80)]
        priority = 0 if CODE_CONTEXT_PATTERN.search(window) else 1
        candidates.append((priority, code))

    codes: list[str] = []
    seen_codes: set[str] = set()
    for _, code in sorted(candidates, key=lambda item: item[0]):
        normalized = code.upper()
        if normalized in seen_codes:
            continue
        seen_codes.add(normalized)
        codes.append(code)
    return codes


def normalize_text(raw_text: str) -> str:
    without_tags = TAG_PATTERN.sub(" ", raw_text)
    unescaped = html.unescape(without_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


class MailTmError(RuntimeError):
    pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nОстановлено.")
        sys.exit(0)
