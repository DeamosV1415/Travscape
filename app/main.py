"""
Travscape FastAPI Application.

Production-grade FastAPI app that serves the static frontend
and exposes the AI chat API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import API_TITLE, API_DESCRIPTION, API_VERSION, CORS_ORIGINS, STATIC_DIR
from app.api.chat import router as chat_router
from app.api.news import router as news_router


# ==================== APP CREATION ====================

app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# ==================== MIDDLEWARE ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API ROUTES ====================

app.include_router(chat_router)
app.include_router(news_router)


# ==================== HEALTH CHECK ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "service": "travescape"}


# ==================== STATIC FILES ====================
# Mount static files LAST so API routes take priority.
# html=True enables serving index.html for directory paths
# (e.g., /chat/ serves static/chat/index.html)

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
