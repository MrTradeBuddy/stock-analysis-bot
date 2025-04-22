from fastapi import FastAPI, Request
import uvicorn
import requests

app = FastAPI()

BOT_TOKEN = '7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8'
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
UPSTOX_ACCESS_TOKEN = "YOUR_UPSTOX_ACCESS_TOKEN_HERE"

def fetch_upstox_data(symbol):
    try:
        symbol_code = f"NSE_EQ|{symbol.upper()}"
        url = f"https://api.upstox.com/v2/market-quote/ltp?symbol={symbol_code}"
        headers = {"Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        ltp_data = data.get('data', {}).get(symbol_code, {})
        ltp = ltp_data.get('ltp')
        if ltp is None:
            return None, None
        dummy_rsi = 50 + (ltp % 10)
        return ltp, round(dummy_rsi, 2)
    except Exception:
        return None, None

@app.post("/")
async def webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if text.strip().lower().startswith("/stock"):
        parts = text.strip().split()
        if len(parts) < 2:
            reply = "❌ Please specify a symbol like /stock tata"
        else:
            symbol = parts[1].upper()
            price, rsi = fetch_upstox_data(symbol)
            if price:
                reply = f"📊 {symbol} Stock Update:\n\nPrice: {price}\nRSI: {rsi}"
            else:
                reply = f"❌ Unable to fetch data for {symbol}"
    else:
        reply = "ℹ️ Use /stock SYMBOL to get updates. For example: /stock tata"

    requests.post(API_URL, json={
        "chat_id": chat_id,
        "text": reply
    })
    return {"ok": True}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
