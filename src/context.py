"""Keep what we send back to the model within budget.

For now: a hard character cap on any single tool result, with a visible marker
so the model knows data was cut.
"""
from src.config import MAX_TOOL_RESULT_CHARS


def truncate_result(text):
    if len(text) <= MAX_TOOL_RESULT_CHARS:
        return text
    cut = len(text) - MAX_TOOL_RESULT_CHARS
    return text[:MAX_TOOL_RESULT_CHARS] + f"\n...[truncated {cut} characters]"
