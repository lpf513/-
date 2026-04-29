import json
from pathlib import Path

from scripts.scan_levels import scan


def test_scan_levels(tmp_path: Path):
    level = {
        "metadata": {"levelId": "L1"},
        "winCondition": {"targetItem": {"level": 2, "type": "tree"}},
        "failCondition": {"maxMoves": 10, "minEmptyCells": 0},
        "boardRules": {
            "size": [6, 6],
            "initialItems": [{"x": 0, "y": 0, "level": 1}, {"x": 0, "y": 1, "level": 1}],
            "blockedCells": [],
            "lockedCells": [],
            "specialCells": [],
        },
        "itemRules": {"allowedLevels": [1, 2, 3, 4, 5]},
        "adRules": {"failTriggerZone": [1, 2]},
    }
    (tmp_path / "a.json").write_text(json.dumps(level))
    report = scan(tmp_path)
    assert report["total"] == 1
    assert report["valid"] == 1
    assert report["progress"]["core_validation"] == "1/1"
