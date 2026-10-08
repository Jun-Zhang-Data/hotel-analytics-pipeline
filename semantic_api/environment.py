from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = ROOT / ".env"


def load_local_environment(path: str | Path = DEFAULT_ENV_PATH) -> bool:
    """Load local development settings without overriding real environment variables."""
    return load_dotenv(dotenv_path=Path(path), override=False)
