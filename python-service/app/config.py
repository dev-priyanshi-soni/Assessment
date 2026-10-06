from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parents[1]
POLICY_PATH = BASE_DIR / "data" / "policies.json"
REQUEST_PATH = BASE_DIR / "data" / "requests"
MODEL_MODE = os.getenv("MODEL_MODE", "offline")
