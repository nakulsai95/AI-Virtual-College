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


def seed_connector() -> dict | None:
    """Optional connector pre-seeded from env, so the app can run without the UI."""
    provider = os.getenv("AULA_PROVIDER")
    if not provider:
        return None
    return {
        "provider": provider,
        "api_key": os.getenv("AULA_API_KEY", ""),
        "model": os.getenv("AULA_MODEL", ""),
        "base_url": os.getenv("AULA_OLLAMA_BASE_URL", "") if provider == "ollama" else "",
    }
