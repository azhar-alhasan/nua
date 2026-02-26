from __future__ import annotations
import os
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from tools.registry import ToolRegistry
from context.manager import ContextBudgetAllocator, TokenBudgetExceeded


SUBAGENT_SYSTEM_TEMPLATE = """You are a specialized AI subagent.

Scope:
- TODO ID: {todo_id}
- Task: {task_description}

Success criteria:
- Complete the requested task directly and report concrete outcomes.
- If artifacts (notes, scripts, report) are produced, persist them using write_file.
- Return a concise final summary that can be merged into the supervisor plan.

Constraints:
- Stay within task scope; do not attempt unrelated work.
- Use only the tools listed in "Available tools" below.
- If required information is missing, state assumptions explicitly in your result.

Task context:
{context}

Available tools:
{available_tools}
"""


def build_task_tool(registry: ToolRegistry):
    @tool
    def task_tool(
        todo_id: str,
        task_description: str,
        tool_names: list[str],
        context: str = "",
    ) -> str:
        """
        Create and run a subagent for a specific task.

        Args:
            todo_id: The ID of the TODO item this subagent is working on
            task_description: What the subagent should accomplish
            tool_names: List of tool names to give the subagent (from registry)
            context: Additional context from the supervisor
        """
        system_prompt = SUBAGENT_SYSTEM_TEMPLATE.format(
            todo_id=todo_id,
            task_description=task_description,
            context=context,
            available_tools=", ".join(tool_names) if tool_names else "(none)",
        )

        # Check token budget
        try:
            allocator = ContextBudgetAllocator(total_budget=4096)
            allocator.allocate(
                system_prompt_tokens=len(system_prompt.split()),
                task_context_tokens=len(context.split()),
            )
        except TokenBudgetExceeded as e:
            return f"Error: context budget exceeded — {e}"

        tools = registry.get_tools(tool_names)

        llm = ChatOpenAI(
            model=os.getenv("SUBAGENT_MODEL", "anthropic/claude-haiku-4.5"),
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=system_prompt,
        )

        result = agent.invoke({"messages": [("user", task_description)]})
        messages = result.get("messages", [])
        if messages:
            return messages[-1].content
        return "Subagent completed with no output."

    return task_tool
