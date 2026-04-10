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


def _build_run_summary_message(candidates: list[Candidate], added_task_ids: list[str]) -> str:
    """Build a plain-text summary for Telegram."""

    auto_add_candidates = [candidate for candidate in candidates if candidate.auto_add]
    added_candidates = auto_add_candidates[: len(added_task_ids)]
    optional_candidates = [
        candidate
        for candidate in candidates
        if candidate.candidate_class == "optional" and not candidate.scored_item.is_active
    ]
    skipped_active_candidates = [
        candidate for candidate in candidates if candidate.scored_item.is_active
    ]

    lines = [
        "Shopping replenisher summary",
        "",
        f"Candidates found: {len(candidates)}",
        "",
        "Items added:",
    ]
    if added_candidates:
        lines.extend(
            f"- {candidate.scored_item.canonical_name} ({candidate.candidate_class})"
            for candidate in added_candidates
        )
    else:
        lines.append("- none")

    lines.extend(["", "Optional items:"])
    if optional_candidates:
        lines.extend(f"- {candidate.scored_item.canonical_name}" for candidate in optional_candidates)
    else:
        lines.append("- none")

    lines.extend(["", "Skipped already active:"])
    if skipped_active_candidates:
        lines.extend(
            f"- {candidate.scored_item.canonical_name}"
            for candidate in skipped_active_candidates
        )
    else:
        lines.append("- none")

    return "\n".join(lines)
