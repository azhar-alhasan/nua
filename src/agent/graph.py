from __future__ import annotations
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from tools.file_tools import VirtualFS
from tools.registry import ToolRegistry
from agent.supervisor import build_supervisor_node, should_continue


def build_graph():
    fs = VirtualFS()
    registry = ToolRegistry(fs)
    supervisor_node = build_supervisor_node(registry)

    builder = StateGraph(AgentState)
    builder.add_node("supervisor", supervisor_node)
    builder.set_entry_point("supervisor")
    builder.add_conditional_edges(
        "supervisor",
        should_continue,
        {"continue": "supervisor", "end": END},
    )
    return builder.compile()


# Module-level graph instance for LangGraph Studio
# Import lazily to avoid ChatOpenAI instantiation at import time in tests
def _get_graph():
    import os
    if os.getenv("OPENROUTER_API_KEY"):
        return build_graph()
    return None

graph = _get_graph()
