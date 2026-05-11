from __future__ import annotations

import json
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .scanner import load_accounts, scan_accounts

INDEX_HTML = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>mail.tm Code Report</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; background: #f8fafc; color: #0f172a; }
    main { max-width: 960px; margin: 0 auto; }
    button { border: 0; border-radius: 10px; padding: 0.8rem 1rem; background: #2563eb; color: white; font-weight: 700; cursor: pointer; }
    button:disabled { opacity: 0.6; cursor: progress; }
    .card { background: white; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1rem; margin: 1rem 0; box-shadow: 0 1px 2px rgb(15 23 42 / 0.05); }
    .error { color: #b91c1c; }
    code { background: #eef2ff; color: #3730a3; padding: 0.15rem 0.35rem; border-radius: 6px; }
    pre { white-space: pre-wrap; }
  </style>
</head>
<body>
<main>
  <h1>mail.tm Code Report</h1>
  <p>Проверяет аккаунты из <code>accounts.json</code> и ищет коды подтверждения в последних письмах.</p>
  <button id="scan">Анализировать аккаунты</button>
  <div id="status"></div>
  <section id="results"></section>
</main>
<script>
const button = document.querySelector("#scan");
const statusEl = document.querySelector("#status");
const resultsEl = document.querySelector("#results");

button.addEventListener("click", async () => {
  button.disabled = true;
  statusEl.textContent = "Идёт анализ...";
  resultsEl.innerHTML = "";
  try {
    const response = await fetch("/api/scan", { method: "POST" });
    const payload = await response.json();
    render(payload);
    statusEl.textContent = "Готово";
  } catch (error) {
    statusEl.textContent = "Ошибка анализа";
    resultsEl.innerHTML = `<div class="card error">${escapeHtml(String(error))}</div>`;
  } finally {
    button.disabled = false;
  }
});

function render(payload) {
  if (!payload.results?.length) {
    resultsEl.innerHTML = '<div class="card">Аккаунты не найдены.</div>';
    return;
  }
  resultsEl.innerHTML = payload.results.map(result => {
    if (result.error) {
      return `<article class="card"><h2>${escapeHtml(result.account)}</h2><p class="error">${escapeHtml(result.error)}</p></article>`;
    }
    if (!result.findings.length) {
      return `<article class="card"><h2>${escapeHtml(result.account)}</h2><p>Коды не найдены.</p></article>`;
    }
    const findings = result.findings.map(finding => `
      <li>
        <strong>${escapeHtml(finding.subject || "(без темы)")}</strong><br>
        Коды: ${finding.codes.map(code => `<code>${escapeHtml(code)}</code>`).join(" ")}<br>
        От: ${escapeHtml(finding.from_address || "unknown")}
      </li>
    `).join("");
    return `<article class="card"><h2>${escapeHtml(result.account)}</h2><ul>${findings}</ul></article>`;
  }).join("");
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[char]));
}
</script>
</body>
</html>
"""


def run_server(
    *,
    host: str,
    port: int,
    accounts_path: str,
    limit_per_account: int,
    base_url: str,
) -> None:
    handler = build_handler(
        accounts_path=Path(accounts_path),
        limit_per_account=limit_per_account,
        base_url=base_url,
    )
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Serving on http://{host}:{port}")
    server.serve_forever()


def build_handler(
    *,
    accounts_path: Path,
    limit_per_account: int,
    base_url: str,
) -> type[BaseHTTPRequestHandler]:
    class MailTmCodeReportHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                self._send_html(INDEX_HTML)
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            if self.path != "/api/scan":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                accounts = load_accounts(accounts_path)
                results = scan_accounts(
                    accounts,
                    limit_per_account=limit_per_account,
                    base_url=base_url,
                )
                self._send_json({"results": [asdict(result) for result in results]})
            except (OSError, ValueError) as error:
                self._send_json({"results": [], "error": str(error)}, status=HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_html(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return MailTmCodeReportHandler
