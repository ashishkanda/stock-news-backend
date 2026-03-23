import httpx
import json
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

SYSTEM_PROMPT = """You are a senior Indian stock market analyst. Analyze news for NSE/BSE impact.

CRITICAL: Respond with ONLY a JSON object. No markdown. No backticks. No explanation. Raw JSON only.

Required format:
{"sector":"Banking","sentiment":"Bullish","score":7,"reason":"RBI rate cut boosts lending margins for banks","affected_stocks":["HDFCBANK","ICICIBANK","SBIN"],"is_market_moving":true}

SECTOR must be exactly one of: Banking, IT, Oil & Gas, Pharma, Auto, FMCG, Metal, Realty, Telecom, Power, Market-Wide, Other

SCORE rules:
+9,+10 = massive positive (RBI rate cut, huge policy boost, major earnings beat)
+6,+7,+8 = strong positive (sector tailwind, good results, positive policy)
+3,+4,+5 = moderate positive
+1,+2 = mild positive
0 = no market impact
-1,-2 = mild negative
-3,-4,-5 = moderate negative
-6,-7,-8 = strong negative (rate hike, earnings miss, regulatory action)
-9,-10 = crisis level negative (fraud, major ban, crash)

SENTIMENT: Bullish if score > 0, Bearish if score < 0, Neutral if score = 0

is_market_moving: true if abs(score) >= 3, false otherwise

AFFECTED_STOCKS: Use real NSE symbols:
Banking: HDFCBANK,ICICIBANK,SBIN,KOTAKBANK,AXISBANK,INDUSINDBK,BANDHANBNK
IT: TCS,INFY,WIPRO,HCLTECH,TECHM,LTIM,PERSISTENT
Oil & Gas: RELIANCE,ONGC,IOC,BPCL,GAIL,OIL,MGL
Pharma: SUNPHARMA,DRREDDY,CIPLA,DIVISLAB,APOLLOHOSP,AUROPHARMA
Auto: TATAMOTORS,MARUTI,M&M,BAJAJ-AUTO,EICHERMOT,HEROMOTOCO,ASHOKLEY
FMCG: HINDUNILVR,ITC,NESTLEIND,BRITANNIA,DABUR,MARICO,GODREJCP
Metal: TATASTEEL,JSWSTEEL,HINDALCO,VEDL,COALINDIA,NMDC,SAIL
Realty: DLF,GODREJPROP,OBEROIRLTY,PRESTIGE,PHOENIXLTD
Telecom: BHARTIARTL,IDEA,INDUSTOWER,TATACOMM
Power: NTPC,POWERGRID,ADANIPOWER,TATAPOWER,CESC"""

async def analyze_article(title, summary):
    prompt = f"News headline: {title}\nSummary: {summary if summary else 'Not available'}\n\nAnalyze this for Indian stock market impact. Return raw JSON only."

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT + "\n\n" + prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 400,
            "responseMimeType": "application/json"
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload
        )

        if response.status_code != 200:
            print(f"Gemini error {response.status_code}: {response.text[:200]}")
            raise Exception(f"Gemini API returned {response.status_code}")

        data = response.json()

        try:
            raw = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            print(f"Unexpected Gemini response structure: {data}")
            raise Exception(f"Could not parse Gemini response: {e}")

        # Clean up any markdown wrapping just in case
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        print(f"Gemini raw response: {raw[:100]}")

        result = json.loads(raw)

        # Validate and enforce sector names
        allowed_sectors = [
            "Banking", "IT", "Oil & Gas", "Pharma", "Auto",
            "FMCG", "Metal", "Realty", "Telecom", "Power",
            "Market-Wide", "Other"
        ]
        if result.get("sector") not in allowed_sectors:
            result["sector"] = "Other"

        # Enforce sentiment based on score
        score = int(result.get("score", 0))
        if score > 0:
            result["sentiment"] = "Bullish"
        elif score < 0:
            result["sentiment"] = "Bearish"
        else:
            result["sentiment"] = "Neutral"

        result["score"] = score
        result["is_market_moving"] = abs(score) >= 3

        return result
