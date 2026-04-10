"""Tests for the Todoist write client."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from urllib import error, request

import pytest

from shopping_replenisher.config import AppConfig
from shopping_replenisher.scoring import ScoredItem
from shopping_replenisher.selection import Candidate
from shopping_replenisher.todoist_api import TodoistAPIError, create_task


def test_create_task_posts_expected_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """Task creation should send the expected Todoist REST payload."""

    config = _build_config(todoist_task_prefix="")
    candidate = _build_candidate()
    captured: dict[str, object] = {}

    def fake_urlopen(http_request: request.Request) -> "_FakeResponse":
        headers = {key.lower(): value for key, value in http_request.header_items()}
        captured["url"] = http_request.full_url
        captured["method"] = http_request.get_method()
        captured["authorization"] = headers.get("authorization")
        captured["content_type"] = headers.get("content-type")
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return _FakeResponse('{"id": "task-123"}')

    monkeypatch.setattr("shopping_replenisher.todoist_api.request.urlopen", fake_urlopen)

    task_id = create_task(config, candidate)

    assert task_id == "task-123"
    assert captured["url"] == "https://api.todoist.com/rest/v2/tasks"
    assert captured["method"] == "POST"
    assert captured["authorization"] == "Bearer token"
    assert captured["content_type"] == "application/json"
    assert captured["body"] == {
        "content": "milk",
        "project_id": "project-id",
    }


def test_create_task_applies_optional_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Task creation should prepend the configured task prefix when present."""

    config = _build_config(todoist_task_prefix="[buy] ")
    candidate = _build_candidate()
    captured: dict[str, object] = {}

    def fake_urlopen(http_request: request.Request) -> "_FakeResponse":
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return _FakeResponse('{"id": "task-456"}')

    monkeypatch.setattr("shopping_replenisher.todoist_api.request.urlopen", fake_urlopen)

    task_id = create_task(config, candidate)

    assert task_id == "task-456"
    assert captured["body"] == {
        "content": "[buy] milk",
        "project_id": "project-id",
    }


def test_create_task_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP failures should be wrapped in a TodoistAPIError."""

    config = _build_config(todoist_task_prefix="")
    candidate = _build_candidate()

    def fake_urlopen(http_request: request.Request) -> "_FakeResponse":
        raise error.HTTPError(
            url=http_request.full_url,
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=_FakeErrorResponse('{"error":"invalid request"}'),
        )

    monkeypatch.setattr("shopping_replenisher.todoist_api.request.urlopen", fake_urlopen)

    with pytest.raises(TodoistAPIError) as exc_info:
        create_task(config, candidate)

    assert "400" in str(exc_info.value)


def _build_config(*, todoist_task_prefix: str) -> AppConfig:
    """Build a config object for Todoist API tests."""

    return AppConfig(
        todoist_db_path=Path("/tmp/todoist.db"),
        todoist_api_token="token",
        shopping_project_id="project-id",
        telegram_bot_token="bot-token",
        telegram_chat_id="chat-id",
        auto_apply=False,
        max_items_per_run=5,
        prediction_window_days=7,
        min_pattern_occurrences=4,
        min_confidence="medium",
        buy_soon_days=7,
        ignored_items=frozenset(),
        enable_completion_events_backfill=True,
        todoist_task_prefix=todoist_task_prefix,
        log_level="INFO",
        timezone="your_timezone",
        overrule_active_duplicates=False,
        forgotten_ratio_threshold=1.75,
        dry_run_notify_empty=True,
    )


def _build_candidate() -> Candidate:
    """Build a representative candidate for Todoist API tests."""

    return Candidate(
        scored_item=ScoredItem(
            canonical_name="milk",
            original_names={"Milk"},
            occurrence_count=4,
            unique_days=4,
            gaps=[7, 7, 7],
            typical_gap=7.0,
            gap_stddev=0.0,
            last_purchased=date(2026, 4, 2),
            days_since_last=7,
            overdue_ratio=1.0,
            is_active=False,
            confidence="medium",
        ),
        candidate_class="now",
        auto_add=True,
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
