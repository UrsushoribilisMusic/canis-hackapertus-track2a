"""Entropy helpers for real model logits."""

from __future__ import annotations

import math
from collections.abc import Sequence


def normalized_entropy(logits: Sequence[float]) -> float:
    values = list(float(value) for value in logits)
    if len(values) <= 1:
        return 0.0
    max_logit = max(values)
    exp_values = [math.exp(value - max_logit) for value in values]
    sum_exp = sum(exp_values)
    if sum_exp <= 0:
        return 0.0
    entropy = 0.0
    for exp_value in exp_values:
        if exp_value > 0:
            probability = exp_value / sum_exp
            entropy -= probability * math.log(probability)
    return max(0.0, min(1.0, entropy / math.log(len(values))))

