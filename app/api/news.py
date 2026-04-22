"""
News API endpoint — proxies GNews.io to keep API key server-side.
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import httpx
import os

router = APIRouter(prefix="/api/news", tags=["news"])

GNEWS_BASE = "https://gnews.io/api/v4"


@router.get("/travel")
async def get_travel_news(
    count: int = Query(default=9, ge=1, le=10),
):
    """
    Fetch latest travel news from GNews.io.
    Free tier: 100 requests/day.
    """
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key:
        return JSONResponse(
            status_code=500,
            content={"error": "GNEWS_API_KEY not configured"},
        )

    params = {
        "apikey": api_key,
        "q": "travel OR tourism OR destinations OR flights",
        "lang": "en",
        "max": count,
        "sortby": "publishedAt",
        "in": "title,description",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{GNEWS_BASE}/search", params=params)
            resp.raise_for_status()
            data = resp.json()

        articles = data.get("articles", [])

        # Return only what the frontend needs
        cleaned = []
        for art in articles:
            cleaned.append({
                "title": art.get("title", ""),
                "description": art.get("description", ""),
                "image": art.get("image", ""),
                "url": art.get("url", ""),
                "publishedAt": art.get("publishedAt", ""),
                "source": art.get("source", {}).get("name", "Unknown"),
            })

        return {"articles": cleaned}

    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=502,
            content={"error": f"GNews API error: {e.response.status_code}"},
        )
    except Exception as e:
        print(f"[News API] Error: {e}")
        return JSONResponse(
            status_code=502,
            content={"error": "Failed to fetch news"},
        )
