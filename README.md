# nua — LangGraph Supervisor Agent

**nua** is a LangGraph-powered supervisor agent that dynamically creates and orchestrates specialized subagents at runtime to accomplish complex, multi-step objectives.

Given a natural-language objective, the supervisor decomposes the work into a TODO list, spawns a dedicated subagent for each item (via a `task_tool`), equips each subagent with only the tools it needs, enforces a per-subagent context budget, and synthesizes a final output when all tasks are done.

---

## Architecture

```
                        ┌─────────────────────────────┐
                        │          Supervisor          │
                        │  (Claude claude-sonnet-4.5)  │
                        │                              │
User ──► objective ────►│  1. update_todo (plan)       │◄──────────────────┐
                        │  2. task_tool  (delegate)    │                   │
                        └────────────┬────────────────-┘                   │
                                     │  task_tool call                     │
                                     ▼                                     │
                        ┌─────────────────────────────┐                   │
                        │           Subagent           │    result         │
                        │  (Claude claude-haiku-4.5)   │───────────────────┘
                        │                              │
                        │  ReAct loop with tools:      │
                        │  • read_file / write_file    │
                        │  • edit_file                 │
                        │  • execute_code (CodeAct)    │
                        │  • search_internet (Tavily)  │
                        │  • web_scrape (Firecrawl)    │
                        └─────────────────────────────┘

        Supervisor loops (continue ──► supervisor) until:
          • final_output is set, OR
          • all TODO items are "done"
        then exits (──► END)
```

---

## How It Works

### Supervisor Loop

The supervisor is the single LangGraph node. On every invocation it receives the current `AgentState` (objective, TODO list, messages) and calls the OpenRouter-hosted Claude model with bound tools:

- **`update_todo`** — sets the structured TODO list (`id`, `description`, `status`, `result`)
- **`task_tool`** — creates a fresh subagent for a specific TODO item and blocks until it returns
- **`read_file` / `write_file` / `edit_file`** — shared virtual file tools the supervisor can invoke directly

LangGraph routes back to the supervisor (`"continue"`) until `final_output` is populated or every TODO item is `"done"`.

### Subagent Creation (task_tool)

Each `task_tool` invocation:

1. Formats a system prompt from the `SUBAGENT_SYSTEM_TEMPLATE` with the task description and any context passed by the supervisor.
2. Runs the formatted prompt through `ContextBudgetAllocator` — raises `TokenBudgetExceeded` if the combined system prompt + context + reserved buffers exceed 4096 tokens.
3. Fetches the requested tools by name from `ToolRegistry`.
4. Instantiates a `create_react_agent` (LangGraph prebuilt ReAct loop) backed by the Claude Haiku model via OpenRouter.
5. Invokes the agent and returns the final message content to the supervisor.

### Tool Assignment

`ToolRegistry` holds all available tools keyed by name. The supervisor specifies `tool_names` when calling `task_tool`, so each subagent receives only what it needs — keeping context small and behaviour predictable.

Available tools registered at startup:

| Tool name           | Description                                     |
| ------------------- | ----------------------------------------------- |
| `read_file`       | Read a file from the in-memory VirtualFS        |
| `write_file`      | Write a file to the in-memory VirtualFS         |
| `edit_file`       | Find-and-replace edits on a VirtualFS file      |
| `execute_code`    | Run Python code in a subprocess (CodeAct style) |
| `search_internet` | Search the web via Tavily (up to 5 results)     |
| `web_scrape`      | Scrape a URL to markdown via Firecrawl          |

### Context Budget

`ContextBudgetAllocator` (4096 token total) reserves:

- **512 tokens** for tool-results buffer
- **512 tokens** for response generation
- Remaining slots are split between system prompt and task context

If inputs overflow the budget the subagent call fails fast with a clear error rather than silently truncating.

---

## Project Structure

```
nua/
├── src/
│   ├── agent/
│   │   ├── graph.py       # build_graph() + module-level graph for LangGraph Studio
│   │   ├── supervisor.py  # Supervisor node, update_todo tool, should_continue()
│   │   ├── subagent.py    # build_task_tool() factory — creates subagents at runtime
│   │   └── state.py       # TypedDicts: AgentState, TodoItem, SubagentLog, TokenBudget
│   ├── tools/
│   │   ├── file_tools.py  # VirtualFS class + read_file/write_file/edit_file tools
│   │   ├── code_tools.py  # execute_code tool (subprocess, CodeAct pattern)
│   │   ├── web_tools.py   # search_internet (Tavily) + web_scrape (Firecrawl)
│   │   └── registry.py    # ToolRegistry — registers and retrieves tools by name
│   └── context/
│       ├── manager.py     # ContextBudgetAllocator, TokenBudgetExceeded exception
│       ├── compression.py # Context compression helpers
│       └── memory.py      # Lightweight working memory
│   ├── evaluation/
│   │   ├── evaluators.py  # Run quality scoring helpers
│   │   ├── metrics.py     # Metrics collector
│   │   └── verification.py# Output validation helpers
│   └── utils/
│       ├── logging.py     # Structured logger setup
│       └── errors.py      # Shared exception types
├── tests/
│   ├── test_state.py       # State schema construction and defaults
│   ├── test_file_tools.py  # VirtualFS read/write/edit + tool wrappers
│   ├── test_registry.py    # ToolRegistry lookup and available_tools()
│   ├── test_code_tools.py  # execute_code output, stderr, timeout
│   ├── test_web_tools.py   # search_internet and web_scrape (mocked APIs)
│   ├── test_context.py     # ContextBudgetAllocator allocation and overflow
│   ├── test_subagent.py    # task_tool invocation (mocked LLM)
│   ├── test_supervisor.py  # Supervisor node tool-call dispatch (mocked LLM)
│   ├── test_graph.py       # Graph wiring — nodes, edges, entry point
│   ├── test_integration.py # End-to-end graph run with mocked LLM
│   ├── test_evaluation.py  # Evaluation + metrics + verification tests
│   ├── test_utils.py       # Utility module tests
│   ├── test_context_compression_memory.py # Context helpers + memory tests
│   └── scenarios/          # Scenario definitions for higher-level testing
├── docs/
│   └── plans/             # Design documents and task plans
├── langgraph.json         # LangGraph Studio config (graph: agent)
├── pyproject.toml         # Project metadata and dependencies
└── .env.example           # Environment variable template
```

---

## Setup

### Prerequisites

- Python 3.12 or later
- API keys for OpenRouter, LangSmith, Tavily, and Firecrawl (see [Environment Variables](#environment-variables))

### 1. Clone the repository

```bash
git clone https://github.com/your-username/nua.git
cd nua
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install the package with dev dependencies

```bash
pip install -e ".[dev]"
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Open .env and fill in your API keys
```

---

## Environment Variables

| Variable                 | Required | Description                                                                 |
| ------------------------ | -------- | --------------------------------------------------------------------------- |
| `OPENROUTER_API_KEY`   | Yes      | API key for[OpenRouter](https://openrouter.ai) — used to access Claude models |
| `LANGCHAIN_TRACING_V2` | No       | Set to `true` to enable LangSmith tracing                                 |
| `LANGCHAIN_API_KEY`    | No       | LangSmith API key (required when tracing is enabled)                        |
| `LANGCHAIN_PROJECT`    | No       | LangSmith project name (defaults to `nua-supervisor-agent`)               |
| `TAVILY_API_KEY`       | No       | [Tavily](https://tavily.com) API key — required for `search_internet` tool  |
| `FIRECRAWL_API_KEY`    | No       | [Firecrawl](https://firecrawl.dev) API key — required for `web_scrape` tool |

The supervisor uses `anthropic/claude-sonnet-4.5` and subagents use `anthropic/claude-haiku-4.5` by default. Override with `SUPERVISOR_MODEL` and `SUBAGENT_MODEL` environment variables.

---

## Run Tests

```bash
pytest -v
```

All tests use mocked LLMs and mocked external APIs — no real API keys are needed to run the test suite.

---

## Run in LangGraph Studio

LangGraph Studio provides a visual interface for running and debugging the agent graph.

### 1. Install the LangGraph CLI

```bash
pip install langgraph-cli
```

### 2. Start the dev server

```bash
langgraph dev
```

### 3. Open the Studio UI

Navigate to [http://localhost:2024](http://localhost:2024) in your browser.

### 4. Send an objective

In the Studio input panel, send the following JSON:

```json
{"objective": "your objective here"}
```

The graph will begin executing, and you can watch each supervisor loop, TODO updates, and subagent calls in real time.

---

## LangSmith Tracing & Evaluation

- Tracing is enabled with `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY`.
- `evaluation/verification.py` validates final outputs.
- `evaluation/evaluators.py` computes deterministic run-quality signals for regression checks.
- `evaluation/metrics.py` provides a small metrics collector for run counters and custom telemetry.

---

## Example Usage

**Objective:**

```json
{"objective": "Research the top 3 Python web frameworks in 2025, write a comparison report, and save it to report.md"}
```

**Expected behaviour:**

1. Supervisor calls `update_todo` with three items:

   - `task-1`: Search for top Python web frameworks in 2025
   - `task-2`: Scrape the homepage of each framework for feature details
   - `task-3`: Write a comparison report and save it to `report.md`
2. For each item the supervisor calls `task_tool`:

   - `task-1` subagent receives `search_internet` — returns search results
   - `task-2` subagent receives `web_scrape` — returns markdown from each framework site
   - `task-3` subagent receives `write_file` and `execute_code` — writes the report to the VirtualFS
3. Supervisor marks all items done, produces `final_output` summarising the results, and the graph exits.
