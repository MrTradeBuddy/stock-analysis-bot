from fastapi import FastAPI, Request
import requests
import uvicorn
import asyncio
import pandas as pd
import numpy as np
from contextlib import asynccontextmanager
import os

app = FastAPI()

BOT_TOKEN = '7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8'
CHAT_ID = '5604148401'
TWELVEDATA_API_KEY = "0e80070490cb46dc9d794364e43caf7a"

last_alerts = {}

# ------------- Utility Functions -------------


def send_message(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)


def get_price(symbol="BTC/USD"):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVEDATA_API_KEY}"
    response = requests.get(url).json()
    return float(response.get("price", 0.0))


def get_ohlcv(symbol="BTC/USD", interval="5min"):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=100&apikey={TWELVEDATA_API_KEY}"
    response = requests.get(url).json()
    values = response.get("values", [])
    df = pd.DataFrame(values)
    df = df.iloc[::-1]  # Reverse for correct order
    df["close"] = pd.to_numeric(df["close"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    return df


def calculate_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calculate_ema(df, span=21):
    return df["close"].ewm(span=span, adjust=False).mean()


def calculate_supertrend(df, period=10, multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    atr = (df['high'] - df['low']).rolling(period).mean()
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
    supertrend = [True]  # True = Bullish, False = Bearish

    for i in range(1, len(df)):
        if df['close'][i] > upperband[i - 1]:
            supertrend.append(True)
        elif df['close'][i] < lowerband[i - 1]:
            supertrend.append(False)
        else:
            supertrend.append(supertrend[-1])

    return supertrend


# ------------- Status Generator -------------


def generate_status(symbol="BTC/USD"):
    df = get_ohlcv(symbol)
    rsi = round(calculate_rsi(df).iloc[-1], 2)
    ema_fast = calculate_ema(df, 9)
    ema_slow = calculate_ema(df, 21)
    ema_trend = "🔼 Bullish" if ema_fast.iloc[-1] > ema_slow.iloc[
        -1] else "🔻 Bearish"
    st = calculate_supertrend(df)
    supertrend = "🟢 Buy" if st[-1] else "🔴 Sell"
    price = get_price(symbol)

    signal = "⚠️ Watch Carefully!" if rsi > 70 or rsi < 30 else "✅ Normal Zone"

    msg = (f"📊 *{symbol} Status*\n"
           f"💵 Price: *{price}*\n"
           f"📈 RSI: *{rsi}*\n"
           f"📉 Supertrend: {supertrend}\n"
           f"📊 EMA Trend: {ema_trend}\n"
           f"🎯 Signal: {signal}")
    return msg


# ------------- Webhook & Background Loop -------------


@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    print("✅ Message Received from Telegram:", data)
    text = data.get("message", {}).get("text", "").lower()

    if "status.btc" in text:
        send_message(generate_status("BTC/USD"))
    elif "status.eur" in text:
        send_message(generate_status("EUR/USD"))
    elif "status.test" in text:
        send_message("🔥 Hello from Mr. Trade Buddy – I'm Alive & Kicking!")

    return {"ok": True}


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    loop.create_task(auto_rsi_alert_loop("BTC/USD"))
    loop.create_task(auto_rsi_alert_loop("EUR/USD"))
    yield


app.router.lifespan_context = lifespan


async def auto_rsi_alert_loop(symbol):
    while True:
        try:
            df = get_ohlcv(symbol)
            rsi = round(calculate_rsi(df).iloc[-1], 2)
            price = get_price(symbol)
            if rsi >= 80:
                send_message(
                    f"🚨 *RSI ALERT* {symbol} is Overbought!\n📈 RSI: *{rsi}*\n💵 Price: *{price}*"
                )
            elif rsi <= 20:
                send_message(
                    f"🚨 *RSI ALERT* {symbol} is Oversold!\n📉 RSI: *{rsi}*\n💵 Price: *{price}*"
                )
        except Exception as e:
            print(f"Error in RSI loop for {symbol}: {e}")
        await asyncio.sleep(300)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
