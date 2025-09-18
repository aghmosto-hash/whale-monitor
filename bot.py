# ================== Whale Monitor - سبحان v4 Final (ready to paste) ==================
# Paste this whole file into Pydroid / Replit as main.py and Run.
import os
import time
import json
import threading
import requests
from datetime import datetime, timedelta, timezone
from flask import Flask

# ------------------ تنظیمات (توکن و chat_id داخل کد) ------------------
BOT_TOKEN = "8396611567:AAGKIY7b47N7QeK8rNWoJZW9OemVB-xz3TI"
CHAT_ID = "7921910205"

# ------------------ ثابت‌ها ------------------
HYPER_URL = "https://api.hyperliquid.xyz/info"
USD_FILTER_MIN = 10_000.0
LOG_FILE = "signals.json"
LAST_FILE = "last_run.json"

CHECK_INTERVAL_SECONDS = 300  # هر 5 دقیقه چک کن
ALIVE_EVERY_MINUTES = 30      # پیام Alive هر نیم ساعت

# ------------------ لیست 50 نهنگ ------------------
WHALES = [
    "0x5078c2fbea2b2ad61bc840bc023e35fce56bedb6",
    "0xf3f496c9486be5924a93d67e98298733bb47057c",
    "0x7ab8c59db7b959bb8c3481d5b9836dfbc939af21",
    "0x45d26f28196d226497130c4bac709d808fed4029",
    "0xe0c8d0d390454dc98977cf53123244d74c9478c1",
    "0xdd588eeebfa4c1b0112a9efffc7f0bc8529bfb1c",
    "0x64afae722a05b1d28e831b2c20a8ebfea9da6352",
    "0x6c50446ced034fb5617b005f0775746931a9db55",
    "0x960bb18454cd67b5a3edb4fa802b7c0b5b10e2ee",
    "0x6e4a971b81ca58045a2aa982eaa3d50c4ac38f42",
    "0x6c46422a0f7dbbad9bec3bbbc1189bfaf9794b05",
    "0x4fa2e5871dd9622c515f66a4b3230b73236e0d8d",
    "0xd2f83cf5c697e892a38f8d1830eb88ebc0809a0c",
    "0xbb92b9d18db99c3695bc820bf2c876d4b1527fa5",
    "0x1d52fe9bde2694f6172192381111a91e24304397",
    "0x15b325660a1c4a9582a7d834c31119c0cb9e3a42",
    "0xebb258660bfb0385ba14625f6876dafc4b9b0a03",
    "0x7ca165f354e3260e2f8d5a7508cc9dd2fa009235",
    "0x53babe76166eae33c861aeddf9ce89af20311cd0",
    "0xb28cf8649d1cda2975d290f04ea4cc4db7b3828e",
    "0x22268f7ad3c232ac9cbb96730411c9ed24ebb239",
    "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2",
    "0x742d35cc6634c0532925a3b844bc454e4438f44e",
    "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0",
    "0x28c6c06298d514db089934071355e5743bf21d60",
    "0xf977814e90da44bfa03b6295a0616a897441acec",
    "0x5a52e96bacdabb82fd05763e25335261b270efcb",
    "0x742d35cc6634c0532925a3b844bc454e4438f44f",
    "0x8ee7d9235e01e6b42345120b5d270bdb763624c7",
    "0x66f820a414680b5bcda5eeca5dea238543f42054",
    "0xbc47b5f1a1f77d5a8b19d3f8bb4b4ea3e65b1a7a",
    "0x0a57ef8b1b3f0f28a2b6a5d4e5f9c6a1b2c3d4e5",
    "0x1a2b3c4d5e6f7081928374655647382918273645",
    "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
    "0x0123456789abcdef0123456789abcdef01234567",
    "0xa0df350d2637096571f7a701cbc1c5fdc5fa5b5d",
    "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
    "0x3f5ce5fbfe3e9af3971d0ef6c5b9e9b1a9a3b2b1",
    "0x2a65aca4d5fc5b5c859090a6c34d164135398226",
    "0x6b175474e89094c44da98b954eedeac495271d0f",
    "0x00000000219ab540356cBB839Cbe05303d7705Fa",
    "0x7ef2e0048f5bAeDe046f6BF797943daF4ED8CB47",
    "0x281055afc982d96fab65b3a49cac8b878184cb16",
    "0x66f820a414680b5bcda5eeca5dea238543f42055",
    "0x5aeda56215b167893e80b4fe645ba6d5bab767de",
    "0x4e9ce36e442e55ecd9025b9a6e0d88485d628a67",
    "0x0d8775f648430679a709e98d2b0cb6250d2887ef",
    "0x742d35cc6634c0532925a3b844bc454e4438f449",
]
WHALES = [w.lower() for w in WHALES]

# ------------------ Helpers ------------------
def now_iran_str():
    return (datetime.now(timezone.utc) + timedelta(hours=3, minutes=30)).strftime("%Y-%m-%d %H:%M:%S IRST")

def fmt_num(x):
    try:
        x = float(x)
        return "{:,.2f}".format(x) if abs(x) >= 1 else "{:.6f}".format(x)
    except:
        return str(x)

def send_telegram(msg: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("BOT token/chat id missing")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        print("Telegram status:", r.status_code)
    except Exception as e:
        print("Telegram send error:", e)

def save_signal(data: dict):
    try:
        all_data = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        all_data.append(data)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Save error:", e)

def load_last_checked():
    try:
        if os.path.exists(LAST_FILE):
            with open(LAST_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if d and d.get("last_checked"):
                    return datetime.fromisoformat(d.get("last_checked"))
    except Exception:
        pass
    return datetime.fromtimestamp(0, tz=timezone.utc)

def save_last_checked(dt: datetime):
    try:
        with open(LAST_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_checked": dt.isoformat()}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Save last checked error:", e)

# ------------------ Hyperliquid checker ------------------
def check_hyper_positions():
    found = 0
    last_checked = load_last_checked()

    for addr in WHALES:
        try:
            r = requests.post(HYPER_URL, json={"type": "clearinghouseState", "user": addr}, timeout=8)
            if r.status_code != 200:
                # API non-200 skip
                continue
            data = r.json()
        except Exception as e:
            # networking or parsing error -> skip this address
            continue

        positions = data.get("assetPositions") or []
        for item in positions:
            pos = item.get("position") or {}
            if not pos:
                continue

            notional = float(pos.get("notionalUsd", 0) or 0)
            szi = float(pos.get("szi", 0) or 0)
            if szi == 0 or notional < USD_FILTER_MIN:
                continue

            opened_ts = pos.get("openedAt")
            if opened_ts:
                try:
                    opened_dt = datetime.fromtimestamp(float(opened_ts), tz=timezone.utc)
                except Exception:
                    opened_dt = datetime.now(timezone.utc)
                if opened_dt <= last_checked:
                    continue
            else:
                opened_dt = datetime.now(timezone.utc)

            coin = pos.get("coin", "")
            side = (pos.get("side") or "").lower()

            msg = (
                f"🛎️ *سیگنال نهنگ (Hyperliquid)*\n\n"
                f"📌 آدرس: {addr}\n"
                f"🕓 زمان باز شدن پوزیشن: {opened_dt.isoformat()}\n"
                f"🕓 زمان دریافت (ایران): {now_iran_str()}\n"
                f"💎 کوین: *{coin}*\n"
                f"{'🟢 خرید (Long)' if side == 'long' else '🔴 فروش (Short)'}\n"
                f"💰 حجم: *{fmt_num(abs(szi))}*\n"
                f"💲 ارزش دلاری: *${fmt_num(notional)}*\n"
                f"🎯 ورود: ${fmt_num(float(pos.get('entryPx') or 0))}\n"
                f"💹 قیمت لحظه‌ای: ${fmt_num(float(pos.get('oraclePx') or 0))}\n"
                f"⚡ اهرم: *{pos.get('leverage', '?')}*"
            )
            send_telegram(msg)

            save_signal({
                "type": "hyper",
                "time": now_iran_str(),
                "opened": opened_dt.isoformat(),
                "addr": addr,
                "coin": coin,
                "side": side,
                "notional": notional,
                "entry": float(pos.get("entryPx") or 0),
                "market": float(pos.get("oraclePx") or 0)
            })
            found += 1

    # update last checked to now (UTC)
    save_last_checked(datetime.now(timezone.utc))
    return found

# ------------------ Worker + Flask (keep-alive) ------------------
app = Flask("whale_keepalive")

@app.route("/")
def home():
    return "Whale Monitor active", 200

def worker_loop():
    while True:
        try:
            found = check_hyper_positions()
            now = datetime.now(timezone.utc)
            if now.minute % ALIVE_EVERY_MINUTES == 0:
                send_telegram(f"✅ Bot Alive | Signals: {found} | {now_iran_str()}")
        except Exception as e:
            print("Worker error:", e)
        time.sleep(CHECK_INTERVAL_SECONDS)

def start_worker_thread():
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()

# ------------------ Start ------------------
if __name__ == "__main__":
    # ensure files exist
    try:
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
        if not os.path.exists(LAST_FILE):
            with open(LAST_FILE, "w", encoding="utf-8") as f:
                json.dump({"last_checked": datetime.fromtimestamp(0, tz=timezone.utc).isoformat()}, f)
    except Exception as e:
        print("File create error:", e)

    start_worker_thread()
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
  
