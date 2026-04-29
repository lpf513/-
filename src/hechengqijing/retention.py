from __future__ import annotations

from dataclasses import dataclass

from .models import PlayerData


@dataclass
class StressResult:
    level: str
    action: str


class RetentionGuard:
    def monitor(self, player: PlayerData, fails_last5: int, ads_last_hour: int, coin_demand: int) -> StressResult:
        stress = 0.0
        stress += min(1.0, fails_last5 / 5) * 0.4
        stress += min(1.0, ads_last_hour / 8) * 0.3
        stress += 0.3 if player.coins < coin_demand * 0.3 else 0

        if stress > 0.8:
            return StressResult("HIGH", "INSERT_CHILL_LEVEL")
        if stress > 0.6:
            return StressResult("MEDIUM", "REDUCE_DIFFICULTY")
        return StressResult("LOW", "NO_CHANGE")
