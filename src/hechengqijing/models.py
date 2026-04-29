from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class GameState(str, Enum):
    INIT = "INIT"
    PLAYING = "PLAYING"
    PRESSURE_BUILDING = "PRESSURE_BUILDING"
    NEAR_FAIL = "NEAR_FAIL"
    DECISION = "DECISION"
    RESULT = "RESULT"
    NEXT_LEVEL = "NEXT_LEVEL"


class CellType(str, Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    LOCKED = "locked"


@dataclass
class Item:
    level: int
    item_type: str = "seed"
    movable: bool = True


@dataclass
class Cell:
    x: int
    y: int
    cell_type: CellType = CellType.NORMAL
    item: Optional[Item] = None

    @property
    def is_empty(self) -> bool:
        return self.item is None and self.cell_type == CellType.NORMAL


@dataclass
class Board:
    width: int = 6
    height: int = 6
    cells: List[List[Cell]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.cells:
            self.cells = [[Cell(x, y) for y in range(self.height)] for x in range(self.width)]

    def get(self, x: int, y: int) -> Cell:
        return self.cells[x][y]

    def neighbors(self, x: int, y: int) -> List[Cell]:
        res: List[Cell] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    res.append(self.get(nx, ny))
        return res

    def empty_cells(self) -> List[Cell]:
        return [self.get(x, y) for x in range(self.width) for y in range(self.height) if self.get(x, y).is_empty]


@dataclass
class PlayerData:
    player_id: str
    level_index: int = 1
    coins: int = 300
    ads_today: int = 0
    ads_this_session: int = 0
    ad_conversion_rate: float = 0.3
    success_rate_10: float = 0.5
    consecutive_losses: int = 0
    is_new_user: bool = True
    last_ad_time: int = 0


@dataclass
class LevelConfig:
    level_id: str
    difficulty: int
    max_moves: int
    target_level: int = 5
    ad_opportunity: float = 0.3
    board: Board = field(default_factory=Board)
    fail_trigger_zone: Tuple[int, int] = (15, 18)
    rescue_item: Item = field(default_factory=lambda: Item(level=3, item_type="key_item"))


@dataclass
class AdContext:
    game_state: GameState
    space_usage: float
    moves_left: int
    success_probability: float
    has_been_stuck_for: int
    is_forced_to_watch: bool = False
    just_failed: bool = False
    time_since_fail: int = 999
    ads_in_last_minute: int = 0
    is_blocking_gameplay: bool = False
