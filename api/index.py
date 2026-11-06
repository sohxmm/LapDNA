"""Vercel ASGI entrypoint; no ingestion or synthetic data on API paths."""

import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "services" / "api" / "src"))

from lapdna.main import create_app

app = create_app()
