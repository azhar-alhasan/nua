from __future__ import annotations
from typing import Literal, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TodoItem(TypedDict):
    id: str
    description: str
    status: Literal["pending", "in_progress", "done"]
    result: str | None


class SubagentLog(TypedDict):
    todo_id: str
    prompt: str
    tools: list[str]
    result: str
    tokens_used: int


class TokenBudget(TypedDict):
    total_used: int
    per_subagent_limit: int


class AgentState(TypedDict):
    objective: str
    todo: list[TodoItem]
    artifacts: dict[str, str]
    subagent_logs: list[SubagentLog]
    token_usage: TokenBudget
    final_output: str | None
    messages: Annotated[list[BaseMessage], add_messages]
