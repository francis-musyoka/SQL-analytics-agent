import json

from src import tools


def test_tools_expose_both_functions():
    names = {t["function"]["name"] for t in tools.TOOLS}
    assert names == {"get_schema", "run_sql"}


def test_dispatch_tool_get_schema_returns_text():
    out = tools.dispatch_tool("get_schema", {})
    assert "Track" in out


def test_dispatch_tool_run_sql_returns_json_string():
    out = tools.dispatch_tool("run_sql", {"query": "SELECT Name FROM Track LIMIT 1"})
    parsed = json.loads(out)
    assert parsed["columns"] == ["Name"]


def test_dispatch_tool_run_sql_error_is_a_string_not_an_exception():
    out = tools.dispatch_tool("run_sql", {"query": "DELETE FROM Track"})
    assert out.startswith("ERROR:")


def test_dispatch_tool_unknown_tool():
    out = tools.dispatch_tool("nope", {})
    assert out.startswith("ERROR:")
