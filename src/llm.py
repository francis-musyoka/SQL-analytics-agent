"""The ONLY module that imports openai. Translates OpenAI's response into our
own small types (LLMMessage, ToolCall) so the rest of the app is provider-agnostic.
"""
from dataclasses import dataclass, field

from openai import OpenAI

from src.config import MODEL, OPENAI_API_KEY


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # raw JSON string exactly as the model produced it


@dataclass
class LLMMessage:
    content: str | None = None
    tool_calls: list = field(default_factory=list)


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def complete(messages, tools):
    """Send the conversation + tools to OpenAI; return one LLMMessage."""
    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    msg = response.choices[0].message
    tool_calls = [
        ToolCall(id=tc.id, name=tc.function.name, arguments=tc.function.arguments)
        for tc in (msg.tool_calls or [])
    ]
    return LLMMessage(content=msg.content, tool_calls=tool_calls)
