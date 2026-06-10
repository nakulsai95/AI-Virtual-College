"""Runtime configuration loaded from the environment (.env supported)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Where the active connector config is persisted between restarts (dev only).
# Holds the user's selected provider + API key, so it lives OUTSIDE git.
CONNECTOR_STORE = BASE_DIR / ".connectors.json"


def cors_origins() -> list[str]:
    default = ",".join(
        f"http://{host}:{port}"
        for host in ("localhost", "127.0.0.1")
        for port in (5173, 5500, 8080, 3000, 4000)
    )
    raw = os.getenv("AULA_CORS_ORIGINS", default)
    return [o.strip() for o in raw.split(",") if o.strip()]


# Standard vendor key names → provider id, so a plain `OPENAI_API_KEY=...`
# in .env goes live without any extra AULA_* config.
_VENDOR_KEYS = [
    ("AULA_API_KEY", None),  # explicit AULA config wins (uses AULA_PROVIDER)
    ("ANTHROPIC_API_KEY", "claude"),
    ("OPENAI_API_KEY", "openai"),
    ("GEMINI_API_KEY", "gemini"),
    ("GOOGLE_API_KEY", "gemini"),
    ("MISTRAL_API_KEY", "mistral"),
    ("GROQ_API_KEY", "groq"),
]


def seed_connector() -> dict | None:
    """Optional connector pre-seeded from env, so the app can run without the UI.

    Either set AULA_PROVIDER + AULA_API_KEY, or just drop a standard vendor
    key (e.g. OPENAI_API_KEY / ANTHROPIC_API_KEY) into .env.
    """
    provider = os.getenv("AULA_PROVIDER", "")
    api_key = os.getenv("AULA_API_KEY", "")
    if not provider:
        for env_name, pid in _VENDOR_KEYS:
            value = os.getenv(env_name, "")
            if value and pid:
                provider, api_key = pid, value
                break
    if not provider:
        return None
    return {
        "provider": provider,
        "api_key": api_key,
        "model": os.getenv("AULA_MODEL", ""),
        "base_url": os.getenv("AULA_OLLAMA_BASE_URL", "") if provider == "ollama" else "",
    }
