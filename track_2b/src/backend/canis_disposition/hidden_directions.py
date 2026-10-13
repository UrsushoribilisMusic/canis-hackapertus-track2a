"""Hidden-state disposition scorer backed by compact Canis artifacts."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from backend.canis_disposition.entropy import normalized_entropy
from backend.canis_disposition.resolver import resolve
from backend.canis_disposition.types import Disposition, DispositionReadout


ARTIFACT_PATH = Path(__file__).resolve().parent / "artifacts" / "hidden_directions.json"


def normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0:
        return [float(value) for value in vector]
    return [float(value) / norm for value in vector]


@lru_cache(maxsize=1)
def load_hidden_directions() -> dict[Disposition, list[float]]:
    if not ARTIFACT_PATH.exists():
        return {}
    payload = json.loads(ARTIFACT_PATH.read_text())
    directions: dict[Disposition, list[float]] = {}
    for key, vector in payload.items():
        try:
            disposition = Disposition(key)
        except ValueError:
            continue
        if isinstance(vector, list) and vector:
            directions[disposition] = normalize([float(value) for value in vector])
    return directions


def score_hidden_state(hidden_state: Sequence[float]) -> dict[Disposition, float]:
    hidden = normalize(hidden_state)
    scores: dict[Disposition, float] = {}
    for disposition, direction in load_hidden_directions().items():
        scores[disposition] = sum(left * right for left, right in zip(hidden, direction))
    return scores


def hidden_direction_readout(
    hidden_state: Sequence[float],
    logits: Sequence[float],
) -> DispositionReadout | None:
    scores = score_hidden_state(hidden_state)
    if not scores:
        return None
    entropy = normalized_entropy(logits)
    return DispositionReadout(
        disposition=resolve(scores, entropy),
        entropy=entropy,
        seed_scores=scores,
        tokens=[],
        source="forwardLens",
    )
