from __future__ import annotations
from dataclasses import dataclass, field


class TokenBudgetExceeded(Exception):
    pass


@dataclass
class ContextBudgetAllocator:
    total_budget: int = 4096
    _tool_results_reserve: int = 512
    _response_reserve: int = 512
    total_used: int = field(default=0, init=False)

    def allocate(self, system_prompt_tokens: int, task_context_tokens: int) -> dict[str, int]:
        fixed = system_prompt_tokens + task_context_tokens
        variable = self._tool_results_reserve + self._response_reserve
        if fixed + variable > self.total_budget:
            raise TokenBudgetExceeded(
                f"Required {fixed + variable} tokens exceeds budget of {self.total_budget}"
            )
        return {
            "system_prompt": system_prompt_tokens,
            "task_context": task_context_tokens,
            "tool_results_buffer": self._tool_results_reserve,
            "response_generation": self._response_reserve,
        }

    def record_usage(self, tokens: int) -> None:
        self.total_used += tokens

    @property
    def remaining(self) -> int:
        return self.total_budget - self.total_used
