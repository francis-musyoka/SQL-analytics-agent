"""The agent loop: think -> act -> observe, repeated until the model answers
or we hit the step cap.

answer_question() takes an optional `call_model` so tests can inject a fake LLM.
"""
import json

from src import context, tools
from src.config import MAX_AGENT_STEPS
from src.llm import call_model

SYSTEM_PROMPT = """You are a careful data analyst with access to a SQLite database.
To answer the user's question:
1. Call get_schema first to learn the exact table and column names.
2. Write ONE SELECT query and call run_sql.
3. If run_sql returns a string starting with ERROR, read it, fix your query, and try again.
4. Once you have the data, reply with a short, direct answer in plain English.
Never invent table or column names. Only use the provided tools."""


def _assistant_dict(msg):
    """Convert our LLMMessage back into the OpenAI message format to re-send."""
    d = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": tc.arguments},
            }
            for tc in msg.tool_calls
        ]
    return d


def answer_question(question, call_model=call_model, max_steps=MAX_AGENT_STEPS):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    sql_used = []

    for _ in range(max_steps):
        msg = call_model(messages, tools.TOOLS)
        messages.append(_assistant_dict(msg))

        if not msg.tool_calls:               # no tool requested => final answer
            return {"answer": msg.content, "sql": sql_used}

        for tc in msg.tool_calls:            # run each requested tool
            args = json.loads(tc.arguments or "{}")
            if tc.name == "run_sql" and "query" in args:
                sql_used.append(args["query"])
            result = context.truncate_result(tools.dispatch_tool(tc.name, args))
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": result}
            )

    return {
        "answer": "Sorry, I couldn't reach an answer within the step limit.",
        "sql": sql_used,
    }
