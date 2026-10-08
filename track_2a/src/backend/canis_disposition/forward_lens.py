"""Forward-lens helpers for the upcoming Apertus hidden-state path."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from backend.canis_disposition.entropy import normalized_entropy
from backend.canis_disposition.resolver import resolve
from backend.canis_disposition.types import Disposition, DispositionReadout, DispositionToken


def normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0:
        return list(vector)
    return [value / norm for value in vector]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    left = normalize(a)
    right = normalize(b)
    return sum(x * y for x, y in zip(left, right, strict=False))


def score_seed_vectors(j_space: Sequence[float], seed_vectors: dict[Disposition, Sequence[float]]) -> dict[Disposition, float]:
    return {disposition: cosine(j_space, seed) for disposition, seed in seed_vectors.items()}


def project(hidden_state: Sequence[float], projection: Sequence[Sequence[float]]) -> list[float]:
    return [sum(weight * value for weight, value in zip(row, hidden_state, strict=False)) for row in projection]


def forward_readout(
    hidden_state: Sequence[float],
    logits: Sequence[float],
    projection: Sequence[Sequence[float]],
    seed_vectors: dict[Disposition, Sequence[float]],
    token_labels: Iterable[str] = (),
) -> DispositionReadout:
    j_space = project(hidden_state, projection)
    scores = score_seed_vectors(j_space, seed_vectors)
    entropy = normalized_entropy(logits)
    tokens = [
        DispositionToken(token=token, weight=weight)
        for token, weight in zip(token_labels, logits, strict=False)
    ]
    tokens.sort(key=lambda item: item.weight, reverse=True)
    return DispositionReadout(
        disposition=resolve(scores, entropy),
        entropy=entropy,
        seed_scores=scores,
        tokens=tokens[:6],
        source="forwardLens",
    )

