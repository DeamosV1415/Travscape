"""
Travscape Application Configuration.

Centralized settings for the FastAPI application.
"""

import os
from pathlib import Path


# ==================== PATHS ====================

# Project root directory (one level up from app/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Static files directory
STATIC_DIR = BASE_DIR / "static"


# ==================== SERVER ====================

HOST = os.getenv("TRAVSCAPE_HOST", "0.0.0.0")
PORT = int(os.getenv("TRAVSCAPE_PORT", "8000"))
DEBUG = os.getenv("TRAVSCAPE_DEBUG", "true").lower() == "true"


# ==================== API ====================

API_TITLE = "Travescape API"
API_DESCRIPTION = "AI-powered travel planning assistant"
API_VERSION = "1.0.0"

# CORS origins (comma-separated in env, defaults to allow all in dev)
CORS_ORIGINS = os.getenv("TRAVSCAPE_CORS_ORIGINS", "*").split(",")
