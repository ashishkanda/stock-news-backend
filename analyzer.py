
import httpx
import json
import os

GEMINI_API_KEY = os.getenv("AIzaSyCKWSKFOPejIN1F16EH8A_5W57R6vrtfTg", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

SYSTEM_PROMPT = """You are a financial analyst for Indian stock markets (NSE, BSE, Nifty, Bank Nifty).

Given a news headline and summary, respond ONLY with valid JSON, no extra text:
{
  "sector": "<Banking | IT | Oil & Gas | Pharma | Auto | FMCG | Metal | Realty | Telecom | Power | Market-Wide | Other>",
  "sentiment": "<Bullish | Bearish | Neutral>",
  "score": <integer -10 to +10>,
  "reason": "<one sentence explaining market impact>",
  "affected_stocks": ["<company or NSE ticker>"]
}

Score guide: +8/+10 = very bullish, +4/+7 = moderately bullish, 0 = neutral, -4/-7 = moderately bearish, -8/-10 = very bearish."""

async def analyze_article(title, summary):
    prompt = f"Headline: {title}\nSummary: {summary}"

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 250}
            }
        )
        response.raise_for_status()
        data = response.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)
