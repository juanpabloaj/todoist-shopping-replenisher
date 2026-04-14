"""Tests for the SQLite read layer."""

from __future__ import annotations

from datetime import datetime
import sqlite3

import pytest

from shopping_replenisher.db import (
    ActiveItemRow,
    CompletionRow,
    fetch_active_items,
    fetch_completed_task_rows,
    fetch_completion_event_rows,
)


@pytest.fixture
def sqlite_conn() -> sqlite3.Connection:
    """Create an in-memory SQLite database with Todoist-like tables."""

    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE tasks (
            id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            content TEXT NOT NULL,
            checked INTEGER NOT NULL DEFAULT 0,
            is_deleted INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE completion_events (
            task_id TEXT NOT NULL,
            parent_project_id TEXT,
            content TEXT,
            event_date TEXT NOT NULL
        );

        CREATE TABLE completed_tasks (
            task_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            content TEXT NOT NULL,
            completed_at TEXT NOT NULL
        );
        """
    )

    conn.executemany(
        "INSERT INTO tasks (id, project_id, content, checked, is_deleted) VALUES (?, ?, ?, ?, ?)",
        [
            ("active-1", "shopping-project", "Milk", 0, 0),
            ("active-2", "shopping-project", "Eggs", 0, 0),
            ("active-3", "other-project", "Should Not Appear", 0, 0),
            ("active-4", "shopping-project", "Checked Item", 1, 0),
            ("active-5", "shopping-project", "Deleted Item", 0, 1),
        ],
    )
    conn.executemany(
        """
        INSERT INTO completion_events (task_id, parent_project_id, content, event_date)
        VALUES (?, ?, ?, ?)
        """,
        [
            ("event-1", "shopping-project", "Coca Cola", "2026-04-01T10:15:00"),
            ("event-2", "other-project", "Filtered Out", "2026-04-01T10:16:00"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO completed_tasks (task_id, project_id, content, completed_at)
        VALUES (?, ?, ?, ?)
        """,
        [
            ("completed-1", "shopping-project", "Queso", "2026-04-02T11:45:00"),
            ("completed-2", "other-project", "Filtered Out", "2026-04-02T11:50:00"),
        ],
    )

    yield conn
    conn.close()


def test_fetch_active_items_returns_typed_rows(
    sqlite_conn: sqlite3.Connection,
) -> None:
    """Active-item queries should return project-scoped typed rows."""

    rows = fetch_active_items(sqlite_conn, "shopping-project")

    assert set(rows) == {
        ActiveItemRow(task_id="active-1", content="Milk"),
        ActiveItemRow(task_id="active-2", content="Eggs"),
    }


def test_fetch_completion_event_rows_returns_typed_rows(
    sqlite_conn: sqlite3.Connection,
) -> None:
    """Completion-event queries should return project-scoped typed rows."""

    rows = fetch_completion_event_rows(sqlite_conn, "shopping-project")

    assert rows == [
        CompletionRow(
            task_id="event-1",
            content="Coca Cola",
            completed_at=datetime.fromisoformat("2026-04-01T10:15:00"),
        )
    ]


def test_fetch_completed_task_rows_returns_typed_rows(
    sqlite_conn: sqlite3.Connection,
) -> None:
    """Completed-task queries should return project-scoped typed rows."""

    rows = fetch_completed_task_rows(sqlite_conn, "shopping-project")

    assert rows == [
        CompletionRow(
            task_id="completed-1",
            content="Queso",
            completed_at=datetime.fromisoformat("2026-04-02T11:45:00"),
        )
    ]
