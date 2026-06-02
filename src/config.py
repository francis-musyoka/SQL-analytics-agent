import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "chinook.db"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")

MAX_RESULT_ROWS = 100
MAX_AGENT_STEPS = 8
MAX_TOOL_RESULT_CHARS = 4000