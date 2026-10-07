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

# Assets
IRONMAN_ICO_PATH = ASSETS_DIR / "ironman.ico"

# Ensure runtime directories exist
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# HUD Settings
HUD_WINDOW_TITLE = "J.A.R.V.I.S. // STARK INDUSTRIES TACTICAL HUD"
