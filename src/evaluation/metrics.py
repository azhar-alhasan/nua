from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class MetricCollector:
    counters: dict[str, int] = field(default_factory=dict)

    def inc(self, name: str, amount: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + amount

    def snapshot(self) -> dict[str, int]:
        return dict(self.counters)
