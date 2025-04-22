from fastapi import FastAPI, Request
import requests

app = FastAPI()

BOT_TOKEN = "7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Accept": "application/json"
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
            symbol = parts[1].upper()
            stock_info = get_nse_price(symbol.lower())
            if stock_info:
                send_message(chat_id, f"📊 {symbol}: ₹{stock_info['price']} ({stock_info['change']})")
            else:
                send_message(chat_id, f"❌ Unable to fetch live data for {symbol}. Please try a valid NSE symbol like TATAMOTORS, ICICIBANK")
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

def get_nse_price(symbol):
    try:
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        session = requests.Session()
        session.headers.update(HEADERS)
        session.get("https://www.nseindia.com")
        res = session.get(url)
        if res.status_code == 200:
            data = res.json()
            price = data['priceInfo']['lastPrice']
            change = f"{'▲' if data['priceInfo']['change'] > 0 else '▼'} {abs(data['priceInfo']['change'])}"
            return {"price": price, "change": change}
    except:
        return None
