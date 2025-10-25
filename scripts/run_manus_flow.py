import asyncio
import re
import os
from agents.dedalus_orchestrator import StockAnalysisAgent
from agents.manus_browser import ManusBrowser


async def main():
    prompt = (
        "Find stocks at 52-week lows with debt conversions from last week "
        "between October 13th, 2025 through October 17th, 2025"
    )

    agent = StockAnalysisAgent()
    browser = ManusBrowser()

    print("Running initial agent search...")
    try:
        resp = await agent.chat(prompt)
    except Exception as e:
        print("Agent.chat failed:", e)
        return

    print("\n=== Agent initial output ===")
    print(resp)

    # Try to extract ticker-like tokens (simple heuristic)
    tickers = set(re.findall(r"\b[A-Z]{1,5}\b", resp))
    # remove common words that are all-caps
    filtered = [t for t in tickers if t not in {"USD", "CEO", "IPO", "WWW"}]
    tickers = list(filtered)[:8]

    if not tickers:
        print("No tickers detected in the agent output. Asking agent for a concise list...")
        try:
            tickers_text = await agent.chat("From your previous analysis, list only the ticker symbols you identified, comma-separated.")
            tickers = [t.strip().upper() for t in re.split('[,\n]', tickers_text) if t.strip()]
        except Exception as e:
            print("Failed to get tickers from agent:", e)
            return

    print("\nTickers to investigate:", tickers)

    results = {}
    for t in tickers:
        print(f"\nQuerying Manus for debt conversion info for {t}...")
        try:
            # Use Manus to search financial news for debt conversion price in the date range
            topic = "debt conversion price Oct 13 2025 through Oct 17 2025"
            mresp = await browser.search_financial_news(t, topic)
            print("Manus response:")
            print(mresp)
            results[t] = {"manus_text": mresp}
        except Exception as e:
            print(f"Manus query failed for {t}:", e)
            results[t] = {"manus_text": None, "error": str(e)}

    # For each ticker, ask the agent to recommend option strikes using the conversion price
    print("\nAsking the agent for option strike recommendations based on Manus findings...")
    for t, info in results.items():
        manus_text = info.get("manus_text") or "No conversion price found"
        ask = (
            f"For ticker {t}, I have this note about a debt conversion price from Manus: {manus_text}. "
            "Assuming the stock is at a 52-week low, recommend 2 option strikes to BUY (include expiration in days, strike price, option type), "
            "give rationale relative to the conversion price and the 52-week low momentum, and suggest a notional sizing percent. "
            "Return a brief structured answer."
        )
        try:
            rec = await agent.chat(ask)
            print(f"\nRecommendations for {t}:")
            print(rec)
        except Exception as e:
            print(f"Agent recommendation failed for {t}:", e)


if __name__ == "__main__":
    asyncio.run(main())
