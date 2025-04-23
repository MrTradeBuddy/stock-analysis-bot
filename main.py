from fastapi import FastAPI, Request
import requests
import time
from upstox_api.api import Upstox, LiveFeedType

app = FastAPI()

# Global tracker to avoid duplicate replies
last_called = {}

# Telegram Bot Details
BOT_TOKEN = "7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Upstox API Setup
API_KEY = "29293c26-f228-4b54-a52c-2aabd500d385"
API_SECRET = "3o5mdjiqcd"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI1WEI3RkQiLCJqdGkiOiI2ODA4YWU3YTMwYmMxMjBlYTZlNTczODMiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzQ1Mzk5NDE4LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDU0NDU2MDB9.x49jmFTZC9OHSmmbN_cqJYPDgoMbyRBwFj-A49b8ar8"  # ✅ Access token added

u = Upstox(API_KEY, API_SECRET)
u.set_access_token(ACCESS_TOKEN)

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

    now = time.time()
    if chat_id in last_called and now - last_called[chat_id] < 2:
        print("⚠️ Skipping duplicate request for chat:", chat_id)
        return {"ok": True}
    last_called[chat_id] = now

    time.sleep(0.5)

    if text == "/start":
        send_message(chat_id, "👋 Hello Mr. Buddy! Welcome to the stock bot world 💼📈\nType `/stock tatamotors` to try.")
    elif text.startswith("/stock"):
        parts = text.split()
        if len(parts) >= 2:
            symbol = "".join(parts[1:]).upper()
            stock_info = get_upstox_price(symbol)
            if stock_info:
                send_message(chat_id, f"📊 *{symbol}*\nCMP: ₹{stock_info['price']} ({stock_info['change']})", markdown=True)
            else:
                send_message(chat_id, f"❌ Unable to fetch data for `{symbol}`.\nTry symbols like `RELIANCE`, `ICICIBANK`.", markdown=True)
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

def get_upstox_price(symbol):
    try:
        instrument = f"NSE_EQ|{symbol.upper()}"
        data = u.get_live_feed(instrument, LiveFeedType.MARKET_DATA)
        ltp = data.get('ltp', 0.00)
        change = data.get('ltpc', 0.00)
        arrow = '▲' if change > 0 else '▼' if change < 0 else ''
        return {"price": f"{ltp:.2f}", "change": f"{arrow} {change:.2f}%"}
    except Exception as e:
        print("❌ Upstox fetch error:", e)
        return None
