import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Suppress Windows GP fault error boxes (SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX)
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002 | 0x8000)
    except Exception:
        pass

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

def _safe_int(env_name: str, default: int) -> int:
    val = os.getenv(env_name, "")
    try:
        return int(val) if val.strip() else default
    except Exception:
        return default

def _safe_float(env_name: str, default: float) -> float:
    val = os.getenv(env_name, "")
    try:
        return float(val) if val.strip() else default
    except Exception:
        return default

# Voice Conversation & Biometric Settings
VOICE_PAUSE_THRESHOLD = _safe_float("VOICE_PAUSE_THRESHOLD", 2.0) # Seconds of silence before concluding utterance
VOICE_PHRASE_TIME_LIMIT = _safe_float("VOICE_PHRASE_TIME_LIMIT", 35.0)
VOICE_CONVERSATION_IDLE_TIMEOUT = _safe_float("VOICE_CONVERSATION_IDLE_TIMEOUT", 12.0)
VOICE_VERIFICATION_ENABLED = os.getenv("VOICE_VERIFICATION_ENABLED", "true").lower() in ("true", "1", "yes")
VOICE_PROFILE_TOLERANCE = _safe_float("VOICE_PROFILE_TOLERANCE", 0.35) # Permissive adaptive tolerance
FORCE_OFFLINE_STT = os.getenv("FORCE_OFFLINE_STT", "false").lower() in ("true", "1", "yes")

# Proactive Butler, Notification & Protocol Sunrise Settings
SUNRISE_ENABLED = os.getenv("SUNRISE_ENABLED", "true").lower() in ("true", "1", "yes")
SUNRISE_TIME = os.getenv("SUNRISE_TIME", "08:00")
UNPROMPTED_NOTIFICATIONS_ENABLED = os.getenv("UNPROMPTED_NOTIFICATIONS_ENABLED", "false").lower() in ("true", "1", "yes")
DISPLAY_GREETINGS_VOCAL = os.getenv("DISPLAY_GREETINGS_VOCAL", "false").lower() in ("true", "1", "yes")
NOTIFY_ONLY_ONCE = True

# Network & Port Settings
WEB_PORTAL_PORT = _safe_int("WEB_PORTAL_PORT", 5050)
WEB_PORTAL_WS_PORT = _safe_int("WEB_PORTAL_WS_PORT", 5051)
OMNIROUTE_PORT = _safe_int("OMNIROUTE_PORT", 20128)
OMNIROUTE_BASE_URL = os.getenv("OMNIROUTE_BASE_URL", f"http://localhost:{OMNIROUTE_PORT}/v1")
OMNIROUTE_MODEL = os.getenv("OMNIROUTE_MODEL", "auto/best-fast")

# API Keys
OMNIROUTE_API_KEY = os.getenv("OMNIROUTE_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", os.getenv("HF_TOKEN", ""))

# Directory Paths
ASSETS_DIR = BASE_DIR / "assets"
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

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

# Security Sentinel & Device Access Settings
DEVICE_UNLOCK_PIN = os.getenv("DEVICE_UNLOCK_PIN", "")

# Ensure runtime directories exist
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
COMPLETED_TASKS_DIR.mkdir(parents=True, exist_ok=True)

# HUD & Projector Settings
HUD_WINDOW_TITLE = "J.A.R.V.I.S. // STARK INDUSTRIES TACTICAL HUD"
HUD_ALWAYS_ON = os.getenv("HUD_ALWAYS_ON", "true").lower() in ("true", "1", "yes")
PROJECTOR_WINDOW_TITLE = "J.A.R.V.I.S. // 3D HOLOGRAPHIC PROJECTOR SYSTEM"

# Campaign & Business Language Settings (Strictly English Only)
CAMPAIGN_LANGUAGE = os.getenv("CAMPAIGN_LANGUAGE", "English")
CAMPAIGN_ENGLISH_ONLY = os.getenv("CAMPAIGN_ENGLISH_ONLY", "true").lower() in ("true", "1", "yes")

