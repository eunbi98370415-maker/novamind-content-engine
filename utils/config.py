"""
NovaMind Configuration
Loads environment variables and exposes app-wide settings.
"""

import os
from dotenv import load_dotenv

# Load .env file if present (dev mode)
load_dotenv()

# App metadata
APP_NAME = "NovaMind"
APP_VERSION = "1.0.0"

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# LLM Provider — defaults to anthropic
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()

# Mock mode: True if no API key is configured for the selected provider
def _is_mock_mode() -> bool:
    if LLM_PROVIDER == "anthropic":
        return not bool(ANTHROPIC_API_KEY)
    elif LLM_PROVIDER == "openai":
        return not bool(OPENAI_API_KEY)
    return True

MOCK_MODE = _is_mock_mode()

# Paths relative to project root
import pathlib
PROJECT_ROOT = pathlib.Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EXPORTS_DIR = PROJECT_ROOT / "exports"
DB_PATH = PROJECT_ROOT / "novamind.db"
