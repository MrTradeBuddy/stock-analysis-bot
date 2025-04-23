from fastapi import FastAPI, Request
import requests
import yfinance as yf

app = FastAPI()  # ✅ This line should appear only once

@app.get("/")
def read_root():
    return {"status": "Server Running 🚀"}

# Your Telegram Bot token
BOT_TOKEN = "7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    print("🔔 Telegram Message Received:", data)  # log incoming message

    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id or not text:
        return {"ok": False, "error": "Invalid message format"}

    if text == "/start":
        send_message(chat_id, "👋 Hello Mr. Buddy! Welcome to the stock bot world 💼📈\nType `/stock tatamotors` to try.")
    elif text.startswith("/stock"):
        parts = text.strip().split()
        if len(parts) >= 2:
            symbol = "".join(parts[1:]).upper()
            stock_info = get_stock_price(symbol)
            if stock_info:
                send_message(chat_id, f"📊 *{symbol}*\nCMP: ₹{stock_info['price']} ({stock_info['change']})", markdown=True)
            else:
                send_message(chat_id, f"❌ Unable to fetch live data for `{symbol}`.\nTry NSE stock symbols like `RELIANCE`, `ICICIBANK`", markdown=True)
        else:
            send_message(chat_id, "⚠️ Format: `/stock SYMBOL`\nExample: `/stock tatamotors`", markdown=True)
    else:
        send_message(chat_id, "🤖 Unknown command. Try `/start` or `/stock tata`", markdown=True)

    return {"ok": True}

def send_message(chat_id, text, markdown=False):
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if markdown:
        payload["parse_mode"] = "Markdown"
    response = requests.post(TELEGRAM_API_URL, json=payload)
    print("📤 Telegram Response:", response.text)

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
        print("❌ Error fetching stock data:", e)
    return None
