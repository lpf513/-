from __future__ import annotations

from dataclasses import dataclass

from .models import PlayerData


@dataclass
class EconomyAction:
    action: str
    value: float


class CoinEntropySystem:
    DAILY_CAP_TOTAL = 1000

    def balance(self, player: PlayerData, demand: int) -> EconomyAction:
        gap = demand - player.coins
        target_gap = demand * 0.6
        if gap > target_gap * 1.5:
            return EconomyAction("INCREASE_REWARD", 1.2)
        if gap < target_gap * 0.5:
            return EconomyAction("REDUCE_REWARD", 0.8)
        return EconomyAction("NO_CHANGE", 1.0)

    def rescue_cost(self, player: PlayerData) -> int:
        return int(max(50, min(player.coins * 0.5, 400)))
