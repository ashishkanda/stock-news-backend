
import feedparser
import hashlib

RSS_FEEDS = {
    "moneycontrol": "https://www.moneycontrol.com/rss/latestnews.xml",
    "economic_times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "google_nse": "https://news.google.com/rss/search?q=NSE+Nifty+Indian+stocks&hl=en-IN&gl=IN&ceid=IN:en",
    "google_banknifty": "https://news.google.com/rss/search?q=Bank+Nifty+BSE+India&hl=en-IN&gl=IN&ceid=IN:en",
}

def fetch_all_news(max_per_feed=8):
    articles = []
    seen = set()

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "").strip()
                if not title:
                    continue
                h = hashlib.md5(title.lower().encode()).hexdigest()
                if h in seen:
                    continue
                seen.add(h)
                articles.append({
                    "id": h,
                    "title": title,
                    "summary": entry.get("summary", "")[:400],
                    "url": entry.get("link", ""),
                    "source": source,
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            print(f"Error fetching {source}: {e}")

    return articles
