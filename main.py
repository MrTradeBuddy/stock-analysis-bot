from fastapi import FastAPI, Request
import uvicorn
import requests
import pandas as pd

app = FastAPI()

# Telegram Bot Setup
BOT_TOKEN = '7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8'
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Upstox API V2 Token
UPSTOX_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI1WEI3RkQiLCJqdGkiOiI2ODA3NjZiZjQyMzI3ZjQ4MzBiZjc0MzQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzQ1MzE1NTE5LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDUzNTkyMDB9.6tiVcaXqfQyyjGORwZEphepH6GSOaNKPkTikdU3x1Fk"

# Strong Signal Check (Upstox API V2)
def analyze_stock(symbol):
    try:
        url = f"https://api.upstox.com/v2/market-quote/ltp?symbol=NSE_EQ%7C{symbol.upper()}"
        headers = {
            "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        ltp = data['data'][f'NSE_EQ|{symbol.upper()}']['last_price']

        # Mock logic for now
        signal = {
            "type": "Buy" if ltp % 2 == 0 else "Sell",
            "entry": round(ltp - 10, 2),
            "cmp": ltp,
            "targets": f"{round(ltp + 10, 2)} / {round(ltp + 20, 2)} / {round(ltp + 30, 2)}",
            "sl": round(ltp - 20, 2),
            "rsi": 28.3,
            "macd": "Bullish",
            "volume": "High",
            "supertrend": "Bullish",
            "bb": "Near Lower Band"
        }
        return signal
    except Exception as e:
        print("Error:", e)
        return None

# Top Movers Command Logic (Dummy Scan)
def get_top_movers():
    movers = [
        {"symbol": "TATAMOTORS", "rsi": 28, "supertrend": "Bullish"},
        {"symbol": "ICICIBANK", "rsi": 76, "supertrend": "Bearish"},
        {"symbol": "RELIANCE", "rsi": 31, "supertrend": "Bullish"}
    ]

    buy_zone = []
    sell_zone = []

    for stock in movers:
        if stock['rsi'] < 30 and stock['supertrend'] == "Bullish":
            buy_zone.append(f"🟢 {stock['symbol']} (RSI: {stock['rsi']}, ST: {stock['supertrend']})")
        elif stock['rsi'] > 70 and stock['supertrend'] == "Bearish":
            sell_zone.append(f"🔴 {stock['symbol']} (RSI: {stock['rsi']}, ST: {stock['supertrend']})")

    reply = "\ud83d\udd39 Top Movers\n\n"
    if buy_zone:
        reply += "\ud83d\udcc8 Buy Zone:\n" + "\n".join(buy_zone) + "\n\n"
    if sell_zone:
        reply += "\ud83d\udd27 Sell Zone:\n" + "\n".join(sell_zone)
    if not buy_zone and not sell_zone:
        reply += "No strong movers right now."

    return reply

@app.post("/")
async def webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if text.startswith("/stock"):
        query = text.split(" ", 1)[-1].strip().lower()
        signal = analyze_stock(query)

        if signal:
            reply = f"\ud83d\udcc8 {query.upper()} Signal:\n\n"
            reply += f"Type: {signal['type']}\n"
            reply += f"CMP: {signal['cmp']}\n"
            reply += f"Entry: {signal['entry']}\n"
            reply += f"Targets: {signal['targets']}\n"
            reply += f"Stop Loss: {signal['sl']}\n"
            reply += f"\nIndicators:\n"
            reply += f"RSI: {signal['rsi']}\n"
            reply += f"MACD: {signal['macd']}\n"
            reply += f"Supertrend: {signal['supertrend']}\n"
            reply += f"BB: {signal['bb']}\n"
            reply += f"Volume: {signal['volume']}\n"
        else:
            reply = "\u274c Stock data not found or error in signal analysis."

    elif text.startswith("/topmovers"):
        reply = get_top_movers()

    else:
        reply = "\ud83d\udd0e Use /stock <symbol> or /topmovers"

    requests.post(API_URL, json={
        "chat_id": chat_id,
        "text": reply
    })

    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
