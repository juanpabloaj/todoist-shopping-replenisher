"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from shopping_replenisher.config import AppConfig, ConfigError, load_config


REQUIRED_ENV_VARS: tuple[str, ...] = (
    "TODOIST_DB_PATH",
    "TODOIST_API_TOKEN",
    "SHOPPING_PROJECT_ID",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
)


def test_load_config_requires_all_required_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """The loader should fail fast when required variables are missing."""

    for name in REQUIRED_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ConfigError) as exc_info:
        load_config(dotenv_path="tests/does-not-exist.env")

    message = str(exc_info.value)
    for name in REQUIRED_ENV_VARS:
        assert name in message


def test_load_config_accepts_required_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """The loader should build a config object when required variables are present."""

    monkeypatch.setenv("TODOIST_DB_PATH", "/tmp/todoist.db")
    monkeypatch.setenv("TODOIST_API_TOKEN", "token")
    monkeypatch.setenv("SHOPPING_PROJECT_ID", "project-id")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat-id")

    config = load_config(dotenv_path="tests/does-not-exist.env")

    assert isinstance(config, AppConfig)
    assert config.todoist_db_path == Path("/tmp/todoist.db")
    assert config.todoist_api_token == "token"
    assert config.shopping_project_id == "project-id"
    assert config.telegram_bot_token == "bot-token"
    assert config.telegram_chat_id == "chat-id"
    assert config.auto_apply is False
    assert config.max_items_per_run == 5
