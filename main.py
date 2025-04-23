from fastapi import FastAPI, Request
import requests
import time
import threading
import numpy as np
from upstox_api.api import Upstox, LiveFeedType

app = FastAPI()

@app.post("/")
async def telegram_webhook(req: Request):
    data = await req.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if text.strip() == "/start":
        send_message(chat_id, "👋 Hello Mr. Buddy! Welcome to the stock bot world 💼📈")
    elif text.startswith("/stock"):
        parts = text.strip().split()
        if len(parts) >= 2:
            symbol = "".join(parts[1:]).replace(" ", "").upper().replace(" ", "")
            stock_info = get_stock_price(symbol)
            if stock_info:
                send_message(chat_id, f"📊 {symbol}: ₹{stock_info['price']} ({stock_info['change']})")
            else:
                send_message(chat_id, f"❌ Unable to fetch data for {symbol}. Try NSE symbols like RELIANCE, ICICIBANK")
        else:
            send_message(chat_id, "⚠️ Format: /stock SYMBOL\nExample: /stock tatamotors")
    elif text.startswith("/signal"):
        parts = text.strip().split()
        if len(parts) >= 2:
            symbol = "".join(parts[1:]).upper()
            try:
                signal = get_signal_status(symbol)
                send_message(chat_id, signal, markdown=True)
            except Exception as e:
                send_message(chat_id, f"❌ Unable to fetch signal for {symbol}", markdown=True)
        else:
            send_message(chat_id, "⚠️ Format: /signal SYMBOL\nExample: /signal tatamotors", markdown=True)
    else:
        send_message(chat_id, "🤖 Unknown command. Try /start or /stock tata")

# Global tracker to avoid duplicate replies
last_called = {}

# Telegram Bot Details
BOT_TOKEN = "7551804667:AAGcSYXvvHwlv9fWx1rQQM3lQT-mr7bvye8"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Upstox API Setup
API_KEY = "29293c26-f228-4b54-a52c-2aabd500d385"
API_SECRET = "3o5mdjiqcd"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI1WEI3RkQiLCJqdGkiOiI2ODA4YWU3YTMwYmMxMjBlYTZlNTczODMiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaWF0IjoxNzQ1Mzk5NDE4LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NDU0NDU2MDB9.x49jmFTZC9OHSmmbN_cqJYPDgoMbyRBwFj-A49b8ar8"

u = Upstox(API_KEY, API_SECRET)
u.set_access_token(ACCESS_TOKEN)

def auto_signal_loop():
    signal_monitor()
    threading.Timer(300.0, auto_signal_loop).start()  # 5 minutes loop

def signal_monitor():
    watchlist = ["TATAMOTORS", "RELIANCE", "ICICIBANK", "HDFCBANK"]
    for symbol in watchlist:
        try:
            message = get_signal_status(symbol)
            if any(signal in message for signal in ["🟢 BUY", "🔴 SELL"]):
                try:
                    lines = message.split('\n')
                    cmp_line = next((line for line in lines if "CMP" in line), None)
                    if cmp_line:
                        cmp_value = float(cmp_line.split("₹")[1].split(" ")[0])
                        sl = cmp_value * 0.97
                        tp1 = cmp_value * 1.03
                        tp2 = cmp_value * 1.06
                        message += f"\n🛑 SL: ₹{sl:.2f} | 🎯 TP1: ₹{tp1:.2f}, TP2: ₹{tp2:.2f}"
                except Exception as e:
                    print(f"Error parsing CMP and calculating SL/TP: {e}")
                send_message(5604148401, f"🔔 Auto Signal Alert for {symbol}\n{message}", markdown=True)
        except Exception as e:
            print(f"Error monitoring signal for {symbol}:", e)

def get_signal_status(symbol):
    try:
        instrument = f"NSE_EQ|{symbol.upper()}"
        price_data = u.get_live_feed(instrument, LiveFeedType.MARKET_DATA)
        ltp = price_data.get('ltp', 0.0)
        return f"📊 {symbol}
CMP: ₹{ltp:.2f}"
    except Exception as e:
        print(f"❌ Error in signal generation for {symbol}:", e)
        return "⚠️ Unable to fetch CMP for this stock."
    except Exception as e:
        print(f"❌ Error in signal generation for {symbol}:", e)
        return "⚠️ Unable to compute signal right now."
