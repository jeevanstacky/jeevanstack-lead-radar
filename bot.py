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
    seen = set(state.get("seen_jobs", []))
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get("https://remoteok.com/api", headers=headers, timeout=15)
    listings = r.json()[1:]

    new_jobs = []
    for j in listings:
        jid = str(j.get("id", ""))
        if jid and jid not in seen:
            new_jobs.append(j)
            seen.add(jid)
        if len(new_jobs) >= 4:
            break

    if not new_jobs:
        print("No brand new jobs this hour.")
        return

    msg = "🚀 <b>FRESH REMOTE TECH & FREELANCE LEADS</b>\n\n"
    for j in new_jobs:
        position = j.get("position", "Role").replace("<", "&lt;").replace(">", "&gt;")
        company = j.get("company", "Company").replace("<", "&lt;").replace(">", "&gt;")
        url = j.get("url", "https://remoteok.com")
        salary_min = j.get("salary_min", 0)
        salary_max = j.get("salary_max", 0)
        sal_str = f"💰 ${salary_min//1000}k–${salary_max//1000}k/yr\n" if salary_min and salary_max else ""
        tags = ", ".join(j.get("tags", [])[:4])
        msg += f"🔹 <b>{position}</b> at {company}\n{sal_str}🏷 <code>{tags}</code>\n👉 <a href='{url}'>Apply / Pitch Client</a>\n\n"

    msg += "🌐 <a href='https://jeevanstacky.github.io/jeevanstack-lead-radar/'>Get VIP Alerts or Order a Custom Bot</a>"
    res = send_tg(CHAT_ID, msg)
    print("Lead Broadcast Status:", res.status_code)
    state["seen_jobs"] = list(seen)[-200:]

if __name__ == "__main__":
    state = load_json(SEEN_FILE, {"last_update_id": 0, "seen_jobs": []})
    forward_customer_inquiries(state)
    fetch_and_send_leads(state)
    save_json(SEEN_FILE, state)
