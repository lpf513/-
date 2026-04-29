import json
from pathlib import Path

from hechengqijing.audio import FREE_AUDIO_CUES
from hechengqijing.dsl import LevelDSLValidator
from hechengqijing.models import Item
from hechengqijing.ui import create_default_controller


def test_levels_pack_all_valid():
    validator = LevelDSLValidator()
    files = sorted(Path("levels").glob("level_*.json"))
    assert len(files) >= 30
    for f in files:
        level = json.loads(f.read_text())
        result = validator.validate(level)
        assert result.is_valid, f"{f.name}: {result.errors}"


def test_ui_controller_wiring():
    c = create_default_controller()
    c.start()
    assert "拖拽" in c.ui.message
    # prepare guaranteed merge
    lvl = c.engine.level
    assert lvl is not None
    lvl.board.get(0, 0).item = lvl.board.get(0, 0).item or Item(level=1)
    lvl.board.get(0, 1).item = lvl.board.get(0, 1).item or Item(level=1)
    c.on_cell_click(0, 0)
    c.on_cell_click(0, 1)
    assert "merge" in c.audio.play_log


def test_audio_resources_declared():
    required = {"merge", "chain", "win", "fail", "button"}
    assert required.issubset(set(FREE_AUDIO_CUES.keys()))
