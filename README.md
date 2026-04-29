# 合成奇境（广告机会驱动版）

本仓库是《合成奇境》PRD的工程化实现版本，目标是：
- 保持可玩性优先（不依赖强制广告）；
- 在困难节点提供可选广告捷径；
- 用数据与配置驱动持续优化。

## 快速开始
```bash
python -m pip install -e .
python -m pytest -q
```

## 核心模块
- `engine.py`：游戏主循环、状态推进、决策处理。
- `merge.py`：合成与连锁规则。
- `level_generator.py`：模板驱动关卡。
- `ad_system.py`：广告策略、平台约束、触发优先级。
- `analytics.py`：本地埋点追踪。
- `config.py`：远程配置模型。
- `abtest.py`：A/B实验分桶。
- `difficulty.py`：难度动态调节。
- `dsl.py`：关卡DSL校验。
- `solver.py`：离线可解性/唯一解BFS求解。
- `monitoring.py`：SQLite落库与告警评估。
- `adsdk.py`：广告SDK抽象层。
- `tutorial.py`：新手引导流程。
- `achievements.py`：成就系统。
- `replay.py`：关卡回放记录。
- `gameplay_assessment.py`：完整度/可玩性评估。
- `ui.py`：UI控制器与交互接线层。
- `audio.py`：音效映射与播放管理。

## 文档
- `docs/architecture.md`：功能映射与已完成/未完成清单。
- `assets/public_resources.md`：公开资源来源建议。
- `assets/ui_audio_resources.md`：UI与音效资源清单。
- `docs/progress.md`：当前完成进度与剩余优化项。
- `docs/deployment.md`：部署与配置文档。


## 离线工具
- `scripts/scan_levels.py`：批量扫描 `levels/*.json`，输出可解率、唯一解率与步数分布。
