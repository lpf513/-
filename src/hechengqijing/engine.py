from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .achievements import AchievementSystem
from .ad_system import OpportunityAdSystem
from .adsdk import RewardedAdAdapter
from .analytics import EventTracker
from .config import RemoteConfig
from .difficulty import DifficultyManager
from .economy import CoinEntropySystem
from .level_generator import TemplateDrivenGenerator
from .merge import MergeEngine, MergeResult
from .models import AdContext, GameState, LevelConfig, PlayerData
from .replay import ReplayRecorder
from .retention import RetentionGuard
from .tutorial import TutorialGuide


class Decision(str, Enum):
    WATCH_AD = "watch_ad"
    SPEND_COINS = "spend_coins"
    HARD_TRY = "hard_try"


@dataclass
class TickResult:
    state: GameState
    ad_offer: bool = False


@dataclass
class DecisionResult:
    success: bool
    message: str


class GameEngine:
    def __init__(self, player: PlayerData, remote_config: RemoteConfig | None = None) -> None:
        self.player = player
        self.state = GameState.INIT
        self.config = remote_config or RemoteConfig()
        self.generator = TemplateDrivenGenerator()
        self.merge_engine = MergeEngine()
        self.ad_system = OpportunityAdSystem()
        self.economy = CoinEntropySystem()
        self.retention = RetentionGuard()
        self.difficulty = DifficultyManager()
        self.tracker = EventTracker()
        self.ad_adapter = RewardedAdAdapter()
        self.tutorial = TutorialGuide()
        self.achievements = AchievementSystem()
        self.replay = ReplayRecorder()
        self.level: LevelConfig | None = None
        self.moves_used = 0

    def load_level(self) -> LevelConfig:
        self.level = self.generator.generate_level(self.player.level_index, self.player)
        self.state = GameState.PLAYING
        self.moves_used = 0
        self.tracker.track("level_start", level_id=self.level.level_id, player_level=self.player.level_index)
        self.replay.record("level_start", level_id=self.level.level_id)
        return self.level

    def execute_merge(self, a: tuple[int, int], b: tuple[int, int]) -> MergeResult:
        if not self.level:
            raise ValueError("level not loaded")
        self.moves_used += 1
        result = self.merge_engine.execute_merge(self.level.board, a, b)
        self.replay.record("merge", from_pos=a, to_pos=b, success=result.success)
        if result.chain_count > 0:
            self.tracker.track("chain_reaction", chain_count=result.chain_count)
            self.achievements.on_chain(result.chain_count)
            self.replay.record("chain", count=result.chain_count)

        if self.check_win_condition():
            self.state = GameState.RESULT
            self.on_level_success()
        elif self.check_fail_condition():
            self.state = GameState.NEAR_FAIL
            self.tracker.track("level_fail_step", level_id=self.level.level_id, fail_step=self.moves_used)

        return result

    def check_win_condition(self) -> bool:
        if not self.level:
            return False
        target = self.level.target_level
        board = self.level.board
        for x in range(board.width):
            for y in range(board.height):
                item = board.get(x, y).item
                if item and item.level >= target:
                    return True
        return False

    def check_fail_condition(self) -> bool:
        if not self.level:
            return False
        if self.moves_used >= self.level.max_moves:
            return True
        board = self.level.board
        if board.empty_cells():
            return False
        return self.find_hint_move() is None

    def find_hint_move(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        if not self.level:
            return None
        board = self.level.board
        for x in range(board.width):
            for y in range(board.height):
                for n in board.neighbors(x, y):
                    if self.merge_engine.can_merge(board, (x, y), (n.x, n.y)):
                        return (x, y), (n.x, n.y)
        return None

    def tick(self, space_usage: float, success_probability: float, stuck_seconds: int) -> TickResult:
        if not self.level:
            raise ValueError("level not loaded")
        moves_left = self.level.max_moves - self.moves_used
        if space_usage >= 0.7 or moves_left <= 8:
            self.state = GameState.PRESSURE_BUILDING
        if (space_usage >= 0.85 or moves_left <= 3) and self.state in (GameState.PLAYING, GameState.PRESSURE_BUILDING):
            self.state = GameState.NEAR_FAIL
            self.tracker.track("level_fail_step", level_id=self.level.level_id, fail_step=self.moves_used)

        context = AdContext(
            game_state=self.state,
            space_usage=space_usage,
            moves_left=moves_left,
            success_probability=success_probability,
            has_been_stuck_for=stuck_seconds,
        )
        ad_offer = self.ad_system.should_show_opportunity_ad(self.player, context)
        if ad_offer:
            self.tracker.track("rescue_ad_show", level_id=self.level.level_id, moves_left=moves_left)
        return TickResult(state=self.state, ad_offer=ad_offer)

    def apply_decision(self, decision: Decision) -> DecisionResult:
        if not self.level:
            raise ValueError("level not loaded")
        if self.state != GameState.NEAR_FAIL:
            return DecisionResult(False, "当前不在决策窗口")

        if decision == Decision.WATCH_AD:
            result = self.ad_adapter.show_with_retry("rescue", max_retries=1)
            if not result.completed:
                self.state = GameState.RESULT
                return DecisionResult(False, "广告失败，已进入失败结算")
            self.player.ads_today += 1
            self.player.ads_this_session += 1
            self.tracker.track("rescue_ad_convert", watched=True)
            self.state = GameState.PLAYING
            return DecisionResult(True, "广告救援成功，已发放关键物品")

        if decision == Decision.SPEND_COINS:
            cost = int(max(50, self.player.coins * self.config.economy_config.coin_rescue_cost_percent))
            if self.player.coins < cost:
                return DecisionResult(False, "金币不足，建议看广告")
            self.player.coins -= cost
            self.tracker.track("coin_balance", coins=self.player.coins, op="rescue_spend")
            self.state = GameState.PLAYING
            return DecisionResult(True, f"已花费{cost}金币救援")

        self.state = GameState.RESULT
        return DecisionResult(False, "硬撑失败，进入结算")

    def retention_action(self, fails_last5: int, ads_last_hour: int, coin_demand: int) -> str:
        stress = self.retention.monitor(self.player, fails_last5=fails_last5, ads_last_hour=ads_last_hour, coin_demand=coin_demand)
        self.tracker.track("retention_guard", level=stress.level, action=stress.action)
        return stress.action

    def tutorial_hint(self) -> str:
        return self.tutorial.current_hint()

    def tutorial_advance(self) -> None:
        self.tutorial.advance()

    def replay_summary(self) -> dict:
        return self.replay.summary()

    def on_level_success(self) -> None:
        self.ad_system.on_level_success(self.player)
        self.achievements.on_win()
        self.tracker.track("level_success", level_id=self.level.level_id if self.level else "unknown")

    def difficulty_recommendation(self) -> int:
        d = self.difficulty.adjust(self.player.success_rate_10, self.player.ad_conversion_rate)
        return d.difficulty_delta
