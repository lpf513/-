from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AdConfig:
    interstitial_frequency: int = 3
    rescue_ad_trigger_step: int = 2
    double_reward_bonus: float = 2.0
    daily_ad_limit: int = 20


@dataclass
class EconomyConfig:
    coin_rescue_cost_percent: float = 0.5
    chain_bonus_base: int = 3
    daily_ad_coin_limit: int = 500


@dataclass
class DifficultyConfig:
    base_success_rate: float = 0.5
    newbie_protection_levels: int = 5
    max_fail_streak: int = 3


@dataclass
class RemoteConfig:
    ad_config: AdConfig = field(default_factory=AdConfig)
    economy_config: EconomyConfig = field(default_factory=EconomyConfig)
    difficulty_config: DifficultyConfig = field(default_factory=DifficultyConfig)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RemoteConfig":
        ad = AdConfig(**payload.get("ad_config", {}))
        economy = EconomyConfig(**payload.get("economy_config", {}))
        difficulty = DifficultyConfig(**payload.get("difficulty_config", {}))
        return cls(ad_config=ad, economy_config=economy, difficulty_config=difficulty)
