from context.compression import compress_text, compress_tool_results
from context.memory import WorkingMemory


def test_compress_text_truncates_long_input():
    text = "word " * 200
    result = compress_text(text, max_words=10)
    assert result.endswith(" ...")
    assert len(result.split()) <= 12


def test_compress_tool_results_limits_items():
    results = [f"result {i}" for i in range(10)]
    packed = compress_tool_results(results, max_items=3)
    assert "[Result 3]" in packed
    assert "[Result 4]" not in packed


def test_working_memory_context_block():
    memory = WorkingMemory()
    memory.set_fact("url", "https://example.com")
    assert memory.get_fact("url") == "https://example.com"
    assert "- url: https://example.com" in memory.to_context_block()
