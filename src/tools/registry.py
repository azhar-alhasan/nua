from __future__ import annotations
from tools.file_tools import VirtualFS, make_file_tools
from tools.code_tools import make_code_tools
from tools.web_tools import make_web_tools


class ToolRegistry:
    def __init__(self, fs: VirtualFS) -> None:
        self._fs = fs
        all_tools = (
            make_file_tools(fs)
            + make_code_tools()
            + make_web_tools()
        )
        self._tools = {t.name: t for t in all_tools}

    def get_tools(self, names: list[str]):
        return [self._tools[name] for name in names]  # raises KeyError if unknown

    def available_tools(self) -> list[str]:
        return list(self._tools.keys())

    def artifacts(self) -> dict[str, str]:
        return self._fs.snapshot()
