from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib import request

from .analytics import EventTracker


DAILY_AD_REVENUE_SQL = """
SELECT date, dau, total_ads, total_watched, avg_ads_per_dau, daily_revenue, arpdau
FROM ad_metrics
ORDER BY date DESC;
""".strip()

FAIL_CONVERSION_FUNNEL_SQL = """
SELECT level_range, total_players, reached_fail_step, ad_shown, ad_watched, success_after_ad
FROM level_analysis;
""".strip()


@dataclass
class AlertThresholds:
    ad_conversion_below: float = 0.2
    near_fail_low: float = 0.3
    near_fail_high: float = 0.7


class TimeSeriesExporter:
    """Exporter with buffer + optional HTTP sink."""

    def __init__(self, endpoint: str | None = None) -> None:
        self.buffer: list[dict] = []
        self.endpoint = endpoint

    def push(self, metric: dict, dry_run: bool = True) -> bool:
        self.buffer.append(metric)
        if not self.endpoint or dry_run:
            return True
        data = json.dumps(metric).encode("utf-8")
        req = request.Request(self.endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=2) as resp:
            return 200 <= resp.status < 300


class MetricsStore:
    def __init__(self, db_path: str = "metrics.db") -> None:
        self.db_path = Path(db_path)

    def init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def ingest(self, tracker: EventTracker) -> int:
        rows = [(e.name, json.dumps(e.params, ensure_ascii=False)) for e in tracker.events]
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("INSERT INTO events(name, payload) VALUES (?, ?)", rows)
        return len(rows)

    def aggregate_health(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT name, payload FROM events").fetchall()

        total = len(rows)
        if total == 0:
            return {"events": 0, "ad_conversion": 0.0, "near_fail_rate": 0.0}

        ad_show = sum(1 for r in rows if r[0] == "rescue_ad_show")
        ad_convert = sum(1 for r in rows if r[0] == "rescue_ad_convert")
        level_start = sum(1 for r in rows if r[0] == "level_start")
        near_fail = sum(1 for r in rows if r[0] == "level_fail_step")

        return {
            "events": total,
            "ad_conversion": (ad_convert / ad_show) if ad_show else 0.0,
            "near_fail_rate": (near_fail / level_start) if level_start else 0.0,
        }

    def export_health(self, exporter: TimeSeriesExporter, dry_run: bool = True) -> dict:
        health = self.aggregate_health()
        exporter.push(health, dry_run=dry_run)
        return health


def evaluate_alerts(ad_conversion_rate: float, near_fail_rate: float, thresholds: AlertThresholds | None = None) -> list[str]:
    t = thresholds or AlertThresholds()
    alerts: list[str] = []
    if ad_conversion_rate < t.ad_conversion_below:
        alerts.append("广告转化率过低")
    if near_fail_rate < t.near_fail_low:
        alerts.append("卡点触发不足")
    elif near_fail_rate > t.near_fail_high:
        alerts.append("卡点触发过高")
    return alerts
