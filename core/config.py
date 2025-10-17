import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
STUDENT_SECRET = os.getenv("STUDENT_SECRET")
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "./workspace")).resolve()
WORKSPACE_ROOT.mkdir(exist_ok=True)

PAGES_POLL_TIMEOUT = int(os.getenv("POLL_PAGES_TIMEOUT", "540"))
PAGES_POLL_INTERVAL = int(os.getenv("PAGES_POLL_INTERVAL", "3"))
