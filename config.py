import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Assistant Identity & Butler Persona
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "JARVIS")
USER_NAME = os.getenv("USER_NAME", "Sir")

# Voice Configuration
# Online voice: High quality British Butler (RyanNeural)
TTS_VOICE = os.getenv("TTS_VOICE", "en-GB-RyanNeural")
TTS_RATE = os.getenv("TTS_RATE", "+0%")
TTS_PITCH = os.getenv("TTS_PITCH", "+0Hz")

# Voice Conversation & Biometric Settings
VOICE_PAUSE_THRESHOLD = float(os.getenv("VOICE_PAUSE_THRESHOLD", "2.2")) # Seconds of silence before concluding utterance
VOICE_PHRASE_TIME_LIMIT = float(os.getenv("VOICE_PHRASE_TIME_LIMIT", "35.0"))
VOICE_CONVERSATION_IDLE_TIMEOUT = float(os.getenv("VOICE_CONVERSATION_IDLE_TIMEOUT", "12.0"))
VOICE_VERIFICATION_ENABLED = os.getenv("VOICE_VERIFICATION_ENABLED", "true").lower() in ("true", "1", "yes")
VOICE_PROFILE_TOLERANCE = float(os.getenv("VOICE_PROFILE_TOLERANCE", "0.50"))
FORCE_OFFLINE_STT = os.getenv("FORCE_OFFLINE_STT", "false").lower() in ("true", "1", "yes")

# Proactive Butler & Protocol Sunrise Settings
SUNRISE_ENABLED = os.getenv("SUNRISE_ENABLED", "true").lower() in ("true", "1", "yes")
SUNRISE_TIME = os.getenv("SUNRISE_TIME", "08:00")

# Network & Port Settings
WEB_PORTAL_PORT = int(os.getenv("WEB_PORTAL_PORT", "5050"))
OMNIROUTE_PORT = int(os.getenv("OMNIROUTE_PORT", "20128"))
OMNIROUTE_BASE_URL = os.getenv("OMNIROUTE_BASE_URL", f"http://localhost:{OMNIROUTE_PORT}/v1")
OMNIROUTE_MODEL = os.getenv("OMNIROUTE_MODEL", "ddgw/mistral-small-2603")

# API Keys
OMNIROUTE_API_KEY = os.getenv("OMNIROUTE_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Directory Paths
ASSETS_DIR = BASE_DIR / "assets"
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs"

# Database Paths
MEMORY_DB_PATH = MEMORY_DIR / "jarvis_memory.db"
SCHEDULE_DB_PATH = MEMORY_DIR / "schedule.db"
TASKS_DB_PATH = MEMORY_DIR / "tasks.db"
PENDING_TASKS_SYNC_PATH = MEMORY_DIR / "pending_tasks.json"
COMPLETED_TASKS_DIR = BASE_DIR / "data" / "completed_tasks"

# Assets
IRONMAN_ICO_PATH = ASSETS_DIR / "ironman.ico"

# Autonomy, Away Mode & Off-Grid Settings
AWAY_MODE_ENABLED = os.getenv("AWAY_MODE_ENABLED", "true").lower() in ("true", "1", "yes")
OFFGRID_SYNC_ENABLED = os.getenv("OFFGRID_SYNC_ENABLED", "true").lower() in ("true", "1", "yes")

# Ensure runtime directories exist
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
COMPLETED_TASKS_DIR.mkdir(parents=True, exist_ok=True)

# HUD Settings
HUD_WINDOW_TITLE = "J.A.R.V.I.S. // STARK INDUSTRIES TACTICAL HUD"
HUD_ALWAYS_ON = os.getenv("HUD_ALWAYS_ON", "true").lower() in ("true", "1", "yes")

# Campaign & Business Language Settings (Strictly English Only)
CAMPAIGN_LANGUAGE = os.getenv("CAMPAIGN_LANGUAGE", "English")
CAMPAIGN_ENGLISH_ONLY = os.getenv("CAMPAIGN_ENGLISH_ONLY", "true").lower() in ("true", "1", "yes")

