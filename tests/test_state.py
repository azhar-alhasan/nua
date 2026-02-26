# tests/test_state.py
from agent.state import AgentState, TodoItem, SubagentLog, TokenBudget

def test_todo_item_structure():
    item: TodoItem = {
        "id": "task-1",
        "description": "Search for information",
        "status": "pending",
        "result": None,
    }
    assert item["id"] == "task-1"
    assert item["status"] == "pending"

def test_agent_state_structure():
    state: AgentState = {
        "objective": "Do something",
        "todo": [],
        "artifacts": {},
        "subagent_logs": [],
        "token_usage": {"total_used": 0, "per_subagent_limit": 4096},
        "final_output": None,
        "messages": [],
    }
    assert state["objective"] == "Do something"
    assert state["token_usage"]["per_subagent_limit"] == 4096

def test_subagent_log_structure():
    log: SubagentLog = {
        "todo_id": "task-1",
        "prompt": "Search for X",
        "tools": ["search_internet"],
        "result": "Found X",
        "tokens_used": 512,
    }
    assert log["tokens_used"] == 512
