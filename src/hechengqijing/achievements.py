from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AchievementState:
    total_wins: int = 0
    best_chain: int = 0
    unlocked: set[str] = field(default_factory=set)


class AchievementSystem:
    def __init__(self) -> None:
        self.state = AchievementState()

    def on_win(self) -> None:
        self.state.total_wins += 1
        if self.state.total_wins >= 1:
            self.state.unlocked.add("FIRST_WIN")
        if self.state.total_wins >= 10:
            self.state.unlocked.add("WIN_10")

    def on_chain(self, chain_count: int) -> None:
        self.state.best_chain = max(self.state.best_chain, chain_count)
        if chain_count >= 3:
            self.state.unlocked.add("CHAIN_3")
        if chain_count >= 5:
            self.state.unlocked.add("CHAIN_5")
