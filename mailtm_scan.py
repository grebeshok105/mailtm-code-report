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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

ACCOUNTS_FILE = Path("accounts.txt")
API_BASE_URL = "https://api.mail.tm"
SCAN_EVERY_SECONDS = 15
MESSAGES_PER_ACCOUNT = 10
START_LOOKBACK_SECONDS = 30
COMPACT_CODE_PATTERN = re.compile(r"(?<!\d)\d{6}(?!\d)")
OLD_WORKING_CODE_PATTERN = re.compile(r"(?<![A-Z0-9])(?:\d{4,8}|[A-Z0-9]{6,10})(?![A-Z0-9])", re.IGNORECASE)
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
    print("Показывает только новые 6-значные коды.")
    print("Debug: python mailtm_scan.py --debug")
    print("Остановить: Ctrl+C")
    print()

    debug = "--debug" in sys.argv
    started_from = datetime.now(timezone.utc) - timedelta(seconds=START_LOOKBACK_SECONDS)
    seen: set[str] = set()
    while True:
        accounts = load_accounts()
        if not accounts:
            print("accounts.txt пустой. Добавь аккаунты и оставь скрипт запущенным.")
        cycle_codes = 0
        for address, password in accounts:
            cycle_codes += scan_account(address, password, seen, started_from, debug)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] проверено аккаунтов: {len(accounts)}, новых кодов: {cycle_codes}")
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


def scan_account(address: str, password: str, seen: set[str], started_from: datetime, debug: bool) -> int:
    try:
        token = login(address, password)
        messages_response = request_api("/messages", token)
        if isinstance(messages_response, list):
            messages = messages_response
        elif isinstance(messages_response, dict):
            messages = messages_response.get("hydra:member", [])
        else:
            print(f"{address}: mail.tm вернул неожиданный список писем")
            return 0
        if not isinstance(messages, list):
            print(f"{address}: mail.tm вернул неожиданный список писем")
            return 0
        if debug:
            print(f"[debug] {address}: писем в списке: {len(messages)}")
        found_codes = 0
        for message in messages[:MESSAGES_PER_ACCOUNT]:
            if not isinstance(message, dict):
                continue
            message_id = str(message.get("id") or "")
            if not message_id:
                continue
            full_message = request_dict(f"/messages/{urllib.parse.quote(message_id)}", token)
            created_at = parse_message_datetime(message, full_message)
            if created_at is not None and created_at < started_from:
                if debug:
                    print(f"[debug] {address}: письмо {message_id} старое: {created_at.isoformat()}")
                continue
            codes = extract_codes(message_text(full_message))
            if debug:
                subject = str(full_message.get("subject") or message.get("subject") or "")
                print(
                    f"[debug] {address}: письмо {message_id}, "
                    f"дата={created_at.isoformat() if created_at else 'unknown'}, "
                    f"тема={subject[:80]!r}, коды={codes or []}"
                )
            if not codes:
                continue
            dedupe_key = f"{address}:{message_id}:{','.join(codes)}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            for code in codes:
                print(f"{address}: {code}")
                found_codes += 1
        return found_codes
    except MailTmError as error:
        print(f"{address}: ошибка — {error}")
        return 0


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
    for match in OLD_WORKING_CODE_PATTERN.finditer(text):
        candidate = match.group(0).strip()
        digit_code = re.sub(r"\D", "", candidate)
        if len(digit_code) != 6:
            continue
        window = text[max(0, match.start() - 80) : min(len(text), match.end() + 80)]
        priority = 0 if CODE_CONTEXT_PATTERN.search(window) else 1
        candidates.append((priority, digit_code))
    for match in COMPACT_CODE_PATTERN.finditer(text):
        candidates.append((1, match.group(0)))

    codes: list[str] = []
    seen_codes: set[str] = set()
    for _, code in sorted(candidates, key=lambda item: item[0]):
        add_code(code, codes, seen_codes)
    return codes


def normalize_text(raw_text: str) -> str:
    without_tags = TAG_PATTERN.sub(" ", raw_text)
    unescaped = html.unescape(without_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


def add_code(code: str, codes: list[str], seen_codes: set[str]) -> None:
    if len(code) != 6 or not code.isdigit() or code in seen_codes:
        return
    seen_codes.add(code)
    codes.append(code)


def parse_mailtm_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_message_datetime(summary: dict[str, Any], full_message: dict[str, Any]) -> datetime | None:
    for key in ("createdAt", "created_at", "updatedAt", "updated_at"):
        parsed = parse_mailtm_datetime(summary.get(key))
        if parsed is not None:
            return parsed
        parsed = parse_mailtm_datetime(full_message.get(key))
        if parsed is not None:
            return parsed
    return None


class MailTmError(RuntimeError):
    pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nОстановлено.")
        sys.exit(0)
