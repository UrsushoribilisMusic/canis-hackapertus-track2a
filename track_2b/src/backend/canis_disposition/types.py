"""Shared disposition types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Disposition(str, Enum):
    IDLE = "idle"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    CURIOUS = "curious"
    CONCERN = "concern"
    RELUCTANT = "reluctant"
    WARM = "warm"
    MISCHIEF = "mischief"

    @property
    def is_safety_override(self) -> bool:
        return self in {Disposition.CONCERN, Disposition.RELUCTANT, Disposition.MISCHIEF}

    @property
    def web_value(self) -> str:
        return {
            Disposition.IDLE: "neutral",
            Disposition.UNCERTAIN: "unsure",
            Disposition.CONCERN: "concerned",
            Disposition.MISCHIEF: "concerned",
        }.get(self, self.value)


@dataclass(frozen=True)
class DispositionToken:
    token: str
    weight: float

    def to_web(self) -> dict:
        return {"token": self.token, "weight": round(float(self.weight), 3)}


@dataclass(frozen=True)
class DispositionReadout:
    disposition: Disposition
    entropy: float
    seed_scores: dict[Disposition, float] = field(default_factory=dict)
    tokens: list[DispositionToken] = field(default_factory=list)
    source: str = "lexicalFallback"

    @property
    def certainty(self) -> float:
        return max(0.0, min(1.0, 1.0 - self.entropy))

    def to_web(self) -> dict:
        web_scores: dict[str, float] = {}
        for disposition, score in self.seed_scores.items():
            if disposition is Disposition.IDLE:
                continue
            web_value = disposition.web_value
            web_scores[web_value] = web_scores.get(web_value, 0.0) + float(score)
        return {
            "disposition": self.disposition.web_value,
            "certainty": round(self.certainty, 3),
            "scores": {key: round(min(1.0, value), 3) for key, value in web_scores.items()},
            "tokens": [token.to_web() for token in self.tokens[:6]],
            "source": self.source,
        }
