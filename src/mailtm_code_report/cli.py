from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .notifier import notify_findings
from .scanner import CodeFinding, load_accounts, scan_accounts
from .server import run_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mailtm-code-report")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan mail.tm accounts once")
    scan_parser.add_argument("--accounts", default="accounts.json", help="Path to accounts JSON")
    scan_parser.add_argument("--limit", type=int, default=10, help="Messages to inspect per account")
    scan_parser.add_argument("--code-regex", help="Custom regex for extracting codes")
    scan_parser.add_argument("--base-url", default="https://api.mail.tm", help="mail.tm API base URL")
    scan_parser.add_argument(
        "--notify",
        choices=["none", "telegram", "webhook"],
        default="none",
        help="Send found codes through a notifier",
    )

    server_parser = subparsers.add_parser("server", help="Run local web UI")
    server_parser.add_argument("--accounts", default="accounts.json", help="Path to accounts JSON")
    server_parser.add_argument("--host", default="127.0.0.1")
    server_parser.add_argument("--port", type=int, default=8000)
    server_parser.add_argument("--limit", type=int, default=10)
    server_parser.add_argument("--base-url", default="https://api.mail.tm")

    args = parser.parse_args(argv)
    if args.command == "scan":
        accounts = load_accounts(args.accounts)
        results = scan_accounts(
            accounts,
            limit_per_account=args.limit,
            code_regex=args.code_regex,
            base_url=args.base_url,
        )
        findings = [finding for result in results for finding in result.findings]
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
        notify_findings(findings, args.notify)
        return 0 if all(result.error is None for result in results) else 1

    if args.command == "server":
        run_server(
            host=args.host,
            port=args.port,
            accounts_path=args.accounts,
            limit_per_account=args.limit,
            base_url=args.base_url,
        )
        return 0

    return 1


def format_findings(findings: list[CodeFinding]) -> str:
    if not findings:
        return "No codes found."
    return "\n".join(
        f"{finding.account}: {', '.join(finding.codes)} ({finding.subject})"
        for finding in findings
    )
