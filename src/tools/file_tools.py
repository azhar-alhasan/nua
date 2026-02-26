from __future__ import annotations
from langchain_core.tools import tool


class VirtualFS:
    def __init__(self) -> None:
        self._files: dict[str, str] = {}

    def read(self, path: str) -> str:
        return self._files.get(path, f"Error: file '{path}' not found")

    def write(self, path: str, content: str) -> dict:
        self._files[path] = content
        return {"path": path, "bytes_written": len(content.encode())}

    def edit(self, path: str, edits: list[dict] | str) -> dict:
        if path not in self._files:
            return {"error": f"file '{path}' not found"}
        old = self._files[path]
        if isinstance(edits, str):
            self._files[path] = edits
            diff = f"- {old}\n+ {edits}"
        else:
            content = old
            for op in edits:
                content = content.replace(op["find"], op["replace"])
            self._files[path] = content
            diff = f"- {old}\n+ {content}"
        return {"path": path, "diff": diff}

    def snapshot(self) -> dict[str, str]:
        """Return a copy of all virtual files for state synchronization."""
        return dict(self._files)


def make_file_tools(fs: VirtualFS) -> list:
    @tool
    def read_file(path: str) -> str:
        """Read a file from the virtual file system."""
        return fs.read(path)

    @tool
    def write_file(path: str, content: str) -> dict:
        """Write content to a file in the virtual file system."""
        return fs.write(path, content)

    @tool
    def edit_file(path: str, edits: list[dict] | str) -> dict:
        """Edit a file: pass a list of find/replace dicts or a full replacement string."""
        return fs.edit(path, edits)

    return [read_file, write_file, edit_file]
