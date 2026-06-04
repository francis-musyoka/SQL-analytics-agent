"""Read-only access to the SQLite database.

This module is the ONLY thing that touches the database. It knows nothing about
LLMs or tools. Two public functions: get_schema() and run_sql().
"""
import sqlite3

from src.config import DB_PATH, MAX_RESULT_ROWS


class QueryError(Exception):
    """Raised when a query is unsafe or fails to execute."""


def _connect():
    # mode=ro => the SQLite engine itself forbids any write. uri=True is
    # required to use the file:...?mode=ro syntax.
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def get_schema():
    """Return a compact text description of every table and its columns."""
    conn = _connect()
    try:
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        lines = []
        for table in tables:
            cols = [
                f"{r[1]} {r[2]}"  # r[1]=column name, r[2]=column type
                for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()
            ]
            lines.append(f"{table}({', '.join(cols)})")
        return "\n".join(lines)
    finally:
        conn.close()


def _is_read_only(query):
    cleaned = query.strip().rstrip(";").strip()
    if ";" in cleaned:  # any leftover ; means multiple statements -> reject
        return False
    lowered = cleaned.lower()
    return lowered.startswith("select") or lowered.startswith("with")


def run_sql(query):
    """Run a single read-only SELECT and return {'columns': [...], 'rows': [...]}."""
    if not _is_read_only(query):
        raise QueryError("Only a single read-only SELECT query is allowed.")
    conn = _connect()
    try:
        cur = conn.execute(query)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = [list(r) for r in cur.fetchmany(MAX_RESULT_ROWS)]
        return {"columns": columns, "rows": rows}
    except sqlite3.Error as e:
        raise QueryError(str(e))
    finally:
        conn.close()
