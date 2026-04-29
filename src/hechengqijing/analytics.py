from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Event:
    name: str
    params: Dict[str, object]


@dataclass
class EventTracker:
    events: List[Event] = field(default_factory=list)

    def track(self, name: str, **params: object) -> None:
        self.events.append(Event(name=name, params=params))

    def count(self, name: str) -> int:
        return len([e for e in self.events if e.name == name])

    def last(self, name: str) -> Event | None:
        for event in reversed(self.events):
            if event.name == name:
                return event
        return None
