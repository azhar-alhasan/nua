# tests/test_graph.py
from unittest.mock import patch, MagicMock

def test_graph_compiles():
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    with patch("agent.supervisor.ChatOpenAI", return_value=mock_llm):
        with patch("agent.subagent.ChatOpenAI"):
            from agent.graph import build_graph
            graph = build_graph()
            assert graph is not None

def test_graph_has_supervisor_node():
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    with patch("agent.supervisor.ChatOpenAI", return_value=mock_llm):
        with patch("agent.subagent.ChatOpenAI"):
            from agent.graph import build_graph
            graph = build_graph()
            assert "supervisor" in graph.nodes
