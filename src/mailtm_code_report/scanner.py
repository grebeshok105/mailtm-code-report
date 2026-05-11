from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .client import MailTmClient, MailTmError
from .extractor import extract_codes


@dataclass(frozen=True)
class AccountCredentials:
    address: str
    password: str


@dataclass(frozen=True)
class CodeFinding:
    account: str
    message_id: str
    from_address: str
    subject: str
    codes: list[str]
    created_at: str


@dataclass(frozen=True)
class AccountScanResult:
    account: str
    findings: list[CodeFinding]
    error: str | None = None


def load_accounts(path: str | Path) -> list[AccountCredentials]:
    account_path = Path(path)
    raw_content = account_path.read_text(encoding="utf-8")
    if account_path.suffix.lower() == ".txt":
        return load_accounts_text(raw_content)

    payload = json.loads(raw_content)
    items = payload.get("accounts") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError("Accounts file must contain a list or an object with an accounts list")

    accounts: list[AccountCredentials] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each account entry must be an object")
        address = item.get("address")
        password = item.get("password")
        if not isinstance(address, str) or not isinstance(password, str) or not address or not password:
            raise ValueError("Each account must have non-empty address and password fields")
        accounts.append(AccountCredentials(address=address, password=password))
    return accounts


def load_accounts_text(raw_content: str) -> list[AccountCredentials]:
    accounts: list[AccountCredentials] = []
    for line_number, raw_line in enumerate(raw_content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Line {line_number}: expected email:password")
        address, password = line.split(":", 1)
        address = address.strip()
        password = password.strip()
        if not address or not password:
            raise ValueError(f"Line {line_number}: email and password must be non-empty")
        accounts.append(AccountCredentials(address=address, password=password))
    return accounts


def scan_accounts(
    accounts: list[AccountCredentials],
    *,
    limit_per_account: int = 10,
    code_regex: str | None = None,
    base_url: str = "https://api.mail.tm",
) -> list[AccountScanResult]:
    results: list[AccountScanResult] = []
    for account in accounts:
        client = MailTmClient(base_url=base_url)
        try:
            client.login(account.address, account.password)
            summaries = client.list_messages()[:limit_per_account]
            findings: list[CodeFinding] = []
            for summary in summaries:
                message = client.get_message(summary.id)
                searchable = "\n".join(
                    [
                        message.subject,
                        message.intro,
                        message.text,
                        message.html,
                    ]
                )
                codes = extract_codes(searchable, custom_pattern=code_regex)
                if codes:
                    findings.append(
                        CodeFinding(
                            account=account.address,
                            message_id=message.id,
                            from_address=message.from_address,
                            subject=message.subject,
                            codes=codes,
                            created_at=message.created_at,
                        )
                    )
            results.append(AccountScanResult(account=account.address, findings=findings))
        except (MailTmError, ValueError) as error:
            results.append(AccountScanResult(account=account.address, findings=[], error=str(error)))
    return results
