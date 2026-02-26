# tests/test_registry.py
import pytest
from tools.file_tools import VirtualFS
from tools.registry import ToolRegistry

def test_get_file_tools():
    fs = VirtualFS()
    registry = ToolRegistry(fs)
    tools = registry.get_tools(["read_file", "write_file"])
    names = [t.name for t in tools]
    assert "read_file" in names
    assert "write_file" in names

def test_get_assignable_tools():
    fs = VirtualFS()
    registry = ToolRegistry(fs)
    tools = registry.get_tools(["execute_code", "search_internet", "web_scrape"])
    names = [t.name for t in tools]
    assert "execute_code" in names
    assert "search_internet" in names
    assert "web_scrape" in names

def test_unknown_tool_raises():
    fs = VirtualFS()
    registry = ToolRegistry(fs)
    with pytest.raises(KeyError):
        registry.get_tools(["nonexistent_tool"])

def test_all_tools_listed():
    fs = VirtualFS()
    registry = ToolRegistry(fs)
    all_names = registry.available_tools()
    assert "read_file" in all_names
    assert "write_file" in all_names
    assert "edit_file" in all_names
    assert "execute_code" in all_names
    assert "search_internet" in all_names
    assert "web_scrape" in all_names
