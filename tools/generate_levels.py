from __future__ import annotations

import json
from pathlib import Path

out = Path('levels')
out.mkdir(exist_ok=True)

for i in range(1, 31):
    x = (i - 1) % 5
    y = ((i - 1) // 5) % 5
    level = {
        "metadata": {"levelId": f"L{i:03d}", "version": 1, "type": "starter", "difficulty": min(100, 5 + i)},
        "winCondition": {"targetItem": {"level": 2, "type": "tree"}, "quantity": 1, "mustExistOnBoard": True},
        "failCondition": {"maxMoves": 10 + i // 3, "minEmptyCells": 0},
        "boardRules": {
            "size": [6, 6],
            "initialItems": [
                {"x": x, "y": y, "level": 1, "type": "seed"},
                {"x": x, "y": y + 1, "level": 1, "type": "seed"},
            ],
            "blockedCells": [],
            "lockedCells": [],
            "specialCells": [],
        },
        "itemRules": {"allowedLevels": [1, 2, 3, 4, 5], "spawnableLevels": [1], "mergeRules": [{"fromLevel": 1, "toLevel": 2}]},
        "adRules": {"failTriggerZone": [1, 2], "rescueItem": {"level": 1, "type": "seed"}, "doubleRewardEnabled": True},
    }
    (out / f"level_{i:03d}.json").write_text(json.dumps(level, ensure_ascii=False, indent=2))

print('generated', 30)
