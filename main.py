from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import sys
import os
from datetime import datetime, timezone

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

@app.get("/debug")
async def debug():
    try:
        result = await analyze_article(
            "RBI cuts repo rate by 25 basis points to boost economy",
            "The Reserve Bank of India reduced the repo rate in its latest monetary policy meeting."
        )
        return {"status": "Gemini working", "result": result}
    except Exception as e:
        return {"status": "Gemini FAILED", "error": str(e)}

@app.get("/news")
async def get_news(
    refresh: bool = False,
    date: str = Query(default=None, description="Filter by date YYYY-MM-DD")
):
    cache_key = f"feed_{date or 'all'}"

    if not refresh:
        cached = cache_get(cache_key)
        if cached:
            return cached

    # Fetch fewer articles to prevent Render from timing out
    articles = fetch_all_news(max_per_feed=3, days_back=1)

    async def enrich(article):
        try:
            analysis = await analyze_article(article["title"], article["summary"])
            return {**article, **analysis}
        except Exception as e:
            print(f"Analysis failed for '{article['title'][:50]}': {e}")
            return {
                **article,
                "sector": "Other",
                "sentiment": "Neutral",
                "score": 0,
                "reason": "Analysis unavailable.",
                "affected_stocks": [],
                "is_market_moving": False
            }

    results = []
    batch_size = 5
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        batch_results = await asyncio.gather(*[enrich(a) for a in batch])
        results.extend(batch_results)
        if i + batch_size < len(articles):
            await asyncio.sleep(1)

    if date:
        results = [r for r in results if r.get("published_date") == date]

    results = sorted(results, key=lambda x: (
        x.get("published_ts", 0),
        abs(x.get("score", 0))
    ), reverse=True)

    cache_set(cache_key, results)
    return results

@app.get("/dates")
def get_available_dates():
    from datetime import timedelta
    today = datetime.now(timezone.utc)
    dates = []
    for i in range(3):
        d = today - timedelta(days=i)
        dates.append({
            "value": d.strftime("%Y-%m-%d"),
            "label": "Today" if i == 0 else ("Yesterday" if i == 1 else d.strftime("%d %b %Y"))
        })
    return dates
