import time
import requests
from flask import Flask
from threading import Thread

# ⚙️ الإعدادات الشخصية ديالك (واجدة ومقادة)
TELEGRAM_TOKEN = '8801990769:AAEbfngIzxSCEGlc7xhZOwRJf2_jG-j9PZ4'
TELEGRAM_CHAT_ID = '1774472504'

TIMEFRAMES = ['15m', '30m', '1h', '4h']
reported_breakouts = {}

# سيرفر وهمي باش يبقى السيرفر السحابي شغال 24/24 فـ Render
app = Flask('')
@app.route('/')
def home(): return "Bot is Running Live!"
def run(): app.run(host='0.0.0.0', port=8080)

def send_to_telegram(text):
    url = f"https://api.telegram.com/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

def get_all_usdt_symbols():
    """ جلب جميع العملات المتاحة للتداول مقابل USDT من بينانص """
    try:
        url = "https://api.binance.com/api/v3/exchangeInfo"
        response = requests.get(url, timeout=10).json()
        symbols = []
        for s in response['symbols']:
            # كنجيبو غير العملات اللي كيساليا بـ USDT واللي مسموح بالتداول ديالها دابا
            if s['symbol'].endswith('USDT') and s['status'] == 'TRADING':
                # كنحيدو عملات الاستقرار بحال USDC أو BUSD باش ما يبرزطوناش فالتوصيات
                if not any(stable in s['symbol'] for stable in ['USDCUSDT', 'BUSDUSDT', 'EURUSDT', 'GBPUSDT', 'DAIUSDT']):
                    symbols.append(s['symbol'])
        return symbols
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        # قائمة احتياطية ف حالة وقع ضغط على السيرفر
        return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']

def get_klines(symbol, interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=50"
    try: return requests.get(url, timeout=10).json()
    except: return None

def check_breakout(symbols_list):
    for interval in TIMEFRAMES:
        for symbol in symbols_list:
            klines = get_klines(symbol, interval)
            if not klines or len(klines) < 25: continue
            
            current_close = float(klines[-1][4]) 
            last_close = float(klines[-2][4])
            highs = [float(candle[2]) for candle in klines[-22:-2]]
            highest_resistance = max(highs)
            
            breakout_key = f"{symbol}_{interval}_{highest_resistance}"
            
            if last_close > highest_resistance and current_close > highest_resistance:
                if breakout_key in reported_breakouts: continue
                
                entry_price = current_close
                if 'h' in interval:
                    # أهداف فريمات كبار (6% ربح، 4% ستوب)
                    take_profit = round(entry_price * 1.06, 4)
                    stop_loss = round(highest_resistance * 0.96, 4)
                else:
                    # أهداف فريمات صغار (3% ربح، 2% ستوب)
                    take_profit = round(entry_price * 1.03, 4)
                    stop_loss = round(highest_resistance * 0.98, 4)
                
                msg = (
                    f"🚨 *إشارة اختراق قمة جديدة (USDT)!*\n\n"
                    f"🪙 *العملة:* `{symbol}`\n"
                    f"⏱️ *الفريم:* `{interval}`\n"
                    f"📈 *النوع:* `BUY / LONG`\n\n"
                    f"📥 *الدخول (Entry):* `{entry_price}`\n"
                    f"🎯 *الهدف (TP):* `{take_profit}`\n"
                    f"🛑 *الستوب (SL):* `{stop_loss}`\n\n"
                    f"👇 _كليكي على الأرقام من التيليفون غيتكوباو نيشان!_"
                )
                send_to_telegram(msg)
                reported_breakouts[breakout_key] = True
            
            # فاصل زمني صغير بـ الأجزاء من الثانية لحماية البوت من الحظر (Anti-Ban)
            time.sleep(0.05)

def bot_loop():
    all_symbols = get_all_usdt_symbols()
    send_to_telegram(f"🚀 *البوت شغال بنجاح!*\n🎯 كيقرا دابا كاع عملات الـ `USDT` (عددها: {len(all_symbols)} عملة) على فريمات: 15m, 30m, 1h, 4h.")
    
    while True:
        check_breakout(all_symbols)
        time.sleep(30)

if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot_loop()
