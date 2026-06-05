import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "chinook.db"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
# 0 = deterministic. We want consistent, reproducible SQL (and eval runs), not
# creative sampling, so default to 0. Override via .env if you ever want variety.
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0"))

MAX_RESULT_ROWS = 100
MAX_AGENT_STEPS = 8
MAX_TOOL_RESULT_CHARS = 4000