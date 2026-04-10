"""Candidate filtering and ranking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from shopping_replenisher.config import AppConfig
from shopping_replenisher.db import ActiveItemRow
from shopping_replenisher.history import ItemHistory
from shopping_replenisher.normalize import normalize
from shopping_replenisher.scoring import ScoredItem, score_item_history


CandidateClass = str
_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class Candidate:
    """A scored item with its final candidate class."""

    scored_item: ScoredItem
    candidate_class: CandidateClass
    auto_add: bool


def select_candidates(
    histories: dict[str, ItemHistory],
    active_items: list[ActiveItemRow],
    config: AppConfig,
    today: date,
) -> list[Candidate]:
    """Filter, classify, rank, and cap candidate items."""

    active_canonical_names = {normalize(item.content) for item in active_items}

    candidates: list[Candidate] = []
    for canonical_name, history in histories.items():
        if canonical_name in config.ignored_items:
            continue

        scored_item = score_item_history(
            history,
            today=today,
            is_active=canonical_name in active_canonical_names,
        )
        if not _passes_candidate_filters(scored_item, config):
            continue

        candidate_class = _classify_candidate(scored_item, config)
        candidates.append(
            Candidate(
                scored_item=scored_item,
                candidate_class=candidate_class,
                auto_add=candidate_class in {"now", "soon"},
            )
        )

    ranked_candidates = sorted(
        candidates,
        key=lambda candidate: (
            _candidate_priority(candidate),
            -(candidate.scored_item.overdue_ratio or 0.0),
            candidate.scored_item.canonical_name,
        ),
    )

    auto_add_count = 0
    limited_candidates: list[Candidate] = []
    for candidate in ranked_candidates:
        if candidate.auto_add:
            if auto_add_count >= config.max_items_per_run:
                continue
            auto_add_count += 1
        limited_candidates.append(candidate)

    return limited_candidates


def _passes_candidate_filters(scored_item: ScoredItem, config: AppConfig) -> bool:
    """Apply the Stage 5 selection filters."""

    if scored_item.unique_days < config.min_pattern_occurrences:
        return False
    if scored_item.typical_gap is None:
        return False
    if scored_item.is_active:
        return False
    if scored_item.overdue_ratio is None:
        return False
    return _CONFIDENCE_RANK[scored_item.confidence] >= _CONFIDENCE_RANK[config.min_confidence]


def _classify_candidate(scored_item: ScoredItem, config: AppConfig) -> CandidateClass:
    """Classify a scored item into now, soon, or optional."""

    assert scored_item.overdue_ratio is not None
    assert scored_item.typical_gap is not None

    if scored_item.overdue_ratio >= 1.0:
        return "now"

    days_until_due = scored_item.typical_gap - scored_item.days_since_last
    if days_until_due <= config.buy_soon_days:
        return "soon"

    return "optional"


def _candidate_priority(candidate: Candidate) -> int:
    """Sort now before soon before optional."""

    if candidate.candidate_class == "now":
        return 0
    if candidate.candidate_class == "soon":
        return 1
    return 2
