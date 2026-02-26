# tests/test_integration.py
"""
Integration test — runs the full graph with mocked LLM to avoid real API calls.
"""
import json
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from agent.graph import build_graph
from agent.state import AgentState

def make_todo(id, desc, status="pending", result=None):
    return {"id": id, "description": desc, "status": status, "result": result}

def test_full_graph_runs_to_completion():
    # Simulate: supervisor plans → runs one subagent → marks done → ends
    call_count = {"n": 0}

    def mock_invoke(messages):
        n = call_count["n"]
        call_count["n"] += 1
        if n == 0:
            # First call: supervisor creates a todo and calls task_tool
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "update_todo",
                        "id": "tc-1",
                        "args": {
                            "items": [make_todo("t1", "Search for info", "pending")],
                        },
                        "type": "tool_call",
                    },
                    {
                        "name": "task_tool",
                        "id": "tc-2",
                        "args": {
                            "todo_id": "t1",
                            "task_description": "Search for info",
                            "tool_names": ["search_internet"],
                            "context": "test",
                        },
                        "type": "tool_call",
                    },
                ],
            )
        else:
            # Second call: supervisor declares done
            return AIMessage(content="All done! Found the info.")

    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.side_effect = mock_invoke

    mock_subagent = MagicMock()
    mock_subagent.invoke.return_value = {
        "messages": [MagicMock(content="Search result: Python is great")]
    }

    with patch("agent.supervisor.ChatOpenAI", return_value=mock_llm):
        with patch("agent.subagent.ChatOpenAI"):
            with patch("agent.subagent.create_react_agent", return_value=mock_subagent):
                graph = build_graph()
                initial_state: AgentState = {
                    "objective": "Learn about Python",
                    "todo": [],
                    "artifacts": {},
                    "subagent_logs": [],
                    "token_usage": {"total_used": 0, "per_subagent_limit": 4096},
                    "final_output": None,
                    "messages": [],
                }
                result = graph.invoke(initial_state, config={"recursion_limit": 5})

    assert result["final_output"] == "All done! Found the info."
    assert len(result["subagent_logs"]) == 1
    assert result["subagent_logs"][0]["todo_id"] == "t1"
