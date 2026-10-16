import os
import json
import requests

if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().replace("export ", "").split("=", 1)
                os.environ[k] = v.strip('"').strip("'")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("CHAT_ID", "").strip()
SEEN_FILE = "seen_ids.json"

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f)

def send_tg(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    return requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })

def forward_customer_inquiries(state):
    last_update_id = state.get("last_update_id", 0)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 5}
    try:
        r = requests.get(url, params=params, timeout=10).json()
        for upd in r.get("result", []):
            state["last_update_id"] = upd["update_id"]
            msg = upd.get("message", {})
            sender = msg.get("from", {})
            sender_id = str(msg.get("chat", {}).get("id", ""))
            text = msg.get("text", "")

            if sender_id and sender_id != str(CHAT_ID) and text:
                uname = sender.get("username", "NoUsername")
                fname = sender.get("first_name", "Lead")
                alert = (
                    f"💰 <b>NEW WEBSITE CLIENT INQUIRY!</b>\n\n"
                    f"👤 <b>From:</b> {fname} (@{uname})\n"
                    f"🆔 <b>Chat ID:</b> <code>{sender_id}</code>\n"
                    f"💬 <b>Message:</b> {text}\n\n"
                    f"👉 Tap @{uname} to close the deal!"
                )
                send_tg(CHAT_ID, alert)
                send_tg(sender_id, "⚡ <b>JeevanStack Radar:</b> Got your message! Jeevan (CEO) has been notified and will reach out to you shortly.")
    except Exception as e:
        print("Inbox check error:", e)

def fetch_and_send_leads(state):
    seen = list(state.get("seen_jobs", []))
    headers = {'User-Agent': 'Mozilla/5.0'}
    new_items = []

    # Source 1: RemoteOK
    try:
        r = requests.get("https://remoteok.com/api", headers=headers, timeout=12)
        for j in r.json()[1:]:
            jid = f"rok_{j.get('id', '')}"
            if jid not in seen and len(new_items) < 2:
                seen.append(jid)
                pos = j.get("position", "Role").replace("<", "&lt;").replace(">", "&gt;")
                comp = j.get("company", "Company").replace("<", "&lt;").replace(">", "&gt;")
                s_min, s_max = j.get("salary_min", 0), j.get("salary_max", 0)
                sal = f"💰 ${s_min//1000}k–${s_max//1000}k/yr\n" if s_min and s_max else ""
                tags = ", ".join(j.get("tags", [])[:4]) or "remote, tech"
                url = j.get("url", "https://remoteok.com")
                new_items.append(f"🔹 <b>{pos}</b> at {comp}\n{sal}🏷 <code>{tags}</code> (RemoteOK)\n👉 <a href='{url}'>Apply / Pitch Direct</a>")
    except Exception as e:
        print("RemoteOK error:", e)

    # Source 2: Y Combinator / Hacker News Official Job Stream
    try:
        hn_ids = requests.get("https://hacker-news.firebaseio.com/v0/jobstories.json", timeout=10).json()[:15]
        for hid in hn_ids:
            jid = f"hn_{hid}"
            if jid not in seen and len(new_items) < 4:
                item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{hid}.json", timeout=10).json()
                if item and item.get("title"):
                    seen.append(jid)
                    title = item.get("title", "YC Startup Role").replace("<", "&lt;").replace(">", "&gt;")
                    url = item.get("url") or f"https://news.ycombinator.com/item?id={hid}"
                    new_items.append(f"🟧 <b>{title}</b>\n🏷 <code>YC Startup / HN Jobs</code>\n👉 <a href='{url}'>View YC Startup Role</a>")
    except Exception as e:
        print("HN/YC error:", e)

    if not new_items:
        print("No brand new jobs this cycle.")
        return

    msg = "🚀 <b>LIVE RADAR: REMOTE & YC STARTUP LEADS</b>\n\n" + "\n\n".join(new_items)
    msg += "\n\n🌐 <a href='https://jeevanstacky.github.io/jeevanstack-lead-radar/'>VIP Radar (₹299/mo) | Order Custom 24/7 Bot (₹4,999)</a>"
    res = send_tg("@jeevanalerts", msg)
    print("Multi-Source Broadcast Status:", res.status_code)
    state["seen_jobs"] = seen[-500:]

if __name__ == "__main__":
    state = load_json(SEEN_FILE, {"last_update_id": 0, "seen_jobs": []})
    forward_customer_inquiries(state)
    fetch_and_send_leads(state)
    save_json(SEEN_FILE, state)
