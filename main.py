from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from fetcher import fetch_all_news
from analyzer import analyze_article
from cache import get as cache_get, set as cache_set

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "NSE Pulse API is running"}

@app.get("/news")
async def get_news(refresh: bool = False):
    if not refresh:
        cached = cache_get("feed")
        if cached:
            return cached

    articles = fetch_all_news(max_per_feed=10)

    async def enrich(article):
        try:
            analysis = await analyze_article(article["title"], article["summary"])
            return {**article, **analysis}
        except Exception as e:
            print(f"Analysis failed: {e}")
            return {
                **article,
                "sector": "Other",
                "sentiment": "Neutral",
                "score": 0,
                "reason": "Could not analyze.",
                "affected_stocks": [],
                "is_market_moving": False
            }

    results = await asyncio.gather(*[enrich(a) for a in articles[:25]])

    # Only keep news that actually impacts the market
    market_moving = [r for r in results if r.get("is_market_moving") == True]

    # If AI filtered too aggressively, fall back to all news
    final = market_moving if len(market_moving) >= 5 else list(results)

    # Sort by absolute score so strongest impact appears first
    final = sorted(final, key=lambda x: abs(x.get("score", 0)), reverse=True)

    cache_set("feed", final)
    return final
