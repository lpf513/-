from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .audio import AudioManager
from .engine import Decision, GameEngine
from .models import GameState, PlayerData


@dataclass
class UIState:
    selected: tuple[int, int] | None = None
    message: str = ""


class GameUIController:
    """UI wiring layer independent of concrete UI toolkit."""

    def __init__(self, engine: GameEngine, audio: Optional[AudioManager] = None) -> None:
        self.engine = engine
        self.audio = audio or AudioManager()
        self.ui = UIState()

    def start(self) -> None:
        self.engine.load_level()
        self.ui.message = self.engine.tutorial_hint()

    def on_cell_click(self, x: int, y: int) -> None:
        if self.ui.selected is None:
            self.ui.selected = (x, y)
            return
        a = self.ui.selected
        b = (x, y)
        self.ui.selected = None
        result = self.engine.execute_merge(a, b)
        if result.success:
            self.audio.play("merge")
            if result.chain_count > 0:
                self.audio.play("chain")
        if self.engine.state == GameState.RESULT:
            self.audio.play("win")
            self.ui.message = "通关成功"

    def on_hint(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        move = self.engine.find_hint_move()
        self.ui.message = "有可用提示" if move else "暂无可用提示"
        return move

    def on_watch_ad(self) -> str:
        self.engine.state = GameState.NEAR_FAIL
        r = self.engine.apply_decision(Decision.WATCH_AD)
        self.audio.play("button")
        self.ui.message = r.message
        return r.message

    def on_spend_coins(self) -> str:
        self.engine.state = GameState.NEAR_FAIL
        r = self.engine.apply_decision(Decision.SPEND_COINS)
        self.audio.play("button")
        self.ui.message = r.message
        return r.message


def create_default_controller() -> GameUIController:
    player = PlayerData(player_id="ui_player", is_new_user=False)
    engine = GameEngine(player)
    return GameUIController(engine)
