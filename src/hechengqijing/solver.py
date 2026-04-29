from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

Grid = Tuple[Tuple[int, ...], ...]
Move = Tuple[Tuple[int, int], Tuple[int, int]]
Pos = Tuple[int, int]


@dataclass
class SolveResult:
    solvable: bool
    solutions: List[List[Move]]
    visited_states: int = 0


class BFSSolver:
    """Offline solver for level validation.

    Supported constraints:
    - blocked / locked / max_moves
    - double cell (+2 merge)
    - spawn fixed level and probabilistic spawn rules
    """

    def __init__(
        self,
        board: Grid,
        target_level: int = 5,
        blocked: Set[Pos] | None = None,
        locked: Set[Pos] | None = None,
        max_moves: int = 20,
        double_cells: Set[Pos] | None = None,
        spawn_cells: Dict[Pos, int] | None = None,
        spawn_rules: Dict[Pos, List[Tuple[int, float]]] | None = None,
    ) -> None:
        self.board = board
        self.target_level = target_level
        self.blocked = blocked or set()
        self.locked = locked or set()
        self.max_moves = max_moves
        self.double_cells = double_cells or set()
        self.spawn_cells = spawn_cells or {}
        self.spawn_rules = spawn_rules or {}

    def find_solutions(self, max_depth: int = 12, max_solutions: int = 2, max_states: int = 10000) -> SolveResult:
        depth_limit = min(max_depth, self.max_moves)
        q = deque([(self.board, [])])
        seen = {self.board}
        solutions: List[List[Move]] = []

        while q and len(seen) <= max_states and len(solutions) < max_solutions:
            state, path = q.popleft()
            if self._has_target(state):
                solutions.append(path)
                continue
            if len(path) >= depth_limit:
                continue

            for move, nxt in self._next_states(state):
                if nxt in seen:
                    continue
                seen.add(nxt)
                q.append((nxt, path + [move]))

        return SolveResult(solvable=len(solutions) > 0, solutions=solutions, visited_states=len(seen))

    def _has_target(self, state: Grid) -> bool:
        return any(cell >= self.target_level for row in state for cell in row)

    def _next_states(self, state: Grid) -> List[Tuple[Move, Grid]]:
        out: List[Tuple[Move, Grid]] = []
        for x in range(6):
            for y in range(6):
                if (x, y) in self.blocked or (x, y) in self.locked:
                    continue
                if state[x][y] <= 0:
                    continue
                for nx, ny in self._neighbors(x, y):
                    if (nx, ny) in self.blocked:
                        continue
                    if state[nx][ny] == state[x][y] and state[x][y] > 0 and (x, y) < (nx, ny):
                        base = [list(r) for r in state]
                        base[x][y] = 0
                        delta = 2 if (nx, ny) in self.double_cells else 1
                        base[nx][ny] = state[nx][ny] + delta

                        spawn_variants = self._spawn_variants((x, y))
                        for spawn_level in spawn_variants:
                            new = [row[:] for row in base]
                            if spawn_level > 0:
                                new[x][y] = spawn_level
                            out.append((((x, y), (nx, ny)), tuple(tuple(r) for r in new)))
        return out

    def _spawn_variants(self, source: Pos) -> List[int]:
        if source in self.spawn_cells:
            return [self.spawn_cells[source]]
        if source in self.spawn_rules:
            levels = sorted(self.spawn_rules[source], key=lambda x: x[1], reverse=True)
            return [lv for lv, _ in levels]
        return [0]

    @staticmethod
    def _neighbors(x: int, y: int) -> List[Tuple[int, int]]:
        res = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < 6 and 0 <= ny < 6:
                    res.append((nx, ny))
        return res


def dsl_to_grid(level: Dict) -> Grid:
    grid = [[0 for _ in range(6)] for _ in range(6)]
    for item in level.get("boardRules", {}).get("initialItems", []):
        x, y, lv = item.get("x", 0), item.get("y", 0), item.get("level", 0)
        if 0 <= x < 6 and 0 <= y < 6:
            grid[x][y] = lv
    return tuple(tuple(r) for r in grid)


def dsl_constraints(level: Dict) -> Tuple[Set[Pos], Set[Pos], int, Set[Pos], Dict[Pos, int], Dict[Pos, List[Tuple[int, float]]]]:
    board_rules = level.get("boardRules", {})
    blocked = {(c["x"], c["y"]) for c in board_rules.get("blockedCells", []) if "x" in c and "y" in c}
    locked = {(c["x"], c["y"]) for c in board_rules.get("lockedCells", []) if "x" in c and "y" in c}
    doubles = {
        (c["x"], c["y"])
        for c in board_rules.get("specialCells", [])
        if c.get("type") == "double" and "x" in c and "y" in c
    }
    spawns = {
        (c["x"], c["y"]): int(c.get("spawnLevel", 1))
        for c in board_rules.get("specialCells", [])
        if c.get("type") == "spawn" and "x" in c and "y" in c and "spawnTable" not in c
    }
    spawn_rules = {
        (c["x"], c["y"]): [(int(v["level"]), float(v["prob"])) for v in c.get("spawnTable", [])]
        for c in board_rules.get("specialCells", [])
        if c.get("type") == "spawn" and "x" in c and "y" in c and "spawnTable" in c
    }
    max_moves = int(level.get("failCondition", {}).get("maxMoves", 20))
    return blocked, locked, max_moves, doubles, spawns, spawn_rules
