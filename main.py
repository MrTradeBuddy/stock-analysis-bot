from fastapi import FastAPI, Request
import uvicorn
import requests

app = FastAPI()

BOT_TOKEN = '7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8'
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# EUR/USD Price and RSI Fetcher
def fetch_eurusd_data():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval=15m&range=1d"
        res = requests.get(url)
        data = res.json()

        close_prices = data['chart']['result'][0]['indicators']['quote'][0]['close']
        timestamps = data['chart']['result'][0]['timestamp']

        # Latest valid close
        latest_price = next((price for price in reversed(close_prices) if price is not None), None)

        # Simple RSI calculation (last 14 closes)
        prices = [p for p in close_prices if p is not None][-15:]
        gains = [max(prices[i+1] - prices[i], 0) for i in range(len(prices)-1)]
        losses = [max(prices[i] - prices[i+1], 0) for i in range(len(prices)-1)]
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))

        return latest_price, round(rsi, 2)

    except Exception as e:
        print("Error fetching EURUSD:", e)
        return None, None


@app.post("/")
async def webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if text.strip().lower() == "/eurusd":
        price, rsi = fetch_eurusd_data()
        if price:
            reply = f"💶 EUR/USD Update:\n\nPrice: {price}\nRSI: {rsi}"
        else:
            reply = "❌ Unable to fetch EUR/USD data."
    else:
        reply = "ℹ️ Use /eurusd to get live update."

    requests.post(API_URL, json={
        "chat_id": chat_id,
        "text": reply
    })
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
