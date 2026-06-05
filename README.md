# SQL Analytics Agent

Ask questions about a database in plain English. An LLM agent — built from
scratch, **no agent framework** — writes SQL, runs it against a real database,
reads the results, corrects its own mistakes, and answers.

The agent is given two tools (`get_schema`, `run_sql`); a hand-written
think → act → observe loop executes them, feeds results back, and decides when to
stop. A thin provider wrapper isolates OpenAI specifics so the loop stays
provider-agnostic.

## What it demonstrates

- A **hand-written agent loop** (think → act → observe) with tool/function calling.
- **Safe, read-only** database access — the model's output is treated as untrusted
  input (SELECT-only, row cap, read-only connection; defense in depth).
- **Self-correction:** SQL errors are returned to the model as text so it rewrites
  its query and tries again.
- **Provider isolation:** every OpenAI call lives behind one module, so swapping
  providers touches only that file.
- **Measured quality:** an eval harness reporting *execution accuracy* (the agent's
  result set vs. a hand-verified gold query's — the Spider/BIRD metric).

## Accuracy

On the 80-question eval set (`python -m evals.runner`):

| Model | Score | Notes |
|---|---|---|
| `gpt-4o-mini` | **76 / 80 (95%)** | after prompt + scoring improvements (see below) |
| `gpt-5.4` | **30 / 30** on the hard tier | frontier-model capability ceiling |

The jump on `gpt-4o-mini` (baseline ~50% on the hard tier) came from two honest
fixes: **float-tolerant scoring** (a measurement-fairness fix) and **general
SQL-technique guidance** in the system prompt — never test-specific answers. The
remaining failures are the small model's reliability ceiling.

## Architecture

Small, single-purpose modules — each knows only the layer below it:

```
cli.py / app.py  →  agent.py  →  tools.py  →  db.py
                          ↘  context.py
                          ↘  llm.py  →  OpenAI
```

| Module | Job |
|---|---|
| `src/config.py` | Central config: paths, model, temperature, limits (rows, steps, chars). |
| `src/db.py` | Read-only SQLite access: `get_schema()`, `run_sql()` + safety. Knows nothing about LLMs. |
| `src/tools.py` | Tool JSON schemas (`TOOLS`) the model reads + `dispatch_tool()` router. |
| `src/llm.py` | The **only** file that imports `openai`. Translates the API response into our `LLMMessage` / `ToolCall` types via `call_model()`. |
| `src/context.py` | `truncate_result()` — cap oversized tool output to the token budget. |
| `src/agent.py` | **The loop.** `answer_question()` orchestrates think → act → observe with a step cap. |
| `src/cli.py` | Interactive command line. |
| `src/app.py` | Flask demo UI (answer + the SQL the agent ran + the result table). |
| `evals/` | Dataset (50 easy + 30 hard, verified) + runner scoring execution accuracy. |

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

Copy the env template and add your key:

```bash
cp .env.example .env   # then set OPENAI_API_KEY
```

## Run it

```bash
python -m src.app        # Flask web demo  → http://127.0.0.1:5000
python -m src.cli        # interactive terminal
python -m pytest         # run the test suite (uses a fake LLM — no API calls)

# eval harness (live model; costs tokens). Pick a tier to control cost:
python -m evals.runner        # hard tier only  (30 cases)
python -m evals.runner easy   # easy tier only  (50 cases)
python -m evals.runner all    # both            (80 cases)
```

For questions to try — from simple counts to multi-join, nested-aggregate, and
revenue questions — see the 80 cases in [`evals/dataset.py`](evals/dataset.py)
(`EVAL_CASES` = easy tier, `HARD_CASES` = hard tier). A few to start:

- `How many tracks are there?`
- `Which 5 genres have the most tracks?`
- `Who are the top 3 customers by total spend?`
- `Which genre generates the most revenue?`

In the CLI and web UI, watch the **SQL the agent ran** — if a query errors, you'll
often see the agent run a corrected query right after. That's self-correction.

## Testing

The logic-heavy modules are test-driven (`db` safety, the `tools` dispatcher, the
`agent` loop, the eval scorer). The agent loop is tested with a **fake LLM** — a
scripted stand-in injected via the `call_model` parameter — so tests are
deterministic, instant, and free. The real API is never called in unit tests.

```bash
python -m pytest -v
```

## How it works

See `docs/superpowers/specs/` for the design and `docs/superpowers/plans/` for the
step-by-step build. (Both are local-only / gitignored.)

## Possible next steps

- Summarize (instead of truncate) large tool results.
- Add query-timeout protection for runaway queries.
- Report eval scores as an average over N runs (acknowledge model stochasticity).
- Run the harness on the Spider/BIRD benchmark for a comparable, external number.
