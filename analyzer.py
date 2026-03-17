import httpx
import json
import os

GEMINI_API_KEY = os.getenv("AIzaSyCKWSKFOPejIN1F16EH8A_5W57R6vrtfTg", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

SYSTEM_PROMPT = """You are a senior stock market analyst specializing in Indian markets — NSE, BSE, Nifty 50, Bank Nifty.

Your job is to read a news headline and summary, then decide if it will move the Indian stock market.

You MUST respond with ONLY a valid JSON object. No explanation. No markdown. No extra text. Just raw JSON.

Use EXACTLY these sector names (copy exactly, no variations):
- Banking
- IT
- Oil & Gas
- Pharma
- Auto
- FMCG
- Metal
- Realty
- Telecom
- Power
- Market-Wide
- Other

Respond in this exact format:
{
  "sector": "<exact sector name from list above>",
  "sentiment": "<Bullish or Bearish or Neutral>",
  "score": <integer from -10 to +10>,
  "reason": "<one clear sentence about why this moves the market>",
  "affected_stocks": ["<NSE stock symbol or company name>", "<another if relevant>"],
  "is_market_moving": <true or false>
}

Scoring rules:
+9 to +10 = massive positive shock (rate cut, huge policy boost, major earnings beat)
+6 to +8  = strong positive (sector tailwind, good quarterly results)
+3 to +5  = mild positive (minor good news)
+1 to +2  = slightly positive
0         = no real market impact
-1 to -2  = slightly negative
-3 to -5  = mild negative (cost pressure, minor regulatory issue)
-6 to -8  = strong negative (rate hike, earnings miss, sector headwind)
-9 to -10 = massive negative shock (crisis, fraud, major ban)

Set is_market_moving to true only if score is >= 3 or <= -3 AND the news directly affects Indian stocks.
Set is_market_moving to false for general world news, sports, entertainment, or politics with no market link.

For affected_stocks, use NSE symbols where possible:
Banking → HDFCBANK, ICICIBANK, SBIN, KOTAKBANK, AXISBANK
IT → TCS, INFY, WIPRO, HCLTECH, TECHM
Oil & Gas → RELIANCE, ONGC, IOC, BPCL, GAIL
Pharma → SUNPHARMA, DRREDDY, CIPLA, DIVISLAB, APOLLOHOSP
Auto → TATAMOTORS, MARUTI, M&M, BAJAJ-AUTO, EICHERMOT
FMCG → HINDUNILVR, ITC, NESTLEIND, BRITANNIA, DABUR
Metal → TATASTEEL, JSWSTEEL, HINDALCO, VEDL, COALINDIA
Realty → DLF, GODREJPROP, OBEROIRLTY, PRESTIGE
Telecom → BHARTIARTL, IDEA, INDUSTOWER
Power → NTPC, POWERGRID, ADANIPOWER, TATAPOWER"""

async def analyze_article(title, summary):
    prompt = f"Headline: {title}\nSummary: {summary if summary else 'No summary available'}"

    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 300
                }
            }
        )
        response.raise_for_status()
        data = response.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        raw = raw.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)

        # Force sector to exactly match one of our allowed values
        allowed_sectors = [
            "Banking", "IT", "Oil & Gas", "Pharma", "Auto",
            "FMCG", "Metal", "Realty", "Telecom", "Power",
            "Market-Wide", "Other"
        ]
        if result.get("sector") not in allowed_sectors:
            result["sector"] = "Other"

        return result
