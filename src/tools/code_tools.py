from __future__ import annotations
import subprocess
import sys
import textwrap
from langchain_core.tools import tool


def make_code_tools() -> list:
    @tool
    def execute_code(code: str) -> str:
        """Write and execute Python code. Returns stdout + stderr. CodeAct style."""
        try:
            result = subprocess.run(
                [sys.executable, "-c", textwrap.dedent(code)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            return output or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: code execution timed out (30s limit)"
        except Exception as e:
            return f"Error: {e}"

    return [execute_code]
