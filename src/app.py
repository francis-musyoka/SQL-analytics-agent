"""Flask demo UI. Run with: python -m src.app  (then open http://localhost:5000)

This is a thin web layer over the agent. It owns NO query logic -- it asks the
agent a question and renders what comes back. To also show the result as a table,
it re-runs the agent's final query through db.run_sql (read-only, so this is safe
and cheap).
"""
from flask import Flask, jsonify, render_template, request

from src import db
from src.agent import answer_question

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/ask")
def ask():
    question = (request.get_json(silent=True) or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    result = answer_question(question)

    # Re-run the agent's final query so we can show the actual rows in a table.
    columns, rows = [], []
    if result["sql"]:
        try:
            table = db.run_sql(result["sql"][-1])
            columns, rows = table["columns"], table["rows"]
        except db.QueryError:
            pass  # the agent's prose answer still stands; just no table

    return jsonify(
        {
            "answer": result["answer"],
            "sql": result["sql"],
            "columns": columns,
            "rows": rows,
        }
    )


def main():
    # debug=True gives auto-reload + tracebacks during development.
    app.run(host="127.0.0.1", port=5000, debug=True)


if __name__ == "__main__":
    main()
