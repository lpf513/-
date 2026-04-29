from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TutorialState:
    step: int = 0
    completed: bool = False


class TutorialGuide:
    STEPS = [
        "拖拽一个物品到相邻格子",
        "合成两个同级物品",
        "使用一次提示按钮",
    ]

    def __init__(self) -> None:
        self.state = TutorialState()

    def current_hint(self) -> str:
        if self.state.completed:
            return "教程已完成"
        return self.STEPS[self.state.step]

    def advance(self) -> None:
        if self.state.completed:
            return
        self.state.step += 1
        if self.state.step >= len(self.STEPS):
            self.state.completed = True
