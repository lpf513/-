from pathlib import Path

from hechengqijing import assess_project
from hechengqijing.abtest import ABTestSystem
from hechengqijing.adsdk import AdLifecycle, PlatformError, RewardVerifier, RewardedAdAdapter
from hechengqijing.config import RemoteConfig
from hechengqijing.dsl import LevelDSLValidator
from hechengqijing.engine import Decision, GameEngine
from hechengqijing.models import GameState, Item, PlayerData
from hechengqijing.monitoring import MetricsStore, TimeSeriesExporter, evaluate_alerts
from hechengqijing.solver import BFSSolver


def test_level_load_and_state():
    e = GameEngine(PlayerData(player_id="p1", is_new_user=False))
    lvl = e.load_level()
    assert lvl.level_id.startswith("L")
    assert e.state == GameState.PLAYING


def test_merge_success_and_replay():
    e = GameEngine(PlayerData(player_id="p2", is_new_user=False))
    lvl = e.load_level()
    lvl.board.get(0, 0).item = Item(level=1)
    lvl.board.get(0, 1).item = Item(level=1)
    result = e.execute_merge((0, 0), (0, 1))
    assert result.success
    summary = e.replay_summary()
    assert summary["merges"] >= 1


def test_tutorial_flow():
    e = GameEngine(PlayerData(player_id="p2b", is_new_user=False))
    assert "拖拽" in e.tutorial_hint()
    e.tutorial_advance()
    assert e.tutorial.current_hint() != "教程已完成"


def test_win_condition_and_achievement():
    e = GameEngine(PlayerData(player_id="p2c", is_new_user=False))
    lvl = e.load_level()
    lvl.board.get(0, 0).item = Item(level=5)
    assert e.check_win_condition()
    e.on_level_success()
    assert "FIRST_WIN" in e.achievements.state.unlocked


def test_near_fail_and_decision_flow_watch_ad():
    p = PlayerData(player_id="p3", is_new_user=False, ads_today=0, ads_this_session=0, last_ad_time=0, coins=500)
    e = GameEngine(p)
    e.load_level()
    t = e.tick(space_usage=0.9, success_probability=0.3, stuck_seconds=20)
    assert t.state == GameState.NEAR_FAIL
    r = e.apply_decision(Decision.WATCH_AD)
    assert r.success is True


def test_remote_config_override():
    cfg = RemoteConfig.from_dict({"economy_config": {"coin_rescue_cost_percent": 0.3}})
    p = PlayerData(player_id="p4", is_new_user=False, coins=200)
    e = GameEngine(p, remote_config=cfg)
    e.load_level()
    e.state = GameState.NEAR_FAIL
    r = e.apply_decision(Decision.SPEND_COINS)
    assert r.success


def test_ab_bucket_stable():
    ab = ABTestSystem()
    assert ab.assign("u1", "exp").bucket == ab.assign("u1", "exp").bucket


def test_dsl_validator_and_solver_unique_solution():
    validator = LevelDSLValidator()
    level = {
        "metadata": {"levelId": "level_001", "version": 1},
        "winCondition": {"targetItem": {"level": 2, "type": "tree"}},
        "failCondition": {"maxMoves": 20, "minEmptyCells": 0},
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
    assert validator.validate(level).is_valid


def test_solver_supports_double_and_prob_spawn():
    grid = ((1, 1, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0))
    solve = BFSSolver(grid, target_level=3, double_cells={(0, 1)}, spawn_rules={(0, 0): [(1, 0.7), (2, 0.3)]}).find_solutions(max_depth=2)
    assert solve.solvable


def test_metrics_store_export_and_alerts(tmp_path: Path):
    e = GameEngine(PlayerData(player_id="p6", is_new_user=False))
    e.load_level()
    e.tracker.track("level_fail_step", level_id="x", fail_step=3)
    e.tracker.track("rescue_ad_show", level_id="x", moves_left=2)
    e.tracker.track("rescue_ad_convert", watched=True)
    store = MetricsStore(str(tmp_path / "metrics.db"))
    store.init_schema()
    store.ingest(e.tracker)
    exporter = TimeSeriesExporter(endpoint="http://localhost:9999/metrics")
    health = store.export_health(exporter, dry_run=True)
    assert health["events"] >= 1
    assert "广告转化率过低" in evaluate_alerts(ad_conversion_rate=0.1, near_fail_rate=0.2)


def test_adsdk_lifecycle_callbacks_retry_and_error_mapping():
    events = []
    ad = RewardedAdAdapter(on_event=lambda evt: events.append(evt.lifecycle), verifier=RewardVerifier("secret"))
    result = ad.show_with_retry("rescue", max_retries=1)
    assert result.reward_granted
    assert AdLifecycle.ERROR in events
    assert ad.map_platform_error(2) == PlatformError.NO_FILL


def test_retention_action_and_assessment():
    e = GameEngine(PlayerData(player_id="p7", is_new_user=False))
    e.load_level()
    action = e.retention_action(fails_last5=4, ads_last_hour=7, coin_demand=1000)
    assert action in {"INSERT_CHILL_LEVEL", "REDUCE_DIFFICULTY", "NO_CHANGE"}
    assert assess_project().completeness >= 80
