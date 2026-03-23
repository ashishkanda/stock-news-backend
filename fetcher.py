import feedparser
import hashlib
import re
from datetime import datetime, timezone, timedelta
import email.utils

RSS_FEEDS = {
    "economic_times_markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "economic_times_economy": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
    "business_standard": "https://www.business-standard.com/rss/markets-106.rss",
    "livemint": "https://www.livemint.com/rss/markets",
    "google_rbi_policy": "https://news.google.com/rss/search?q=RBI+India+policy+interest+rate&hl=en-IN&gl=IN&ceid=IN:en",
    "google_nifty": "https://news.google.com/rss/search?q=Nifty+NSE+BSE+India+market+crash+rally&hl=en-IN&gl=IN&ceid=IN:en",
    "google_earnings": "https://news.google.com/rss/search?q=India+quarterly+results+earnings+profit+loss+NSE&hl=en-IN&gl=IN&ceid=IN:en",
    "google_economy": "https://news.google.com/rss/search?q=India+GDP+inflation+rupee+dollar+economy&hl=en-IN&gl=IN&ceid=IN:en",
}

JUNK_PATTERNS = [
    r"target of rs", r"target price", r"buy .{1,30}; target",
    r"sell .{1,30}; target", r"reduce .{1,30}; target",
    r"accumulate .{1,30}; target", r"hold .{1,30}; target",
    r"initiates coverage", r"price objective", r"raises target",
    r"cuts target", r"brokerage", r"emkay", r"icici securities",
    r"kr choksey", r"motilal oswal initiates",
]

def is_junk(title):
    t = title.lower()
    return any(re.search(p, t) for p in JUNK_PATTERNS)

def parse_date(entry):
    # Try to parse the published date from RSS entry
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        if hasattr(entry, 'published') and entry.published:
            parsed = email.utils.parsedate_to_datetime(entry.published)
            return parsed.astimezone(timezone.utc)
    except Exception:
        pass
    return datetime.now(timezone.utc)

def fetch_all_news(max_per_feed=12, days_back=3):
    articles = []
    seen = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if count >= max_per_feed:
                    break

                title = entry.get("title", "").strip()
                if not title or is_junk(title):
                    continue

                h = hashlib.md5(title.lower().encode()).hexdigest()
                if h in seen:
                    continue
                seen.add(h)

                pub_date = parse_date(entry)

                # Skip news older than days_back
                if pub_date < cutoff:
                    continue

                articles.append({
                    "id": h,
                    "title": title,
                    "summary": entry.get("summary", "")[:500],
                    "url": entry.get("link", ""),
                    "source": source,
                    "published": pub_date.isoformat(),
                    "published_date": pub_date.strftime("%Y-%m-%d"),
                    "published_ts": pub_date.timestamp(),
                })
                count += 1

        except Exception as e:
            print(f"Error fetching {source}: {e}")

    print(f"Total articles fetched: {len(articles)}")
    return articles
