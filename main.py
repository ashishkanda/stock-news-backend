
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
    return {"message": "NSE Pulse API is running ✅"}

@app.get("/news")
async def get_news():
    cached = cache_get("feed")
    if cached:
        return cached

    articles = fetch_all_news(max_per_feed=8)

    async def enrich(article):
        try:
            analysis = await analyze_article(article["title"], article["summary"])
            return {**article, **analysis}
        except Exception as e:
            print(f"Analysis failed for: {article['title'][:50]} — {e}")
            return {**article, "sector": "Other", "sentiment": "Neutral",
                    "score": 0, "reason": "Could not analyze.", "affected_stocks": []}

    results = await asyncio.gather(*[enrich(a) for a in articles[:20]])
    sorted_results = sorted(results, key=lambda x: abs(x.get("score", 0)), reverse=True)
    cache_set("feed", sorted_results)
    return sorted_results
