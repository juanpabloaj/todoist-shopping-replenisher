"""Local report generation for prediction runs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from shopping_replenisher.selection import Candidate


@dataclass(frozen=True)
class ReportArtifacts:
    """Filesystem paths for generated local report artifacts."""

    report_dir: Path
    summary_json_path: Path
    summary_md_path: Path
    candidates_csv_path: Path


def build_summary_payload(
    candidates: list[Candidate],
    *,
    generated_at: datetime,
) -> dict[str, object]:
    """Build the JSON-serializable summary payload for a prediction run."""

    class_counts = {
        "now": sum(1 for candidate in candidates if candidate.candidate_class == "now"),
        "soon": sum(1 for candidate in candidates if candidate.candidate_class == "soon"),
        "optional": sum(1 for candidate in candidates if candidate.candidate_class == "optional"),
    }
    return {
        "generated_at": generated_at.isoformat(),
        "candidate_count": len(candidates),
        "class_counts": class_counts,
        "candidates": [_serialize_candidate(candidate) for candidate in candidates],
    }


def write_report_artifacts(
    candidates: list[Candidate],
    *,
    reports_root: Path,
    generated_at: datetime,
    payload: dict[str, object] | None = None,
) -> ReportArtifacts:
    """Write JSON, Markdown, and CSV artifacts for a prediction run."""

    report_dir = _allocate_report_dir(reports_root, generated_at)

    if payload is None:
        payload = build_summary_payload(candidates, generated_at=generated_at)
    summary_json_path = report_dir / "summary.json"
    summary_md_path = report_dir / "summary.md"
    candidates_csv_path = report_dir / "candidates.csv"

    summary_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary_md_path.write_text(
        render_summary_markdown(payload),
        encoding="utf-8",
    )
    write_candidates_csv(payload, candidates_csv_path)

    return ReportArtifacts(
        report_dir=report_dir,
        summary_json_path=summary_json_path,
        summary_md_path=summary_md_path,
        candidates_csv_path=candidates_csv_path,
    )


def _allocate_report_dir(reports_root: Path, generated_at: datetime) -> Path:
    """Allocate a unique report directory without silently reusing old artifacts."""

    base_name = generated_at.strftime("%Y%m%dT%H%M%S%f")
    for suffix in range(1000):
        dir_name = base_name if suffix == 0 else f"{base_name}-{suffix}"
        report_dir = reports_root / dir_name
        try:
            report_dir.mkdir(parents=True, exist_ok=False)
            return report_dir
        except FileExistsError:
            continue

    raise RuntimeError(f"Failed to allocate a unique report directory for base name {base_name}.")


def render_summary_markdown(payload: dict[str, object]) -> str:
    """Render a human-readable Markdown summary from the payload."""

    class_counts = payload["class_counts"]
    candidates = payload["candidates"]

    lines = [
        "# Prediction Summary",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Candidates: `{payload['candidate_count']}`",
        f"- `now`: `{class_counts['now']}`",
        f"- `soon`: `{class_counts['soon']}`",
        f"- `optional`: `{class_counts['optional']}`",
        "",
        "## Candidates",
        "",
    ]

    if not candidates:
        lines.append("No candidates found.")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            "| Item | Class | Auto-add | Confidence | Days Since Last | Typical Gap | Overdue Ratio |",
            "|---|---|---|---|---:|---:|---:|",
        ]
    )

    for candidate in candidates:
        lines.append(
            "| {display_name} | {candidate_class} | {auto_add} | {confidence} | "
            "{days_since_last} | {typical_gap} | {overdue_ratio} |".format(
                display_name=candidate["display_name"],
                candidate_class=candidate["candidate_class"],
                auto_add=str(candidate["auto_add"]).lower(),
                confidence=candidate["confidence"],
                days_since_last=candidate["days_since_last"],
                typical_gap=_format_number(candidate["typical_gap"]),
                overdue_ratio=_format_number(candidate["overdue_ratio"]),
            )
        )

    lines.append("")
    return "\n".join(lines)


def write_candidates_csv(payload: dict[str, object], csv_path: Path) -> None:
    """Write the candidate summary as CSV."""

    fieldnames = [
        "display_name",
        "canonical_name",
        "candidate_class",
        "auto_add",
        "confidence",
        "occurrence_count",
        "unique_days",
        "gaps",
        "typical_gap",
        "gap_stddev",
        "last_purchased",
        "days_since_last",
        "overdue_ratio",
        "is_active",
        "original_names",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in payload["candidates"]:
            writer.writerow(
                {
                    "display_name": candidate["display_name"],
                    "canonical_name": candidate["canonical_name"],
                    "candidate_class": candidate["candidate_class"],
                    "auto_add": str(candidate["auto_add"]).lower(),
                    "confidence": candidate["confidence"],
                    "occurrence_count": candidate["occurrence_count"],
                    "unique_days": candidate["unique_days"],
                    "gaps": ",".join(str(gap) for gap in candidate["gaps"]),
                    "typical_gap": _format_number(candidate["typical_gap"]),
                    "gap_stddev": _format_number(candidate["gap_stddev"]),
                    "last_purchased": candidate["last_purchased"],
                    "days_since_last": candidate["days_since_last"],
                    "overdue_ratio": _format_number(candidate["overdue_ratio"]),
                    "is_active": str(candidate["is_active"]).lower(),
                    "original_names": ",".join(candidate["original_names"]),
                }
            )


def _serialize_candidate(candidate: Candidate) -> dict[str, object]:
    """Convert a candidate into a JSON-serializable dictionary."""

    scored_item = candidate.scored_item
    return {
        "canonical_name": scored_item.canonical_name,
        "display_name": scored_item.display_name,
        "original_names": sorted(scored_item.original_names),
        "candidate_class": candidate.candidate_class,
        "auto_add": candidate.auto_add,
        "occurrence_count": scored_item.occurrence_count,
        "unique_days": scored_item.unique_days,
        "gaps": scored_item.gaps,
        "typical_gap": scored_item.typical_gap,
        "gap_stddev": scored_item.gap_stddev,
        "last_purchased": scored_item.last_purchased.isoformat(),
        "days_since_last": scored_item.days_since_last,
        "overdue_ratio": scored_item.overdue_ratio,
        "is_active": scored_item.is_active,
        "confidence": scored_item.confidence,
    }


def _format_number(value: object) -> str:
    """Format numeric values for Markdown and CSV output."""

    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)
