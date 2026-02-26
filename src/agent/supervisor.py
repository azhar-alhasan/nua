from __future__ import annotations
import os
import json
from typing import Literal
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from agent.state import AgentState
from tools.registry import ToolRegistry
from agent.subagent import build_task_tool


SUPERVISOR_SYSTEM = """You are a Supervisor AI agent. Your job is to:
1. Decompose the user's objective into a TODO list using update_todo
2. For each TODO item, call task_tool to create a subagent that completes it
3. Track results and update the TODO list as items complete
4. When all TODO items are done, respond with a final summary (do NOT call any tools)

Always call update_todo first to plan before calling task_tool.

When calling task_tool, include relevant results from previous completed tasks in the context field so subagents can build on prior work.

Available tools you can assign to subagents via tool_names:
- "search_internet" — search the web using Tavily
- "web_scrape" — scrape a webpage using Firecrawl
- "execute_code" — write and execute Python code
- "read_file" — read from virtual file system
- "write_file" — write to virtual file system
- "edit_file" — edit files in virtual file system

Only use exact tool names from the list above in tool_names.
"""


def build_supervisor_node(registry: ToolRegistry):
    task_tool = build_task_tool(registry)
    read_file_tool, write_file_tool, edit_file_tool = registry.get_tools(
        ["read_file", "write_file", "edit_file"]
    )
    shared_file_tools = {
        "read_file": read_file_tool,
        "write_file": write_file_tool,
        "edit_file": edit_file_tool,
    }

    def estimate_tokens(*chunks: str) -> int:
        # Keep accounting simple and deterministic for state/log tracking.
        return sum(len((chunk or "").split()) for chunk in chunks)

    @tool
    def update_todo(items: list[dict]) -> str:
        """
        Update the TODO list. Each item must have: id (str), description (str),
        status ('pending'|'in_progress'|'done'), result (str|null).
        """
        return json.dumps(items)

    supervisor_tools = [update_todo, task_tool, read_file_tool, write_file_tool, edit_file_tool]

    llm = ChatOpenAI(
        model=os.getenv("SUPERVISOR_MODEL", "anthropic/claude-sonnet-4.5"),
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    llm_with_tools = llm.bind_tools(supervisor_tools)

    def supervisor_node(state: AgentState) -> dict:
        objective = state.get("objective", "")
        prior_messages = list(state.get("messages", []))
        todo = list(state.get("todo", []))

        messages = [
            ("system", SUPERVISOR_SYSTEM),
            ("user", f"Objective: {objective}"),
        ] + prior_messages

        if todo:
            messages.append(
                ("user", f"Current TODO list: {json.dumps(todo)}")
            )

        response = llm_with_tools.invoke(messages)

        updates: dict = {"messages": [response]}

        # Process tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                if tc["name"] == "update_todo":
                    try:
                        raw = tc["args"].get("items", "[]")
                        if isinstance(raw, list):
                            new_todo = raw
                        else:
                            new_todo = json.loads(raw)
                        if isinstance(new_todo, list):
                            updates["todo"] = new_todo
                    except (json.JSONDecodeError, TypeError):
                        pass
                    updates["messages"].append(
                        ToolMessage(content="TODO updated", tool_call_id=tc["id"])
                    )
                elif tc["name"] == "task_tool":
                    result = task_tool.invoke(tc["args"])
                    todo_id = tc["args"].get("todo_id", "unknown")
                    task_description = tc["args"].get("task_description", "")
                    context = tc["args"].get("context", "")
                    tokens_used = estimate_tokens(task_description, context, result)

                    # Mark the todo item as done
                    updated_todo = list(todo)
                    for item in updated_todo:
                        if item["id"] == todo_id:
                            item["status"] = "done"
                            item["result"] = result
                    updates["todo"] = updated_todo
                    log = {
                        "todo_id": todo_id,
                        "prompt": task_description,
                        "tools": tc["args"].get("tool_names", []),
                        "result": result,
                        "tokens_used": tokens_used,
                    }
                    updates["subagent_logs"] = state.get("subagent_logs", []) + [log]
                    token_usage = dict(state.get("token_usage", {}))
                    token_usage["per_subagent_limit"] = token_usage.get("per_subagent_limit", 4096)
                    token_usage["total_used"] = token_usage.get("total_used", 0) + tokens_used
                    updates["token_usage"] = token_usage
                    updates["artifacts"] = registry.artifacts()
                    updates["messages"].append(
                        ToolMessage(content=result, tool_call_id=tc["id"])
                    )
                elif tc["name"] in shared_file_tools:
                    file_result = shared_file_tools[tc["name"]].invoke(tc["args"])
                    if isinstance(file_result, (dict, list)):
                        content = json.dumps(file_result)
                    else:
                        content = str(file_result)
                    updates["artifacts"] = registry.artifacts()
                    updates["messages"].append(
                        ToolMessage(content=content, tool_call_id=tc["id"])
                    )
        else:
            # No tool calls — supervisor is done
            updates["final_output"] = response.content

        return updates

    return supervisor_node


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    if state.get("final_output"):
        return "end"
    return "continue"
