from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DifficultyAdjustment:
    difficulty_delta: int
    reason: str


class DifficultyManager:
    TARGET_SUCCESS_RATE = 0.5

    def adjust(self, player_success_rate: float, player_ad_conversion: float) -> DifficultyAdjustment:
        error = player_success_rate - self.TARGET_SUCCESS_RATE
        delta = 0
        if error > 0.2:
            delta = 10
        elif error > 0.1:
            delta = 5
        elif error < -0.2:
            delta = -10
        elif error < -0.1:
            delta = -5

        if player_ad_conversion < 0.2:
            delta -= 3
        elif player_ad_conversion > 0.4:
            delta += 2

        delta = max(-15, min(15, delta))
        return DifficultyAdjustment(delta, self._reason(error, player_ad_conversion))

    @staticmethod
    def _reason(error: float, conversion: float) -> str:
        if error > 0.1:
            return "玩家成功率偏高，增加难度"
        if error < -0.1:
            return "玩家成功率偏低，降低难度"
        if conversion < 0.2:
            return "广告转化偏低，适度降压"
        return "保持稳定"
