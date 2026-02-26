# tests/test_file_tools.py
import pytest
from tools.file_tools import VirtualFS, make_file_tools

def test_write_and_read():
    fs = VirtualFS()
    tools = make_file_tools(fs)
    write = next(t for t in tools if t.name == "write_file")
    read = next(t for t in tools if t.name == "read_file")

    result = write.invoke({"path": "notes.txt", "content": "hello"})
    assert result["path"] == "notes.txt"
    assert result["bytes_written"] == 5

    content = read.invoke({"path": "notes.txt"})
    assert content == "hello"

def test_read_missing_file_returns_error():
    fs = VirtualFS()
    tools = make_file_tools(fs)
    read = next(t for t in tools if t.name == "read_file")
    result = read.invoke({"path": "missing.txt"})
    assert "not found" in result.lower()

def test_edit_file_find_replace():
    fs = VirtualFS()
    tools = make_file_tools(fs)
    write = next(t for t in tools if t.name == "write_file")
    edit = next(t for t in tools if t.name == "edit_file")

    write.invoke({"path": "doc.txt", "content": "Hello World"})
    result = edit.invoke({
        "path": "doc.txt",
        "edits": [{"find": "World", "replace": "LangGraph"}],
    })
    assert result["path"] == "doc.txt"
    assert "diff" in result

    assert fs.read("doc.txt") == "Hello LangGraph"

def test_edit_file_whole_replace():
    fs = VirtualFS()
    tools = make_file_tools(fs)
    write = next(t for t in tools if t.name == "write_file")
    edit = next(t for t in tools if t.name == "edit_file")

    write.invoke({"path": "doc.txt", "content": "old content"})
    result = edit.invoke({"path": "doc.txt", "edits": "new content"})
    assert fs.read("doc.txt") == "new content"


def test_virtualfs_snapshot_returns_copy():
    fs = VirtualFS()
    fs.write("a.txt", "A")
    snap = fs.snapshot()

    snap["a.txt"] = "changed"

    assert fs.read("a.txt") == "A"
