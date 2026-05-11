from __future__ import annotations

import html
import re

DEFAULT_CODE_PATTERN = re.compile(r"(?<![A-Z0-9])(?:\d{4,8}|[A-Z0-9]{6,10})(?![A-Z0-9])", re.IGNORECASE)
CONTEXT_PATTERN = re.compile(
    r"(code|код|verification|verify|confirm|confirmation|otp|парол|подтвержд)",
    re.IGNORECASE,
)
TAG_PATTERN = re.compile(r"<[^>]+>")


def extract_codes(text: str, custom_pattern: str | None = None) -> list[str]:
    cleaned = normalize_message_text(text)
    pattern = re.compile(custom_pattern) if custom_pattern else DEFAULT_CODE_PATTERN
    candidates: list[tuple[int, str]] = []
    for match in pattern.finditer(cleaned):
        code = match.group(0).strip()
        if not code or code.lower() in {"mailtm", "mailto"}:
            continue
        window_start = max(0, match.start() - 80)
        window_end = min(len(cleaned), match.end() + 80)
        context = cleaned[window_start:window_end]
        priority = 0 if CONTEXT_PATTERN.search(context) else 1
        candidates.append((priority, code))

    result: list[str] = []
    seen: set[str] = set()
    for _, code in sorted(candidates, key=lambda item: item[0]):
        normalized = code.upper()
        if normalized not in seen:
            seen.add(normalized)
            result.append(code)
    return result


def normalize_message_text(text: str) -> str:
    without_tags = TAG_PATTERN.sub(" ", text)
    unescaped = html.unescape(without_tags)
    return re.sub(r"\s+", " ", unescaped).strip()
