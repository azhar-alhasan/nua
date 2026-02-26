from __future__ import annotations


def compress_text(text: str, max_words: int = 120) -> str:
    """Compress verbose text to a bounded word count for prompt packing."""
    words = (text or "").split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " ..."


def compress_tool_results(results: list[str], max_items: int = 5, max_words_each: int = 80) -> str:
    """Compact tool outputs into a short context block for the next model call."""
    selected = results[:max_items]
    lines: list[str] = []
    for idx, item in enumerate(selected, start=1):
        lines.append(f"[Result {idx}] {compress_text(item, max_words=max_words_each)}")
    return "\n".join(lines)
