from fastapi import FastAPI, Request
import requests
import yfinance as yf
import time

app = FastAPI()

# Global tracker to avoid duplicate replies
last_called = {}

# Telegram Bot Details
BOT_TOKEN = "7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@app.get("/")
def read_root():
    return {"status": "Server Running 🚀"}

@app.post("/")
async def telegram_webhook(req: Request):
    global last_called
    data = await req.json()
    print("🔔 Telegram Message Received:", data)

    message = data.get("message", {})
    text = message.get("text", "").strip()
    chat_id = message.get("chat", {}).get("id")

    if not chat_id or not text:
        return {"ok": False, "error": "Invalid message format"}

    # Duplicate prevention (block same chat within 2 seconds)
    now = time.time()
    if chat_id in last_called and now - last_called[chat_id] < 2:
        print("⚠️ Skipping duplicate request for chat:", chat_id)
        return {"ok": True}
    last_called[chat_id] = now

    # Small delay to avoid flooding
    time.sleep(0.5)

    # Command Logic
    if text == "/start":
        send_message(chat_id, "👋 Hello Mr. Buddy! Welcome to the stock bot world 💼📈\nType `/stock tatamotors` to try.")
    elif text.startswith("/stock"):
        parts = text.split()
        if len(parts) >= 2:
            symbol = "".join(parts[1:]).upper()
            stock_info = get_stock_price(symbol)
            if stock_info:
                send_message(chat_id, f"📊 *{symbol}*\nCMP: ₹{stock_info['price']} ({stock_info['change']})", markdown=True)
            else:
                send_message(chat_id, f"❌ Unable to fetch data for `{symbol}`.\nTry NSE symbols like `RELIANCE`, `ICICIBANK`", markdown=True)
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

