# tests/test_context.py
import pytest
from context.manager import ContextBudgetAllocator, TokenBudgetExceeded

def test_allocate_splits_budget():
    allocator = ContextBudgetAllocator(total_budget=4096)
    allocation = allocator.allocate(
        system_prompt_tokens=200,
        task_context_tokens=1000,
    )
    assert allocation["system_prompt"] == 200
    assert allocation["task_context"] == 1000
    assert allocation["tool_results_buffer"] > 0
    assert allocation["response_generation"] > 0
    total = sum(allocation.values())
    assert total <= 4096

def test_raises_when_over_budget():
    allocator = ContextBudgetAllocator(total_budget=4096)
    with pytest.raises(TokenBudgetExceeded):
        allocator.allocate(
            system_prompt_tokens=2000,
            task_context_tokens=3000,
        )

def test_track_usage():
    allocator = ContextBudgetAllocator(total_budget=4096)
    allocator.record_usage(512)
    allocator.record_usage(256)
    assert allocator.total_used == 768

def test_remaining_budget():
    allocator = ContextBudgetAllocator(total_budget=4096)
    allocator.record_usage(1000)
    assert allocator.remaining == 3096
