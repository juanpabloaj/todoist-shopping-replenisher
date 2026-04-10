"""Telegram Bot API notifications for run summaries and errors."""

from __future__ import annotations

import json
from urllib import error, request

from shopping_replenisher.config import AppConfig
from shopping_replenisher.selection import Candidate


class TelegramAPIError(RuntimeError):
    """Raised when the Telegram Bot API returns an invalid or failed response."""


def send_run_summary(
    config: AppConfig,
    candidates: list[Candidate],
    added_task_ids: list[str],
) -> None:
    """Send a run summary message to the configured Telegram chat."""

    message = _build_run_summary_message(candidates, added_task_ids)
    _send_message(config, message)


def send_error(config: AppConfig, error_message: str) -> None:
    """Send an error notification to the configured Telegram chat."""

    message = "\n".join(
        [
            "Shopping replenisher error",
            "",
            error_message,
        ]
    )
    _send_message(config, message)


def _send_message(config: AppConfig, message: str) -> None:
    """Send a plain-text Telegram message."""

    payload = {
        "chat_id": config.telegram_chat_id,
        "text": message,
    }
    endpoint = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    request_body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        endpoint,
        data=request_body,
        method="POST",
        headers={
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(http_request) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise TelegramAPIError(f"Telegram API request failed: {exc.code} {error_body}") from exc
    except error.URLError as exc:
        raise TelegramAPIError(f"Telegram API request failed: {exc.reason}") from exc

    try:
        response_payload = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise TelegramAPIError("Telegram API returned invalid JSON.") from exc

    if not response_payload.get("ok", False):
        raise TelegramAPIError("Telegram API returned ok=false.")


def _build_run_summary_message(
    candidates: list[Candidate],
    added_task_ids: list[str],
) -> str:
    """Build a human-friendly plain-text summary for Telegram."""

    auto_add_candidates = [c for c in candidates if c.auto_add and not c.scored_item.is_active]
    added_candidates = auto_add_candidates[: len(added_task_ids)]
    now_candidates = [c for c in added_candidates if c.candidate_class == "now"]
    soon_candidates = [c for c in added_candidates if c.candidate_class == "soon"]
    optional_candidates = [
        c for c in candidates if c.candidate_class == "optional" and not c.scored_item.is_active
    ]

    lines = ["Replenisher", ""]

    if not added_candidates and not optional_candidates:
        lines.append("Nothing to replenish today.")
        return "\n".join(lines)

    if now_candidates:
        lines.append("Overdue:")
        lines.extend(f"- {c.scored_item.canonical_name}" for c in now_candidates)
        lines.append("")

    if soon_candidates:
        lines.append("Coming up:")
        lines.extend(f"- {c.scored_item.canonical_name}" for c in soon_candidates)
        lines.append("")

    if optional_candidates:
        names = ", ".join(c.scored_item.canonical_name for c in optional_candidates)
        lines.append(f"On the radar: {names}")

    return "\n".join(lines).rstrip()
