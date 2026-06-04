from src import db

def test_get_schema_lists_known_tables():
    schema = db.get_schema()
    assert "Track" in schema
    assert "Album" in schema


def test_run_sql_returns_rows_for_select():
    result = db.run_sql("SELECT Name FROM Track LIMIT 3")
    assert result["columns"] == ["Name"]
    assert len(result["rows"]) == 3


def test_run_sql_rejects_non_select():
    try:
        db.run_sql("DELETE FROM Track")
        assert False, "should have raised QueryError"
    except db.QueryError:
        pass


def test_run_sql_rejects_multiple_statements():
    try:
        db.run_sql("SELECT 1; DROP TABLE Track")
        assert False, "should have raised QueryError"
    except db.QueryError:
        pass


def test_run_sql_caps_rows():
    result = db.run_sql("SELECT TrackId FROM Track")
    assert len(result["rows"]) <= 100