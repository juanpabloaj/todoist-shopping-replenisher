"""Configuration loading for the shopping replenisher."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

from shopping_replenisher.normalize import normalize


class ConfigError(ValueError):
    """Raised when application configuration is invalid."""


@dataclass(frozen=True)
class AppConfig:
    """Application configuration loaded from environment variables."""

    todoist_db_path: Path
    todoist_api_token: str
    shopping_project_id: str
    telegram_bot_token: str
    telegram_chat_id: str
    auto_apply: bool
    max_items_per_run: int
    prediction_window_days: int
    min_pattern_occurrences: int
    min_confidence: str
    buy_soon_days: int
    ignored_items: frozenset[str]
    enable_completion_events_backfill: bool
    todoist_task_prefix: str
    log_level: str
    timezone: str
    overrule_active_duplicates: bool
    forgotten_ratio_threshold: float
    dry_run_notify_empty: bool


REQUIRED_ENV_VARS: tuple[str, ...] = (
    "TODOIST_DB_PATH",
    "TODOIST_API_TOKEN",
    "SHOPPING_PROJECT_ID",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
)


def load_config(dotenv_path: str | Path | None = None) -> AppConfig:
    """Load application configuration from environment variables and .env."""

    load_dotenv(dotenv_path=dotenv_path, override=False)

    missing_vars = [name for name in REQUIRED_ENV_VARS if not _get_required_str(name)]
    if missing_vars:
        missing_list = ", ".join(sorted(missing_vars))
        raise ConfigError(f"Missing required environment variables: {missing_list}")

    return AppConfig(
        todoist_db_path=Path(_get_required_str("TODOIST_DB_PATH")),
        todoist_api_token=_get_required_str("TODOIST_API_TOKEN"),
        shopping_project_id=_get_required_str("SHOPPING_PROJECT_ID"),
        telegram_bot_token=_get_required_str("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_get_required_str("TELEGRAM_CHAT_ID"),
        auto_apply=_get_bool("AUTO_APPLY", default=False),
        max_items_per_run=_get_int("MAX_ITEMS_PER_RUN", default=5),
        prediction_window_days=_get_int("PREDICTION_WINDOW_DAYS", default=7),
        min_pattern_occurrences=_get_int("MIN_PATTERN_OCCURRENCES", default=4),
        min_confidence=_get_str("MIN_CONFIDENCE", default="medium"),
        buy_soon_days=_get_int("BUY_SOON_DAYS", default=7),
        ignored_items=_get_ignored_items("IGNORED_ITEMS"),
        enable_completion_events_backfill=_get_bool(
            "ENABLE_COMPLETION_EVENTS_BACKFILL",
            default=True,
        ),
        todoist_task_prefix=_get_str("TODOIST_TASK_PREFIX", default=""),
        log_level=_get_str("LOG_LEVEL", default="INFO"),
        timezone=_get_str("TIMEZONE", default="your_timezone"),
        overrule_active_duplicates=_get_bool("OVERRULE_ACTIVE_DUPLICATES", default=False),
        forgotten_ratio_threshold=_get_float("FORGOTTEN_RATIO_THRESHOLD", default=1.75),
        dry_run_notify_empty=_get_bool("DRY_RUN_NOTIFY_EMPTY", default=True),
    )


def _get_required_str(name: str) -> str:
    """Read a required non-empty string environment variable."""

    value = os.getenv(name, "").strip()
    return value


def _get_str(name: str, default: str) -> str:
    """Read a string environment variable with a default."""

    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _get_int(name: str, default: int) -> int:
    """Read an integer environment variable with a default."""

    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"Environment variable {name} must be an integer.") from exc


def _get_float(name: str, default: float) -> float:
    """Read a float environment variable with a default."""

    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ConfigError(f"Environment variable {name} must be a float.") from exc


def _get_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable with a default."""

    value = os.getenv(name)
    if value is None or not value.strip():
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"Environment variable {name} must be a boolean.")


def _get_ignored_items(name: str) -> frozenset[str]:
    """Read a comma-separated set of ignored canonical item names."""

    value = os.getenv(name)
    if value is None or not value.strip():
        return frozenset()

    ignored_items = [
        normalize(item.strip())
        for item in value.split(",")
        if item.strip()
    ]
    return frozenset(ignored_items)
