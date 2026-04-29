from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class ABVariant:
    experiment: str
    bucket: str


class ABTestSystem:
    """Deterministic bucketing by player_id + experiment name."""

    def assign(self, player_id: str, experiment: str, ratio_b: float = 0.5) -> ABVariant:
        seed = f"{player_id}:{experiment}".encode("utf-8")
        digest = hashlib.md5(seed).hexdigest()
        value = int(digest[:8], 16) / 0xFFFFFFFF
        bucket = "B" if value < ratio_b else "A"
        return ABVariant(experiment=experiment, bucket=bucket)
