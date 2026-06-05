"""Flask demo UI. Run with: python -m src.app  (then open http://localhost:5000)

This is a thin web layer over the agent. It owns NO query logic -- it asks the
agent a question and renders what comes back. To also show the result as a table,
it re-runs the agent's final query through db.run_sql (read-only, so this is safe
and cheap).
"""
from flask import Flask, jsonify, render_template, request

from src.agent import answer_question

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/ask")
def ask():
    body = request.get_json(silent=True)
    question = body.get("question") if isinstance(body, dict) else None
    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Please enter a question."}), 400

    result = answer_question(question.strip())

    # The agent already fetched the rows for its final query and returned them,
    # so we render those directly -- no need to re-run the SQL.
    table = result.get("result") or {}
    return jsonify(
        {
            "answer": result["answer"],
            "sql": result["sql"],
            "columns": table.get("columns", []),
            "rows": table.get("rows", []),
        }
    )


def main():
    # debug=True gives auto-reload + tracebacks during development.
    app.run(host="127.0.0.1", port=5000, debug=True)


if __name__ == "__main__":
    main()
