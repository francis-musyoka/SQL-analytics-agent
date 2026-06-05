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

When writing SQL:
- SELECT only the column(s) the question asks for. Do not add extra columns such
  as the value you ORDER BY. If asked for a name, return just the name -- not the
  name and its count.
- If the question states a rounding or a unit (e.g. "round to one decimal",
  "in minutes", "in seconds"), apply it inside the query.
- To count HOW MANY entities satisfy an aggregate condition (e.g. how many
  albums have exactly one track), first compute the per-entity aggregate in a
  subquery, then COUNT(*) the qualifying rows in the outer query. Do NOT put
  COUNT(...) in a query that is grouped by the entity -- that returns one row
  per entity, not a single total.
- A "total" spend or revenue for some entity means SUM the relevant amounts
  GROUPED BY that entity. Revenue tied to specific tracks is the sum of
  (line unit price x quantity) on the matching invoice lines, not the whole
  invoice total (an invoice total covers every track on that invoice).

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
    last_result = None  # rows from the last SUCCESSFUL run_sql (the answer's data)

    for _ in range(max_steps):
        msg = call_model(messages, tools.TOOLS)
        messages.append(_assistant_dict(msg))

        if not msg.tool_calls:               # no tool requested => final answer
            return {"answer": msg.content, "sql": sql_used, "result": last_result}

        for tc in msg.tool_calls:            # run each requested tool
            args = json.loads(tc.arguments or "{}")
            if tc.name == "run_sql" and "query" in args:
                sql_used.append(args["query"])
            raw = tools.dispatch_tool(tc.name, args)
            # Capture the structured rows BEFORE truncation so callers (CLI, web,
            # evals) can use what the agent saw instead of re-running the query.
            # We keep the LAST SUCCESSFUL run_sql result, not the last attempt --
            # the final attempt may be an errored or exploratory query.
            if tc.name == "run_sql" and not raw.startswith("ERROR"):
                try:
                    last_result = json.loads(raw)  # {"columns": [...], "rows": [...]}
                except ValueError:
                    pass
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": context.truncate_result(raw)}
            )

    return {
        "answer": "Sorry, I couldn't reach an answer within the step limit.",
        "sql": sql_used,
        "result": last_result,
    }
