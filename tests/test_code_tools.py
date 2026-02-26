# tests/test_code_tools.py
from tools.code_tools import make_code_tools

def test_execute_simple_code():
    tools = make_code_tools()
    execute = next(t for t in tools if t.name == "execute_code")
    result = execute.invoke({"code": "print('hello')"})
    assert "hello" in result

def test_execute_arithmetic():
    tools = make_code_tools()
    execute = next(t for t in tools if t.name == "execute_code")
    result = execute.invoke({"code": "print(2 + 2)"})
    assert "4" in result

def test_execute_syntax_error():
    tools = make_code_tools()
    execute = next(t for t in tools if t.name == "execute_code")
    result = execute.invoke({"code": "def ("})
    assert "error" in result.lower() or "Error" in result

def test_execute_runtime_error():
    tools = make_code_tools()
    execute = next(t for t in tools if t.name == "execute_code")
    result = execute.invoke({"code": "raise ValueError('oops')"})
    assert "oops" in result or "ValueError" in result
