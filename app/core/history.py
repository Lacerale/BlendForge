from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HistoryState:
    actions: list[str] = field(default_factory=list)

    def push(self, description: str) -> None:
        self.actions.append(description)

    def last(self) -> str | None:
        return self.actions[-1] if self.actions else None
