"""Todoist REST API client for task creation."""

from __future__ import annotations

import json
import logging
import time
import uuid
from urllib import error, request

from shopping_replenisher.config import AppConfig
from shopping_replenisher.selection import Candidate


logger = logging.getLogger(__name__)

TODOIST_TASKS_URL = "https://api.todoist.com/api/v1/tasks"
REQUEST_TIMEOUT_SECONDS = 30
# Todoist returns transient 5xx/429 responses; retry those a few times before giving up.
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = (2.0, 5.0)
MAX_RETRY_AFTER_SECONDS = 30.0
RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


class TodoistAPIError(RuntimeError):
    """Raised when the Todoist API returns an invalid or failed response."""


def create_task(config: AppConfig, candidate: Candidate) -> str:
    """Create a Todoist task for a selected candidate and return its task id."""

    content = _build_task_content(config, candidate)
    payload = {
        "content": content,
        "project_id": _build_project_id(config.shopping_project_id),
    }
    request_body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        TODOIST_TASKS_URL,
        data=request_body,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.todoist_api_token}",
            "Content-Type": "application/json",
            "X-Request-Id": str(uuid.uuid4()),
        },
    )

    response_body = _send_with_retries(http_request, candidate)

    try:
        response_payload = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise TodoistAPIError("Todoist API returned invalid JSON.") from exc

    task_id = response_payload.get("id")
    if not isinstance(task_id, (str, int)) or str(task_id) == "":
        raise TodoistAPIError("Todoist API response did not include a task id.")

    return str(task_id)


def _send_with_retries(http_request: request.Request, candidate: Candidate) -> str:
    """Send the request, retrying transient failures, and return the response body."""

    item_name = candidate.scored_item.canonical_name
    last_error: TodoistAPIError | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with request.urlopen(http_request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return response.read().decode("utf-8")
        except error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            last_error = TodoistAPIError(f"Todoist API request failed: {exc.code} {error_body}")
            if exc.code not in RETRYABLE_STATUS_CODES:
                raise last_error from exc
            delay = _retry_delay(attempt, retry_after=_parse_retry_after(exc))
        except error.URLError as exc:
            last_error = TodoistAPIError(f"Todoist API request failed: {exc.reason}")
            delay = _retry_delay(attempt, retry_after=None)

        if attempt == MAX_ATTEMPTS:
            break

        logger.warning(
            "todoist request retry item=%s attempt=%s/%s delay=%.1fs error=%s",
            item_name,
            attempt,
            MAX_ATTEMPTS,
            delay,
            last_error,
        )
        time.sleep(delay)

    assert last_error is not None
    raise last_error


def _retry_delay(attempt: int, *, retry_after: float | None) -> float:
    """Return how long to wait before the next attempt."""

    if retry_after is not None:
        return retry_after
    index = min(attempt, len(RETRY_BACKOFF_SECONDS)) - 1
    return RETRY_BACKOFF_SECONDS[index]


def _parse_retry_after(exc: error.HTTPError) -> float | None:
    """Return the Retry-After delay in seconds when the server sent a usable one."""

    headers = getattr(exc, "headers", None)
    raw_value = headers.get("Retry-After") if headers is not None else None
    if raw_value is None:
        return None
    try:
        seconds = float(str(raw_value).strip())
    except ValueError:
        return None
    if seconds < 0:
        return None
    return min(seconds, MAX_RETRY_AFTER_SECONDS)


def _build_task_content(config: AppConfig, candidate: Candidate) -> str:
    """Build the Todoist task content from config and candidate data."""

    item_name = candidate.scored_item.display_name
    if not config.todoist_task_prefix:
        return item_name
    return f"{config.todoist_task_prefix}{item_name}"


def _build_project_id(project_id: str) -> str | int:
    """Convert a configured project id into the API payload representation."""

    if project_id.isdigit():
        return int(project_id)
    return project_id
