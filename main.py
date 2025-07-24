import os, asyncio
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from binance.client import Client
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN = os.environ["8388245484:AAEOxz42dBgXDi8BekJSrQZkK63kzwPNCjM"]
CHAT_ID = int(os.environ["7971223324"])
client = Client(api_key="", api_secret="")  # без ключей, только публичный доступ
PRICE_LIMIT = 1.0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я сигнал-бот Binance на Render.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start — старт\n/help — помощь")

def get_cheap_symbols():
    return [t['symbol'] for t in client.get_all_tickers() if t['symbol'].endswith('USDT') and float(t['price']) < PRICE_LIMIT]

def analyze_symbol(sym):
    try:
        df = pd.DataFrame(client.get_klines(symbol=sym, interval=Client.KLINE_INTERVAL_1MINUTE, limit=30),
                          columns=['open_time','open','high','low','close','volume','close_time','q_vol','trades','tb_base','tb_quote','ignore'])
        df['close'] = df['close'].astype(float)
        df['MA5'] = df['close'].rolling(5).mean()
        df['MA20'] = df['close'].rolling(20).mean()
        if len(df) < 20: return None
        p5, p20, l5, l20 = df['MA5'].iloc[-2], df['MA20'].iloc[-2], df['MA5'].iloc[-1], df['MA20'].iloc[-1]
        price = df['close'].iloc[-1]
        if p5 < p20 < l5 > l20: sig = "LONG"
        elif p5 > p20 > l5 < l20: sig = "SHORT"
        else: return None
        return {"symbol": sym, "signal": sig, "price": price}
    except:
        return None

async def send_signal(bot: Bot, s):
    price = s["price"]; sym = s["symbol"]; tp = price * (1.05 if s["signal"] == "LONG" else 0.95)
    sl = price * (0.98 if s["signal"] == "LONG" else 1.02)
    msg = f"🔥 {sym}\nТип: {s['signal']}\nВход: {price:.6f}\nSL: {sl:.6f}\nTP: {tp:.6f}\n{datetime.now(timezone.utc)}"
    await bot.send_message(chat_id=CHAT_ID, text=msg)

async def job(app):
    print("✅ Анализ...")
    syms = get_cheap_symbols()
    for s in [analyze_symbol(sym) for sym in syms]:
        if s: await send_signal(app.bot, s)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    sched = AsyncIOScheduler()
    sched.add_job(job, "interval", minutes=20, args=[app])
    sched.start()
    await job(app)
    print("🚀 Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio; nest_asyncio.apply()
    asyncio.run(main())
b) requirements.txt
Копировать
Редактировать
python-telegram-bot==20.3
python-binance
pandas
apscheduler
nest_asyncio
