"""Read-only SQLite access for Todoist shopping data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import sqlite3


@dataclass(frozen=True)
class ActiveItemRow:
    """A currently active Todoist task in the shopping project."""

    task_id: str
    content: str


@dataclass(frozen=True)
class CompletionRow:
    """A historical completion record used for deduplication and scoring."""

    task_id: str
    content: str
    completed_at: datetime


def fetch_active_items(conn: sqlite3.Connection, project_id: str) -> list[ActiveItemRow]:
    """Fetch active tasks for the given shopping project."""

    query = """
        SELECT
            id,
            content
        FROM tasks
        WHERE project_id = ?
    """
    rows = conn.execute(query, (project_id,)).fetchall()
    return [
        ActiveItemRow(
            task_id=str(row[0]),
            content=str(row[1]),
        )
        for row in rows
    ]


def fetch_completion_event_rows(conn: sqlite3.Connection, project_id: str) -> list[CompletionRow]:
    """Fetch completion-event history rows for the given shopping project."""

    query = """
        SELECT
            task_id,
            content,
            event_date
        FROM completion_events
        WHERE parent_project_id = ?
    """
    rows = conn.execute(query, (project_id,)).fetchall()
    return [_build_completion_row(row) for row in rows]


def fetch_completed_task_rows(conn: sqlite3.Connection, project_id: str) -> list[CompletionRow]:
    """Fetch completed-task history rows for the given shopping project."""

    query = """
        SELECT
            task_id,
            content,
            completed_at
        FROM completed_tasks
        WHERE project_id = ?
    """
    rows = conn.execute(query, (project_id,)).fetchall()
    return [_build_completion_row(row) for row in rows]


def _build_completion_row(row: sqlite3.Row | tuple[object, ...]) -> CompletionRow:
    """Convert a SQLite row into a typed completion record."""

    task_id = str(row[0])
    content = str(row[1])
    completed_at = _parse_completed_at(row[2])
    return CompletionRow(
        task_id=task_id,
        content=content,
        completed_at=completed_at,
    )


def _parse_completed_at(value: object) -> datetime:
    """Parse a completion timestamp stored as a SQLite text value."""

    if not isinstance(value, str):
        raise TypeError("completed_at must be stored as a text timestamp.")

    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid completed_at timestamp: {value}") from exc

