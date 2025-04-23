from fastapi import FastAPI, Request
import requests
import yfinance as yf

app = FastAPI()

BOT_TOKEN = "7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if text == "/start":
        send_message(chat_id, "👋 Hello Mr. Buddy! Welcome to the stock bot world 💼📈\n\nType `/stock tatamotors` or `/stock reliance` to get live data.")
    elif text.startswith("/stock"):
        parts = text.strip().split()
        if len(parts) >= 2:
            symbol = "".join(parts[1:]).upper()
            stock_info = get_stock_price(symbol)
            if stock_info:
                send_message(chat_id, f"📊 *{symbol}*\nCMP: ₹{stock_info['price']} ({stock_info['change']})", markdown=True)
            else:
                send_message(chat_id, f"❌ Unable to fetch data for `{symbol}`.\nTry NSE symbols like: `RELIANCE`, `ICICIBANK`, `TATAMOTORS`.", markdown=True)
        else:
            send_message(chat_id, "⚠️ Format: `/stock SYMBOL`\nEg: `/stock tatamotors`", markdown=True)
    else:
        send_message(chat_id, "❌ Unknown command. Try `/start` or `/stock tata`", markdown=True)

    return {"ok": True}

def send_message(chat_id, text, markdown=False):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown" if markdown else None
    }
    requests.post(TELEGRAM_API_URL, json=payload)

def get_stock_price(symbol):
    try:
        ticker = yf.Ticker(symbol + ".NS")
        data = ticker.history(period="2d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2] if len(data) > 1 else price
            change = ((price - prev_close) / prev_close) * 100 if prev_close else 0
            arrow = '▲' if change > 0 else '▼' if change < 0 else ''
            return {"price": f"{price:.2f}", "change": f"{arrow} {change:.2f}%"}
    except Exception as e:
        print("Error fetching stock data:", e)
    return None
