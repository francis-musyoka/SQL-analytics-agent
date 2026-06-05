import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "chinook.db"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")

# Sampling temperature. 0 = deterministic (consistent SQL + reproducible evals).
# Some models (e.g. the gpt-5 / reasoning family) reject any explicit temperature;
# set LLM_TEMPERATURE=default (or leave it blank) and we omit the parameter so
# the model uses its own default. We parse defensively so a stray/empty value in
# .env can never crash every module at import time.
_temp_raw = os.environ.get("LLM_TEMPERATURE", "0").strip().lower()
if _temp_raw in ("", "default", "none"):
    LLM_TEMPERATURE = None  # None => don't send a temperature at all
else:
    try:
        LLM_TEMPERATURE = float(_temp_raw)
    except ValueError:
        LLM_TEMPERATURE = 0.0

MAX_RESULT_ROWS = 100
MAX_AGENT_STEPS = 8
MAX_TOOL_RESULT_CHARS = 4000