from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReplayEvent:
    action: str
    payload: dict


@dataclass
class ReplayRecorder:
    events: list[ReplayEvent] = field(default_factory=list)

    def record(self, action: str, **payload: object) -> None:
        self.events.append(ReplayEvent(action=action, payload=dict(payload)))

    def summary(self) -> dict:
        merges = len([e for e in self.events if e.action == "merge"])
        chains = len([e for e in self.events if e.action == "chain"])
        return {"events": len(self.events), "merges": merges, "chains": chains}
