from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .solver import BFSSolver, dsl_constraints, dsl_to_grid


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)


class LevelDSLValidator:
    REQUIRED_KEYS = {"metadata", "winCondition", "failCondition", "boardRules", "itemRules", "adRules"}

    def validate(self, level: Dict) -> ValidationResult:
        errors: List[str] = []
        missing = self.REQUIRED_KEYS - set(level.keys())
        if missing:
            errors.append(f"缺少字段: {sorted(missing)}")
            return ValidationResult(False, errors)

        meta = level["metadata"]
        if not meta.get("levelId"):
            errors.append("缺少levelId")

        target_level = level["winCondition"]["targetItem"].get("level", 0)
        if target_level < 1 or target_level > 5:
            errors.append("目标等级必须在1-5之间")

        allowed_levels = level.get("itemRules", {}).get("allowedLevels", [1, 2, 3, 4, 5])
        if target_level not in allowed_levels:
            errors.append("目标等级不在可用等级集合中")

        size = tuple(level["boardRules"].get("size", []))
        if size != (6, 6):
            errors.append("棋盘必须是6×6")

        zone = tuple(level["adRules"].get("failTriggerZone", []))
        if len(zone) != 2 or zone[0] >= zone[1]:
            errors.append("失败触发区间无效")

        if not self._has_seed_items(level):
            errors.append("至少需要2个可合成初始物品")

        for c in level["boardRules"].get("specialCells", []):
            if not (0 <= c.get("x", -1) < 6 and 0 <= c.get("y", -1) < 6):
                errors.append("specialCells 坐标越界")
                break
            if c.get("type") == "spawn" and "spawnTable" in c:
                p_sum = sum(float(v.get("prob", 0)) for v in c.get("spawnTable", []))
                if abs(p_sum - 1.0) > 1e-6:
                    errors.append("spawnTable 概率和必须为1")

        if not errors:
            grid = dsl_to_grid(level)
            blocked, locked, max_moves, doubles, spawns, spawn_rules = dsl_constraints(level)
            solver = BFSSolver(
                grid,
                target_level=target_level,
                blocked=blocked,
                locked=locked,
                max_moves=max_moves,
                double_cells=doubles,
                spawn_cells=spawns,
                spawn_rules=spawn_rules,
            )
            solved = solver.find_solutions(max_depth=max_moves, max_solutions=2, max_states=15000)
            if not solved.solvable:
                errors.append("关卡不可解")
            elif len(solved.solutions) > 1:
                errors.append("关卡存在多个解（非唯一解）")
            else:
                optimal_steps = len(solved.solutions[0])
                if not (zone[0] <= optimal_steps <= zone[1]):
                    errors.append("最优解步数不在广告触发区间")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    @staticmethod
    def _has_seed_items(level: Dict) -> bool:
        items = level["boardRules"].get("initialItems", [])
        lv1_count = sum(1 for x in items if x.get("level") == 1)
        return lv1_count >= 2
