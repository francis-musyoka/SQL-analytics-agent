"""Tool definitions (for the model) and the dispatcher (for our code).

TOOLS is the JSON Schema the model reads. dispatch() turns a tool name +
arguments into a real call against db.py and ALWAYS returns a string, because
tool results are sent back to the model as message text.
"""
import json

from src import db

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "Return the database schema (every table and its columns). Call this first.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Run a single read-only SELECT query and return the resulting rows as JSON.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A single SQLite SELECT statement.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]


def dispatch(name, arguments):
    """Run the tool the model asked for. Returns a STRING in all cases."""
    if name == "get_schema":
        return db.get_schema()
    if name == "run_sql":
        try:
            return json.dumps(db.run_sql(arguments["query"]))
        except db.QueryError as e:
            return f"ERROR: {e}"  # handed back to the model so it can self-correct
    return f"ERROR: unknown tool '{name}'"
