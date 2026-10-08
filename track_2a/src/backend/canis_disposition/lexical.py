"""Lexical fallback disposition readout.

This is a direct Python port of the current Swift fallback. It keeps the demo
honest while the forward-lens path is being wired to Apertus hidden states.
"""

from __future__ import annotations

from backend.canis_disposition.resolver import resolve
from backend.canis_disposition.types import Disposition, DispositionReadout, DispositionToken


LEXICAL_SEEDS: dict[Disposition, list[tuple[str, float]]] = {
    Disposition.CONFIDENT: [
        ("certain", 0.42),
        ("definitely", 0.48),
        ("confirmed", 0.42),
        ("correct", 0.36),
        ("yes", 0.30),
    ],
    Disposition.UNCERTAIN: [
        ("not sure", 0.56),
        ("maybe", 0.46),
        ("uncertain", 0.54),
        ("might", 0.34),
        ("depends", 0.30),
    ],
    Disposition.CURIOUS: [
        ("how", 0.30),
        ("why", 0.32),
        ("interesting", 0.36),
        ("wonder", 0.34),
        ("question", 0.28),
    ],
    Disposition.CONCERN: [
        ("danger", 0.62),
        ("unsafe", 0.58),
        ("risk", 0.46),
        ("warning", 0.54),
        ("harm", 0.48),
        ("stop", 0.40),
    ],
    Disposition.RELUCTANT: [
        ("cannot", 0.58),
        ("can't", 0.52),
        ("unable", 0.52),
        ("decline", 0.54),
        ("sorry", 0.34),
        ("not able", 0.48),
    ],
    Disposition.WARM: [
        ("great", 0.44),
        ("happy", 0.40),
        ("glad", 0.40),
        ("wonderful", 0.52),
        ("excellent", 0.48),
        ("thanks", 0.30),
    ],
    Disposition.MISCHIEF: [
        ("loophole", 0.62),
        ("bypass", 0.58),
        ("won't notice", 0.60),
        ("technically", 0.44),
        ("slip through", 0.56),
    ],
}


def lexical_seed_scores(text: str) -> dict[Disposition, float]:
    lower = text.lower()
    scores = {disposition: 0.0 for disposition in Disposition}
    for disposition, seeds in LEXICAL_SEEDS.items():
        for term, weight in seeds:
            if term in lower:
                scores[disposition] += weight
    return {disposition: min(1.0, score) for disposition, score in scores.items()}


def lexical_entropy(text: str) -> float:
    lower = text.lower()
    uncertainty_hits = sum(1 for term, _ in LEXICAL_SEEDS[Disposition.UNCERTAIN] if term in lower)
    confidence_hits = sum(1 for term, _ in LEXICAL_SEEDS[Disposition.CONFIDENT] if term in lower)
    if uncertainty_hits > 0:
        return min(1.0, 0.62 + uncertainty_hits * 0.08)
    if confidence_hits > 0:
        return 0.18
    if "?" in lower:
        return 0.48
    return 0.35


def top_lexical_tokens(text: str) -> list[DispositionToken]:
    lower = text.lower()
    tokens: list[DispositionToken] = []
    for seeds in LEXICAL_SEEDS.values():
        for term, weight in seeds:
            if term in lower:
                tokens.append(DispositionToken(token=term, weight=weight))
    return sorted(tokens, key=lambda token: token.weight, reverse=True)[:6]


def lexical_readout(text: str, latest_chunk: str = "") -> DispositionReadout:
    combined = f"{text} {latest_chunk}".lower()
    scores = lexical_seed_scores(combined)
    entropy = lexical_entropy(combined)
    return DispositionReadout(
        disposition=resolve(scores, entropy),
        entropy=entropy,
        seed_scores=scores,
        tokens=top_lexical_tokens(combined),
        source="lexicalFallback",
    )

