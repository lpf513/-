#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from hechengqijing.dsl import LevelDSLValidator
from hechengqijing.solver import BFSSolver, dsl_constraints, dsl_to_grid


def scan(folder: Path) -> dict:
    validator = LevelDSLValidator()
    files = sorted(folder.glob("*.json"))
    total = len(files)
    valid = 0
    unique = 0
    fail_zone_pass = 0
    step_hist: dict[int, int] = {}

    for f in files:
        level = json.loads(f.read_text())
        result = validator.validate(level)
        if result.is_valid:
            valid += 1
            fail_zone_pass += 1

        grid = dsl_to_grid(level)
        blocked, locked, max_moves, doubles, spawns, spawn_rules = dsl_constraints(level)
        target = level["winCondition"]["targetItem"]["level"]
        solve = BFSSolver(
            grid,
            target_level=target,
            blocked=blocked,
            locked=locked,
            max_moves=max_moves,
            double_cells=doubles,
            spawn_cells=spawns,
            spawn_rules=spawn_rules,
        ).find_solutions(max_depth=max_moves, max_solutions=2)

        if solve.solvable and len(solve.solutions) == 1:
            unique += 1
            steps = len(solve.solutions[0])
            step_hist[steps] = step_hist.get(steps, 0) + 1

    return {
        "total": total,
        "valid": valid,
        "valid_rate": (valid / total if total else 0),
        "unique_solution": unique,
        "unique_rate": (unique / total if total else 0),
        "fail_zone_pass": fail_zone_pass,
        "progress": {
            "core_validation": f"{valid}/{total}",
            "unique_solution": f"{unique}/{total}",
        },
        "step_hist": step_hist,
    }


if __name__ == "__main__":
    base = Path("levels")
    report = scan(base)
    print(json.dumps(report, ensure_ascii=False, indent=2))
