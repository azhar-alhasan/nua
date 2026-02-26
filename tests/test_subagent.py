# tests/test_subagent.py
from unittest.mock import patch, MagicMock
from tools.file_tools import VirtualFS
from tools.registry import ToolRegistry
from agent.subagent import build_task_tool

def test_task_tool_is_callable():
    fs = VirtualFS()
    registry = ToolRegistry(fs)
    task_tool = build_task_tool(registry)
    assert task_tool.name == "task_tool"

def test_task_tool_calls_llm(monkeypatch):
    fs = VirtualFS()
    registry = ToolRegistry(fs)

    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {
        "messages": [MagicMock(content="Task done: result here")]
    }

    with patch("agent.subagent.create_react_agent", return_value=mock_agent):
        with patch("agent.subagent.ChatOpenAI"):
            task_tool = build_task_tool(registry)
            result = task_tool.invoke({
                "todo_id": "task-1",
                "task_description": "Search for Python info",
                "tool_names": ["search_internet"],
                "context": "User wants to learn Python",
            })
    assert isinstance(result, str)
    assert len(result) > 0


def test_task_tool_prompt_contains_required_sections():
    fs = VirtualFS()
    registry = ToolRegistry(fs)

    captured = {}

    def fake_create_react_agent(model, tools, prompt):
        captured["prompt"] = prompt
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [MagicMock(content="ok")]}
        return mock_agent

    with patch("agent.subagent.create_react_agent", side_effect=fake_create_react_agent):
        with patch("agent.subagent.ChatOpenAI"):
            task_tool = build_task_tool(registry)
            task_tool.invoke({
                "todo_id": "task-42",
                "task_description": "Analyze docs",
                "tool_names": ["read_file", "write_file"],
                "context": "Focus on assignment constraints",
            })

    prompt = captured["prompt"]
    assert "Scope:" in prompt
    assert "Success criteria:" in prompt
    assert "Constraints:" in prompt
    assert "Available tools:" in prompt
