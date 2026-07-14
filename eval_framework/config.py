import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "llama-3.3-70b-versatile")

DB_PATH = str(BASE_DIR / "eval_history.sqlite3")
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

if not GROQ_API_KEY:
    raise EnvironmentError(
        "GROQ_API_KEY not found. Copy .env.example to .env and add your free key "
        "from https://console.groq.com/keys"
    )
