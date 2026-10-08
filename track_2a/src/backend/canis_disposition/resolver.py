"""Disposition resolution logic ported from the iOS prototype."""

from __future__ import annotations

from backend.canis_disposition.types import Disposition


SEED_SIMILARITY_THRESHOLD = 0.02
ENTROPY_GATE_ENABLED = False
ENTROPY_HIGH = 0.60
ENTROPY_LOW = 0.22


def resolve(seed_scores: dict[Disposition, float], entropy: float) -> Disposition:
    seed_disposition = max(seed_scores, key=seed_scores.get, default=Disposition.IDLE)
    seed_score = seed_scores.get(seed_disposition, 0.0)
    base = seed_disposition if seed_score >= SEED_SIMILARITY_THRESHOLD else Disposition.IDLE

    if base.is_safety_override:
        return base
    if ENTROPY_GATE_ENABLED and entropy >= ENTROPY_HIGH:
        return Disposition.UNCERTAIN
    if ENTROPY_GATE_ENABLED and entropy <= ENTROPY_LOW:
        return Disposition.CONFIDENT if base == Disposition.IDLE else base
    return base

