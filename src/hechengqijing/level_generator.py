from __future__ import annotations

import random
from dataclasses import dataclass

from .models import Board, CellType, Item, LevelConfig, PlayerData


@dataclass
class Template:
    name: str
    difficulty: int
    max_moves: int
    ad_opportunity: float


class TemplateDrivenGenerator:
    TEMPLATES = [
        Template("TEMPLATE_A", 10, 15, 0.3),
        Template("TEMPLATE_B", 30, 20, 0.5),
        Template("TEMPLATE_C", 50, 25, 0.7),
    ]

    def select_template(self, level_index: int) -> Template:
        if level_index <= 10:
            return self.TEMPLATES[0]
        if level_index <= 30:
            return self.TEMPLATES[1]
        return self.TEMPLATES[2]

    def generate_level(self, level_index: int, player: PlayerData) -> LevelConfig:
        t = self.select_template(level_index)
        board = Board(6, 6)
        fill_rate = 0.3 + min(t.difficulty / 200, 0.3)
        items = int((board.width * board.height) * fill_rate)
        for _ in range(items):
            empties = board.empty_cells()
            if not empties:
                break
            c = random.choice(empties)
            lv = 1 if random.random() < 0.7 else 2
            c.item = Item(level=lv, item_type="seed")

        # light perturbation
        if random.random() < 0.2:
            random.choice(board.empty_cells()).cell_type = CellType.BLOCKED

        ad_opp = min(0.8, max(0.1, t.ad_opportunity + (0.3 - player.ad_conversion_rate) * 0.2))
        return LevelConfig(
            level_id=f"L{level_index:04d}",
            difficulty=t.difficulty,
            max_moves=t.max_moves,
            ad_opportunity=ad_opp,
            board=board,
        )
