from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .models import Board, Item


@dataclass
class MergeResult:
    success: bool
    chain_count: int = 0
    new_item: Optional[Item] = None


class MergeEngine:
    def can_merge(self, board: Board, a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        ax, ay = a
        bx, by = b
        ca = board.get(ax, ay)
        cb = board.get(bx, by)
        if not ca.item or not cb.item:
            return False
        if not ca.item.movable or not cb.item.movable:
            return False
        if ca.item.level != cb.item.level:
            return False
        if max(abs(ax - bx), abs(ay - by)) > 1:
            return False
        return True

    def execute_merge(self, board: Board, a: Tuple[int, int], b: Tuple[int, int]) -> MergeResult:
        if not self.can_merge(board, a, b):
            return MergeResult(success=False)
        ax, ay = a
        bx, by = b
        item_a = board.get(ax, ay).item
        assert item_a
        board.get(ax, ay).item = None
        board.get(bx, by).item = None
        new_item = Item(level=item_a.level + 1, item_type="tree")
        board.get(bx, by).item = new_item
        chain = self._chain(board, (bx, by), 0)
        return MergeResult(success=True, chain_count=chain, new_item=board.get(bx, by).item)

    def _chain(self, board: Board, pos: Tuple[int, int], count: int) -> int:
        if count >= 5:
            return count
        x, y = pos
        cell = board.get(x, y)
        if not cell.item:
            return count
        for n in board.neighbors(x, y):
            if n.item and n.item.level == cell.item.level and n.item.movable:
                n.item = None
                cell.item = Item(level=cell.item.level + 1, item_type="tree")
                return self._chain(board, pos, count + 1)
        return count
