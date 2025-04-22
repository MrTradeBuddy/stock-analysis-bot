from fastapi import FastAPI, Request
import requests

app = FastAPI()

BOT_TOKEN = "7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

STOCK_DATA = {
    "tata": "TATAMOTORS: ₹895.25 (▲ 1.34%)",
    "icici": "ICICIBANK: ₹1,095.10 (▼ 0.45%)",
    "reliance": "RELIANCE: ₹2,830.70 (▲ 0.76%)",
    "hdfc": "HDFCBANK: ₹1,435.65 (▼ 0.21%)"
}

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if text.strip() == "/":
        send_message(chat_id, "👋 Hello Mr. Buddy! Type /stock SYMBOL to get stock updates. For example: /stock tata")
    elif text == "/start":
        send_message(chat_id, "👋 Hello Mr. Buddy! Welcome to the stock bot world 💼📈")
    elif text.startswith("/stock"):
        parts = text.strip().split()
        if len(parts) == 2:
            symbol = parts[1].lower()
            stock_info = STOCK_DATA.get(symbol)
            if stock_info:
                send_message(chat_id, f"📊 {stock_info}")
            else:
                send_message(chat_id, f"❌ Stock '{symbol}' not found. Try /stock tata or /stock icici")
        else:
            send_message(chat_id, "📢 Please use the correct format: /stock SYMBOL")
    else:
        send_message(chat_id, "❌ Unknown command. Try /start or /stock tata")

    return {"ok": True}

def send_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(TELEGRAM_API_URL, json=payload)
