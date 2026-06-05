from evals import runner


def test_result_set_equal_for_equivalent_queries():
    a = runner._result_set("SELECT COUNT(*) FROM Track")
    b = runner._result_set("SELECT COUNT(*) AS n FROM Track")
    assert a == b  # column alias differs, rows identical


def test_result_set_tolerates_float_precision():
    # 0.1 + 0.2 == 0.30000000000000004 in floating point; the scorer should not
    # treat that as a different answer from 0.3.
    a = runner._result_set("SELECT 0.1 + 0.2")
    b = runner._result_set("SELECT 0.3")
    assert a == b


def test_score_case_passes_when_agent_matches_gold():
    case = {"question": "count tracks", "gold_sql": "SELECT COUNT(*) FROM Track"}
    gold_rows = runner.db.run_sql(case["gold_sql"])["rows"]

    def stub_answer(question):
        return {"answer": "...", "sql": ["SELECT COUNT(*) FROM Track"],
                "result": {"columns": ["n"], "rows": gold_rows}}

    out = runner.score_case(case, answer_fn=stub_answer)
    assert out["passed"] is True


def test_score_case_fails_when_no_result():
    case = {"question": "x", "gold_sql": "SELECT COUNT(*) FROM Track"}

    def stub_answer(question):
        return {"answer": "...", "sql": [], "result": None}

    out = runner.score_case(case, answer_fn=stub_answer)
    assert out["passed"] is False


def test_score_case_scores_returned_result_not_last_sql():
    # The agent's LAST sql is broken/exploratory, but it returned the correct
    # rows from an earlier query. Scoring the result (not re-running sql[-1])
    # must still pass -- this is the fix for the "sql[-1] may be errored" bug.
    case = {"question": "count tracks", "gold_sql": "SELECT COUNT(*) FROM Track"}
    gold_rows = runner.db.run_sql(case["gold_sql"])["rows"]

    def stub_answer(question):
        return {"answer": "...", "sql": ["SELECT COUNT(*) FROM Track", "SELECT nonsense ;;"],
                "result": {"columns": ["n"], "rows": gold_rows}}

    out = runner.score_case(case, answer_fn=stub_answer)
    assert out["passed"] is True
