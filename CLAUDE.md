# Project Rules — SQL Analytics Agent

## Prime directive
This is a LEARNING project. Optimize for understanding, not speed. A working
feature with no understanding is a failure here.

## How to work in this repo
- For every non-trivial change, explain: (1) WHY this approach, (2) WHY NOT the
  obvious alternative, (3) a reference to read. Keep it to a few sentences.
- Teach Python idioms inline when you use them — the author is strong in
  JS/TypeScript but newer to Python.
- Keep modules small and single-purpose (see the file structure in the plan).
  If a file starts doing two jobs, split it.

## Hard technical rules
- NO agent framework (LangChain, CrewAI, LlamaIndex agents, etc.). The agent
  loop is hand-written on purpose — that is the whole point.
- The database is READ-ONLY. The agent may only run SELECT queries. Enforce this
  in , never trust the model.
- All OpenAI access goes through . No other file imports .
- TDD: failing test → watch it fail → minimal code → watch it pass. The agent
  loop is tested with a FAKE LLM; never call the real API inside unit tests.
- Secrets live in  (gitignored). Never hardcode an API key.

## Git
- Claude must NOT run git add/commit/push. The human runs all commits as
  checkpoints. Claude may run read-only git (status, diff, log).

## Definition of done for a task
Tests pass (============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/musyoka/personal/myProject/frank/sql-analytics-agent
plugins: anyio-4.13.0
collected 0 items

============================ no tests ran in 0.03s =============================), the human understands why it works, and the
why this / why not was explained.
