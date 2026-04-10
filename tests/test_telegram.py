"""Tests for Telegram notifications."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from urllib import error, request

import pytest

from shopping_replenisher.config import AppConfig
from shopping_replenisher.scoring import ScoredItem
from shopping_replenisher.selection import Candidate
from shopping_replenisher.telegram import TelegramAPIError, send_run_summary


def test_send_run_summary_posts_expected_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run summaries should be posted to the configured Telegram chat."""

    config = _build_config()
    candidates = [
        _build_candidate("milk", "now", True, is_active=False),
        _build_candidate("eggs", "soon", True, is_active=False),
        _build_candidate("jugo", "optional", False, is_active=False),
        _build_candidate("bread", "optional", False, is_active=True),
    ]
    captured: dict[str, object] = {}

    def fake_urlopen(http_request: request.Request) -> "_FakeResponse":
        headers = {key.lower(): value for key, value in http_request.header_items()}
        captured["url"] = http_request.full_url
        captured["method"] = http_request.get_method()
        captured["content_type"] = headers.get("content-type")
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return _FakeResponse('{"ok": true, "result": {"message_id": 1}}')

    monkeypatch.setattr("shopping_replenisher.telegram.request.urlopen", fake_urlopen)

    send_run_summary(config, candidates, added_task_ids=["task-1", "task-2"])

    assert captured["url"] == "https://api.telegram.org/botbot-token/sendMessage"
    assert captured["method"] == "POST"
    assert captured["content_type"] == "application/json"
    assert captured["body"] == {
        "chat_id": "chat-id",
        "text": "\n".join(
            [
                "Replenisher",
                "",
                "Overdue:",
                "- milk",
                "",
                "Coming up:",
                "- eggs",
                "",
                "On the radar: jugo",
            ]
        ),
    }


def test_send_run_summary_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Telegram HTTP failures should be wrapped in a TelegramAPIError."""

    config = _build_config()

    def fake_urlopen(http_request: request.Request) -> "_FakeResponse":
        raise error.HTTPError(
            url=http_request.full_url,
            code=500,
            msg="Internal Server Error",
            hdrs=None,
            fp=_FakeErrorResponse('{"ok":false}'),
        )

    monkeypatch.setattr("shopping_replenisher.telegram.request.urlopen", fake_urlopen)

    with pytest.raises(TelegramAPIError) as exc_info:
        send_run_summary(config, [], added_task_ids=[])

    assert "500" in str(exc_info.value)


def _build_config() -> AppConfig:
    """Build a config object for Telegram tests."""

    return AppConfig(
        todoist_db_path=Path("/tmp/todoist.db"),
        todoist_api_token="todoist-token",
        shopping_project_id="project-id",
        telegram_bot_token="bot-token",
        telegram_chat_id="chat-id",
        auto_apply=False,
        max_items_per_run=5,
        min_pattern_occurrences=4,
        min_confidence="medium",
        buy_soon_days=7,
        ignored_items=frozenset(),
        todoist_task_prefix="",
        log_level="INFO",
        timezone=None,
    )


def _build_candidate(
    canonical_name: str,
    candidate_class: str,
    auto_add: bool,
    *,
    is_active: bool,
) -> Candidate:
    """Build a representative candidate for Telegram tests."""

    return Candidate(
        scored_item=ScoredItem(
            canonical_name=canonical_name,
            original_names={canonical_name.title()},
            occurrence_count=4,
            unique_days=4,
            gaps=[7, 7, 7],
            typical_gap=7.0,
            gap_stddev=0.0,
            last_purchased=date(2026, 4, 2),
            days_since_last=7,
            overdue_ratio=1.0,
            is_active=is_active,
            confidence="medium",
        ),
        candidate_class=candidate_class,
        auto_add=auto_add,
    )


class _FakeResponse:
    """Minimal context-manager response for urllib tests."""

    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        """Return the mocked body."""

        return self._body

    def __enter__(self) -> "_FakeResponse":
        """Enter the response context manager."""

        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """Exit the response context manager."""

        return None


class _FakeErrorResponse:
    """Minimal file-like object for HTTPError bodies."""

    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        """Return the mocked error body."""

        return self._body

    def close(self) -> None:
        """Provide the close method expected by HTTPError cleanup."""

        return None
