# 部署及配置文档（合成奇境）

## 1. 环境要求
- Python 3.10+
- Linux/macOS/Windows 均可
- 推荐：`venv` 或 `conda`

## 2. 本地安装
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e .
```

## 3. 运行测试
```bash
python -m pytest -q
```

## 4. 配置说明
项目配置入口：`RemoteConfig`（`src/hechengqijing/config.py`）。

### 4.1 广告配置
- `interstitial_frequency`: 每 N 关插屏（默认 3）
- `rescue_ad_trigger_step`: 倒数几步触发救援（默认 2）
- `double_reward_bonus`: 双倍奖励倍率（默认 2.0）
- `daily_ad_limit`: 每日广告上限（默认 20）

### 4.2 经济配置
- `coin_rescue_cost_percent`: 金币救援成本比例（默认 0.5）
- `chain_bonus_base`: 连锁奖励基数（默认 3）
- `daily_ad_coin_limit`: 每日广告金币上限（默认 500）

### 4.3 难度配置
- `base_success_rate`: 基础成功率目标（默认 0.5）
- `newbie_protection_levels`: 新手保护关数（默认 5）
- `max_fail_streak`: 最大连败阈值（默认 3）

## 5. 广告SDK接入说明
SDK抽象层：`src/hechengqijing/adsdk.py`
- `RewardedAdAdapter.show()`：展示一次广告
- `show_with_retry()`：失败自动重试
- `map_platform_error()`：平台错误码映射
- `RewardVerifier`：HMAC签名校验

生产接入建议：
1. 用平台SDK替换 `show()` 内部实现。
2. 保留 `AdEvent` 回调用于统一埋点。
3. 服务端校验 `reward_token` 后再下发奖励。

## 6. 监控与数据落地
- 本地落库：`MetricsStore`（SQLite）
- 健康聚合：`aggregate_health()`
- 时序导出：`export_health(TimeSeriesExporter)`

示例：
```python
store = MetricsStore("metrics.db")
store.init_schema()
store.ingest(tracker)
health = store.aggregate_health()
```

## 7. 关卡批量扫描
脚本：`scripts/scan_levels.py`

扫描目录：`levels/*.json`
```bash
python scripts/scan_levels.py
```

输出指标：
- `valid_rate`
- `unique_rate`
- `fail_zone_pass`
- `progress`
- `step_hist`

## 8. 发布流程建议
1. 合并代码并跑 `pytest`。
2. 扫描关卡包，确保 `valid_rate/unique_rate` 达标。
3. 灰度发布：先 5% 用户。
4. 观察 `ad_conversion` 和 `near_fail_rate`，再扩大流量。

## 9. 玩法增强模块
- 教程：`TutorialGuide`（`tutorial.py`）
- 成就：`AchievementSystem`（`achievements.py`）
- 回放：`ReplayRecorder`（`replay.py`）

建议在客户端 UI 中接入：
1. 教程气泡引导（首日首局）。
2. RESULT 页展示成就解锁。
3. RESULT 页展示回放摘要（合成次数、连锁次数）。

## 10. UI接线与资源配置
- UI控制层：`src/hechengqijing/ui.py`（`GameUIController`）
- 音效映射：`src/hechengqijing/audio.py`（`FREE_AUDIO_CUES`）
- 关卡包目录：`levels/`（30关）

接线建议：
1. App 启动时 `controller.start()`。
2. 棋盘点击事件调用 `on_cell_click(x, y)`。
3. 提示按钮调用 `on_hint()`。
4. 广告按钮调用 `on_watch_ad()`。
5. 金币救援按钮调用 `on_spend_coins()`。
