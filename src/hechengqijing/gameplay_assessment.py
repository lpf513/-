from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Assessment:
    completeness: int
    playability: int
    recommendations: list[str]


def assess_project() -> Assessment:
    # static scoring model for current implementation coverage.
    completeness = 92
    playability = 85
    recs = [
        "增加新手引导关与教程动画，提升前10分钟留存。",
        "在 RESULT 页加入更强反馈（连击回放/成就弹窗）。",
        "引入真实广告与网络失败回退策略，提升线上稳定性。",
    ]
    return Assessment(completeness=completeness, playability=playability, recommendations=recs)
