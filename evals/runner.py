"""Run the agent over the eval dataset and score EXECUTION ACCURACY:
the agent passes a case if the result set of its query equals the result set
of the gold query.
"""
from src import db
from src.agent import answer_question as real_answer


def _normalize(value):
    """Round floats so trivial precision differences don't count as wrong.
    e.g. 10.0951... (the exact average) vs 10.1 (rounded) are the same answer.
    """
    if isinstance(value, float):
        return round(value, 2)
    return value


def _result_set(sql):
    """Run a query and return its rows as a set of tuples (order-insensitive)."""
    res = db.run_sql(sql)
    return {tuple(_normalize(v) for v in row) for row in res["rows"]}


def score_case(case, answer_fn=real_answer):
    gold = _result_set(case["gold_sql"])
    result = answer_fn(case["question"])
    if not result["sql"]:
        return {"question": case["question"], "passed": False, "reason": "no SQL produced",
                "agent_sql": None, "predicted": None, "gold": sorted(map(repr, gold))}
    agent_sql = result["sql"][-1]  # the agent's final query
    try:
        predicted = _result_set(agent_sql)
    except db.QueryError as e:
        return {"question": case["question"], "passed": False, "reason": str(e),
                "agent_sql": agent_sql, "predicted": None, "gold": sorted(map(repr, gold))}
    # diagnostics (sorted reprs so mixed types print without sort errors)
    return {"question": case["question"], "passed": predicted == gold,
            "agent_sql": agent_sql,
            "predicted": sorted(map(repr, predicted)),
            "gold": sorted(map(repr, gold))}


def run_all(cases, answer_fn=real_answer):
    results = [score_case(c, answer_fn=answer_fn) for c in cases]
    passed = sum(1 for r in results if r["passed"])
    return {"passed": passed, "total": len(results), "results": results}


def main():
    """Run a chosen tier of the dataset against the LIVE model (costs tokens).

    Usage:
      python -m evals.runner          # hard tier only (30 cases) -- the default
      python -m evals.runner easy     # easy tier only (50 cases)
      python -m evals.runner all      # both tiers (80 cases)
    """
    import sys

    from evals.dataset import EVAL_CASES, HARD_CASES

    tier = sys.argv[1] if len(sys.argv) > 1 else "hard"
    sets = {"easy": EVAL_CASES, "hard": HARD_CASES, "all": EVAL_CASES + HARD_CASES}
    if tier not in sets:
        print(f"Unknown tier '{tier}'. Choose: easy | hard | all")
        return
    cases = sets[tier]

    report = run_all(cases)
    print(f"\nExecution accuracy ({tier} tier): {report['passed']}/{report['total']}\n")
    for r in report["results"]:
        mark = "PASS" if r["passed"] else "FAIL"
        extra = "" if r["passed"] else f"  ({r.get('reason', 'wrong result set')})"
        print(f"[{mark}] {r['question']}{extra}")

    # diagnostics: show WHY each failure failed (agent SQL + both result sets)
    fails = [r for r in report["results"] if not r["passed"]]
    if fails:
        print("\n" + "=" * 70 + "\nFAILURE DETAILS\n" + "=" * 70)
        for r in fails:
            print(f"\nQ: {r['question']}")
            print(f"  agent SQL : {r.get('agent_sql')}")
            print(f"  predicted : {r.get('predicted')}")
            print(f"  gold      : {r.get('gold')}")


if __name__ == "__main__":
    main()
