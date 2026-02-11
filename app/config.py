import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "maleon")
CACHE_FILE = "cache_inteligente.json"

BLACKLIST = ["clima", "tiempo", "hora", "hoy", "ayer", "mañana"]
