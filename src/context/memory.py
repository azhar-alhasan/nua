from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class WorkingMemory:
    """Simple in-process memory store for cross-step facts and notes."""

    _facts: dict[str, str] = field(default_factory=dict)

    def set_fact(self, key: str, value: str) -> None:
        self._facts[key] = value

    def get_fact(self, key: str, default: str = "") -> str:
        return self._facts.get(key, default)

    def to_context_block(self) -> str:
        if not self._facts:
            return ""
        return "\n".join(f"- {k}: {v}" for k, v in self._facts.items())
