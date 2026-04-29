from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum

from .models import AdContext, GameState, PlayerData


class AdState(str, Enum):
    NO_AD = "NO_AD"
    ELIGIBLE = "ELIGIBLE"
    TRIGGERED = "TRIGGERED"
    VIEWING = "VIEWING"
    COMPLETED = "COMPLETED"
    REWARDED = "REWARDED"


AD_PRIORITY = {
    "rescue": 100,
    "double_reward": 80,
    "interstitial": 60,
}


@dataclass
class AdTriggerSystem:
    state: AdState = AdState.NO_AD
    triggers: dict[str, bool] = field(default_factory=lambda: {
        "rescue": False,
        "double_reward": False,
        "interstitial": False,
    })

    def clear(self) -> None:
        for key in self.triggers:
            self.triggers[key] = False
        self.state = AdState.NO_AD

    def get_next_ad(self) -> str | None:
        active = [k for k, v in self.triggers.items() if v]
        if not active:
            return None
        return sorted(active, key=lambda t: AD_PRIORITY[t], reverse=True)[0]


class WeChatAdPolicy:
    REWARDED_MAX_PER_DAY = 20
    INTERSTITIAL_MAX_PER_HOUR = 4
    MIN_COOLDOWN_SECONDS = 60

    def can_show_rewarded(self, player: PlayerData, context: AdContext) -> bool:
        if player.ads_today >= self.REWARDED_MAX_PER_DAY:
            return False
        if int(time.time()) - player.last_ad_time < self.MIN_COOLDOWN_SECONDS:
            return False
        if player.is_new_user and player.level_index <= 5:
            return False
        if player.ads_this_session >= 8:
            return False
        if self.is_dark_pattern(context):
            return False
        return True

    @staticmethod
    def is_dark_pattern(context: AdContext) -> bool:
        return any([
            context.is_forced_to_watch,
            context.just_failed and context.time_since_fail < 3,
            context.ads_in_last_minute >= 2,
            context.is_blocking_gameplay,
        ])


class OpportunityAdSystem:
    def __init__(self) -> None:
        self.policy = WeChatAdPolicy()
        self.trigger_system = AdTriggerSystem()

    def should_show_opportunity_ad(self, player: PlayerData, context: AdContext) -> bool:
        self.trigger_system.clear()
        if context.game_state != GameState.NEAR_FAIL:
            return False
        if not self._has_perceived_difficulty(context):
            return False
        if context.success_probability <= 0:
            return False
        if not self.policy.can_show_rewarded(player, context):
            return False

        base_chance = 0.6
        tolerance = max(0.4, 1 - player.ads_today / 30)
        final = base_chance * tolerance
        yes = random.random() < final
        if yes:
            self.trigger_system.triggers["rescue"] = True
            self.trigger_system.state = AdState.ELIGIBLE
        return yes

    def on_level_success(self, player: PlayerData) -> None:
        if player.ads_today < self.policy.REWARDED_MAX_PER_DAY:
            self.trigger_system.triggers["double_reward"] = True
            self.trigger_system.state = AdState.ELIGIBLE

    @staticmethod
    def _has_perceived_difficulty(context: AdContext) -> bool:
        checks = [
            context.space_usage > 0.7,
            context.moves_left < 5,
            context.success_probability < 0.4,
            context.has_been_stuck_for > 10,
        ]
        return len([x for x in checks if x]) >= 2
