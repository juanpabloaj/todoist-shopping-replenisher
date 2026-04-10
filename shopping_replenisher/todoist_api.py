"""Todoist REST API client for task creation."""

from __future__ import annotations

import json
import uuid
from urllib import error, request

from shopping_replenisher.config import AppConfig
from shopping_replenisher.selection import Candidate


TODOIST_TASKS_URL = "https://api.todoist.com/api/v1/tasks"


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

    try:
        with request.urlopen(http_request) as response:
            response_body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise TodoistAPIError(f"Todoist API request failed: {exc.code} {error_body}") from exc
    except error.URLError as exc:
        raise TodoistAPIError(f"Todoist API request failed: {exc.reason}") from exc

    try:
        response_payload = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise TodoistAPIError("Todoist API returned invalid JSON.") from exc

    task_id = response_payload.get("id")
    if not isinstance(task_id, (str, int)) or str(task_id) == "":
        raise TodoistAPIError("Todoist API response did not include a task id.")

    return str(task_id)


def _build_task_content(config: AppConfig, candidate: Candidate) -> str:
    """Build the Todoist task content from config and candidate data."""

    item_name = candidate.scored_item.canonical_name
    if not config.todoist_task_prefix:
        return item_name
    return f"{config.todoist_task_prefix}{item_name}"


def _build_project_id(project_id: str) -> str | int:
    """Convert a configured project id into the API payload representation."""

    if project_id.isdigit():
        return int(project_id)
    return project_id
