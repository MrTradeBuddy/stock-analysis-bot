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

# ✅ Live NSE Symbol Cache
VALID_SYMBOLS = set()

def fetch_valid_symbols():
    try:
        url = "https://assets.upstox.com/market-quote/symbols.csv"
        df = pd.read_csv(url)
        df = df[df['exchange'] == 'NSE_EQ']
        symbols = df['symbol'].str.upper().tolist()
        stripped = [s.split('|')[-1] for s in symbols]
        VALID_SYMBOLS.update(stripped)
        print(f"✅ Loaded {len(VALID_SYMBOLS)} symbols from Upstox")
    except Exception as e:
        print("Error loading symbols:", e)

fetch_valid_symbols()

# Symbol alias/fallback list
SYMBOL_FIX = {
    "tata": "TATAMOTORS",
    "icici": "ICICIBANK",
    "reliance": "RELIANCE",
    "hdfc": "HDFCBANK",
    "kotak": "KOTAKBANK",
    "jsw": "JSWSTEEL"
}

# Strong Signal Check (Upstox API V2)
def analyze_stock(symbol):
    try:
        url = f"https://api.upstox.com/v2/market-quote/ltp?symbol=NSE_EQ%7C{symbol.upper()}"
        headers = {
            "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        print("DEBUG URL:", url)
        print("DEBUG STATUS:", response.status_code)
        print("DEBUG RESPONSE:", data)

        key = f'NSE_EQ|{symbol.upper()}'
        if key in data['data']:
            ltp = data['data'][key]['last_price']
        else:
            print("DEBUG: Symbol not found in response")
            return None

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

    reply = "📉 Top Movers\n\n"
    if buy_zone:
        reply += "📈 Buy Zone:\n" + "\n".join(buy_zone) + "\n\n"
    if sell_zone:
        reply += "🔧 Sell Zone:\n" + "\n".join(sell_zone)
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
        fixed_symbol = SYMBOL_FIX.get(query, query).upper()

        if fixed_symbol not in VALID_SYMBOLS:
            reply = f"❌ Symbol '{fixed_symbol}' not found in NSE database."
        else:
            signal = analyze_stock(fixed_symbol)
            if signal:
                reply = f"📈 {fixed_symbol} Signal:\n\n"
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
                reply = "❌ Stock data not found or error in signal analysis."

    elif text.startswith("/topmovers"):
        reply = get_top_movers()

    else:
        reply = "🔎 Use /stock <symbol> or /topmovers"

    requests.post(API_URL, json={
        "chat_id": chat_id,
        "text": reply
    })

    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
