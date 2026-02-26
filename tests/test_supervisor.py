# tests/test_supervisor.py
from unittest.mock import patch, MagicMock
from agent.state import AgentState
from tools.file_tools import VirtualFS
from tools.registry import ToolRegistry
from agent.supervisor import build_supervisor_node, should_continue

def make_state(**kwargs) -> AgentState:
    defaults: AgentState = {
        "objective": "Test objective",
        "todo": [],
        "artifacts": {},
        "subagent_logs": [],
        "token_usage": {"total_used": 0, "per_subagent_limit": 4096},
        "final_output": None,
        "messages": [],
    }
    defaults.update(kwargs)
    return defaults

def test_should_continue_when_todo_pending():
    state = make_state(todo=[
        {"id": "1", "description": "task", "status": "pending", "result": None}
    ])
    assert should_continue(state) == "continue"

def test_should_continue_when_all_done_but_no_final_output():
    # All todos done but no final_output yet — supervisor should get one more pass
    state = make_state(todo=[
        {"id": "1", "description": "task", "status": "done", "result": "ok"}
    ])
    assert should_continue(state) == "continue"

def test_should_end_when_final_output_set():
    state = make_state(final_output="All done!")
    assert should_continue(state) == "end"

def test_supervisor_node_returns_state_update():
    fs = VirtualFS()
    registry = ToolRegistry(fs)

    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.tool_calls = []
    mock_response.content = "All tasks complete."
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    with patch("agent.supervisor.ChatOpenAI", return_value=mock_llm):
        supervisor_node = build_supervisor_node(registry)
        state = make_state(
            todo=[{"id": "1", "description": "search", "status": "done", "result": "found"}]
        )
        result = supervisor_node(state)

    assert isinstance(result, dict)


def test_task_tool_updates_token_usage_and_artifacts():
    fs = VirtualFS()
    registry = ToolRegistry(fs)
    write_tool = registry.get_tools(["write_file"])[0]

    class FakeTaskTool:
        name = "task_tool"

        def invoke(self, args):
            write_tool.invoke({"path": "out.txt", "content": "hello world"})
            return "Task completed successfully"

    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.tool_calls = [
        {
            "name": "task_tool",
            "id": "tc-task-1",
            "args": {
                "todo_id": "1",
                "task_description": "Create output file",
                "tool_names": ["write_file"],
                "context": "Need an artifact for downstream steps",
            },
        }
    ]
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    with patch("agent.supervisor.ChatOpenAI", return_value=mock_llm):
        with patch("agent.supervisor.build_task_tool", return_value=FakeTaskTool()):
            supervisor_node = build_supervisor_node(registry)
            state = make_state(
                todo=[{"id": "1", "description": "create file", "status": "pending", "result": None}]
            )
            result = supervisor_node(state)

    assert result["todo"][0]["status"] == "done"
    assert result["subagent_logs"][0]["tokens_used"] > 0
    assert result["token_usage"]["total_used"] == result["subagent_logs"][0]["tokens_used"]
    assert result["artifacts"]["out.txt"] == "hello world"


def test_supervisor_node_accepts_minimal_studio_input_state():
    fs = VirtualFS()
    registry = ToolRegistry(fs)

    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.tool_calls = []
    mock_response.content = "All tasks complete."
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    with patch("agent.supervisor.ChatOpenAI", return_value=mock_llm):
        supervisor_node = build_supervisor_node(registry)
        # Studio can start with objective-only state payloads.
        result = supervisor_node({"objective": "Test objective"})

    assert result["final_output"] == "All tasks complete."


def test_supervisor_can_execute_shared_file_tools():
    fs = VirtualFS()
    registry = ToolRegistry(fs)

    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.tool_calls = [
        {
            "name": "write_file",
            "id": "tc-write-1",
            "args": {"path": "notes.txt", "content": "hello"},
        },
    ]
    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.return_value = mock_response

    with patch("agent.supervisor.ChatOpenAI", return_value=mock_llm):
        supervisor_node = build_supervisor_node(registry)
        result = supervisor_node(make_state())

    assert result["artifacts"]["notes.txt"] == "hello"
