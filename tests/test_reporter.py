"""Tests for local report generation."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from shopping_replenisher.reporter import build_summary_payload, write_report_artifacts
from shopping_replenisher.scoring import ScoredItem
from shopping_replenisher.selection import Candidate


def test_build_summary_payload_has_expected_json_structure() -> None:
    """The summary payload should expose counts and serialized candidate features."""

    candidate = _build_candidate()

    payload = build_summary_payload([candidate], generated_at=datetime(2026, 4, 9, 8, 30, 0))

    assert payload["generated_at"] == "2026-04-09T08:30:00"
    assert payload["candidate_count"] == 1
    assert payload["class_counts"] == {"now": 1, "soon": 0, "optional": 0}
    assert payload["candidates"] == [
        {
            "canonical_name": "milk",
            "display_name": "Milk",
            "original_names": ["Milk"],
            "candidate_class": "now",
            "auto_add": True,
            "occurrence_count": 4,
            "unique_days": 4,
            "gaps": [7, 7, 7],
            "typical_gap": 7.0,
            "gap_stddev": 0.0,
            "last_purchased": "2026-04-02",
            "days_since_last": 7,
            "overdue_ratio": 1.0,
            "is_active": False,
            "confidence": "medium",
        }
    ]


def test_write_report_artifacts_writes_json_markdown_and_csv(tmp_path: Path) -> None:
    """Artifact generation should create the expected local files and summary layout."""

    candidate = _build_candidate()

    artifacts = write_report_artifacts(
        [candidate],
        reports_root=tmp_path,
        generated_at=datetime(2026, 4, 9, 8, 30, 0),
    )

    summary_payload = json.loads(artifacts.summary_json_path.read_text(encoding="utf-8"))
    summary_markdown = artifacts.summary_md_path.read_text(encoding="utf-8")
    candidates_csv = artifacts.candidates_csv_path.read_text(encoding="utf-8")

    assert artifacts.report_dir.name == "20260409T083000000000"
    assert summary_payload["candidate_count"] == 1
    assert "# Prediction Summary" in summary_markdown
    assert (
        "| Item | Class | Auto-add | Confidence | Days Since Last | Typical Gap | Overdue Ratio |"
        in summary_markdown
    )
    assert "| Milk | now | true | medium | 7 | 7.00 | 1.00 |" in summary_markdown
    assert "display_name,canonical_name,candidate_class,auto_add,confidence" in candidates_csv
    assert "Milk,milk,now,true,medium" in candidates_csv


def test_write_report_artifacts_avoids_reusing_existing_directory(tmp_path: Path) -> None:
    """Artifact generation should allocate a fresh directory when the base name already exists."""

    candidate = _build_candidate()
    generated_at = datetime(2026, 4, 9, 8, 30, 0)

    first_artifacts = write_report_artifacts(
        [candidate],
        reports_root=tmp_path,
        generated_at=generated_at,
    )
    second_artifacts = write_report_artifacts(
        [candidate],
        reports_root=tmp_path,
        generated_at=generated_at,
    )

    assert first_artifacts.report_dir.name == "20260409T083000000000"
    assert second_artifacts.report_dir.name == "20260409T083000000000-1"
    assert second_artifacts.summary_json_path.exists()


def _build_candidate() -> Candidate:
    """Build a representative candidate for reporter tests."""

    return Candidate(
        scored_item=ScoredItem(
            canonical_name="milk",
            display_name="Milk",
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
