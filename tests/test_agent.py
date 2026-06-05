import json

from src import agent
from src.llm import LLMMessage, ToolCall


def make_fake(scripted_messages):
    """Returns a call_model() stand-in that yields scripted messages in order."""
    calls = {"i": 0}

    def fake_call_model(messages, tools):
        msg = scripted_messages[calls["i"]]
        calls["i"] += 1
        return msg

    return fake_call_model


def test_agent_runs_tool_then_answers():
    scripted = [
        # turn 1: model asks to run a query
        LLMMessage(tool_calls=[
            ToolCall(id="c1", name="run_sql",
                     arguments=json.dumps({"query": "SELECT Name FROM Track LIMIT 1"}))
        ]),
        # turn 2: model gives a final answer (no tool calls)
        LLMMessage(content="There is at least one track."),
    ]
    result = agent.answer("Is there any track?", call_model=make_fake(scripted))
    assert result["answer"] == "There is at least one track."
    assert result["sql"] == ["SELECT Name FROM Track LIMIT 1"]


def test_agent_respects_step_cap():
    # a model that ALWAYS asks for another tool call would loop forever
    always_tool = LLMMessage(tool_calls=[
        ToolCall(id="c", name="get_schema", arguments="{}")
    ])
    scripted = [always_tool] * 50
    result = agent.answer("loop forever?", call_model=make_fake(scripted), max_steps=3)
    assert "couldn't" in result["answer"].lower()
