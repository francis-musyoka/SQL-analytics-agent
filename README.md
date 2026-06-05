# SQL Analytics Agent

Ask questions about a database in plain English. An LLM agent — built from
scratch, **no agent framework** — writes SQL, runs it against a real database,
reads the results, corrects its own mistakes, and answers.

The agent is given two tools (`get_schema`, `run_sql`); a hand-written
think → act → observe loop executes them, feeds results back, and decides when to
stop. A thin provider wrapper isolates OpenAI specifics so the loop stays
provider-agnostic.

> **Status:** in progress. The full agent runs end-to-end (CLI). The eval harness
> and Streamlit demo are not built yet — see [Roadmap](#roadmap).

## What it demonstrates

- A **hand-written agent loop** (think → act → observe) with tool/function calling.
- **Safe, read-only** database access — the model's output is treated as untrusted
  input (SELECT-only, row cap, read-only connection; defense in depth).
- **Self-correction:** SQL errors are returned to the model as text so it rewrites
  its query and tries again.
- **Provider isolation:** every OpenAI call lives behind one module, so swapping
  providers touches only that file.

## Architecture

Small, single-purpose modules — each knows only the layer below it:

```
cli.py  →  agent.py  →  tools.py  →  db.py
                  ↘  context.py
                  ↘  llm.py  →  OpenAI
```

| Module | Job | Built |
|---|---|:---:|
| `src/config.py` | Central config: paths, model, limits (rows, steps, chars). | ✅ |
| `src/db.py` | Read-only SQLite access: `get_schema()`, `run_sql()` + safety. Knows nothing about LLMs. | ✅ |
| `src/tools.py` | Tool JSON schemas (`TOOLS`) the model reads + `dispatch_tool()` router. | ✅ |
| `src/llm.py` | The **only** file that imports `openai`. Translates the API response into our `LLMMessage` / `ToolCall` types via `call_model()`. | ✅ |
| `src/context.py` | `truncate_result()` — cap oversized tool output to the token budget. | ✅ |
| `src/agent.py` | **The loop.** `answer_question()` orchestrates think → act → observe with a step cap. | ✅ |
| `src/cli.py` | Interactive command line — first real end-to-end run. | ✅ |
| `evals/` | Dataset + runner scoring execution accuracy. | ⬜ planned |
| `src/app.py` | Streamlit demo page. | ⬜ planned |

**Why the separation:** if OpenAI changes its API, only `llm.py` changes. If you
swap SQLite for Postgres, only `db.py` changes. Changes stay local because
responsibilities stay separate.

## Data flow (one question)

```
User asks a question
  → agent sends [question + tool definitions] to the model
  → model: "call get_schema()"        → agent runs it → sends schema back
  → model: "call run_sql('SELECT…')"  → agent runs it
         ├─ SQL error?  → send error text back → model rewrites query (self-correction)
         └─ rows OK?    → send rows back
  → model: "final answer: …"          → agent stops
  → user sees the answer + the SQL that produced it
```

The model decides *what* to do; the agent code actually *does* it and decides
*when to stop* (a final answer, or a hard step cap so it can never loop forever).

## Safety

- **Read-only:** the SQLite connection is opened with `mode=ro` (the engine itself
  refuses writes) **and** non-`SELECT`/`WITH` queries are rejected before running —
  two independent layers.
- **Row cap:** results are limited to `MAX_RESULT_ROWS`.
- **Step cap:** the loop stops after `MAX_AGENT_STEPS` iterations.
- **Context budget:** oversized tool results are truncated with a visible marker so
  the model knows data was cut.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Download the Chinook database into `data/chinook.db`:

```bash
mkdir -p data
curl -L -o data/chinook.db \
  https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite
```

Create `.env` (gitignored) with your key and model:

```
OPENAI_API_KEY=sk-your-key-here
MODEL=gpt-4o-mini
```

## Run it

```bash
python -m src.cli      # interactive terminal — ask questions, watch the SQL
python -m pytest       # run the test suite
```

Example questions to try in the CLI:

- `How many tracks are there?`
- `Which 5 genres have the most tracks?`
- `Who are the top 3 customers by total spend?`

Watch the **"SQL the agent ran"** output — if a query errors, you'll often see the
agent run a corrected query right after. That's the self-correction loop working.

## Testing

The logic-heavy modules are test-driven (`db` safety, the `tools` dispatcher, the
`agent` loop). The agent loop is tested with a **fake LLM** — a scripted stand-in
injected via the `call_model` parameter — so tests are deterministic, instant, and
free. The real API is never called in unit tests.

```bash
python -m pytest -v
```

## Roadmap

- **Evals (next):** a dataset of `(question, gold_sql)` pairs and a runner that
  scores **execution accuracy** (compare the agent's result set to a gold query's —
  the Spider/BIRD metric). This produces the headline number to improve.
- **Streamlit demo:** a clickable web page for non-terminal users.
- Summarize (instead of truncate) large tool results.
- Add query-timeout protection for runaway queries.

