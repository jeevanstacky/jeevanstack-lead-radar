import os
import requests

# Automatically load from .env if present
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().replace("export ", "").split("=", 1)
                os.environ[k] = v.strip('"').strip("'")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("CHAT_ID", "").strip()

def fetch_and_send():
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get("https://remoteok.com/api", headers=headers, timeout=15)
    jobs = r.json()[1:4]

    msg = "🚀 <b>NEW REMOTE TECH & FREELANCE LEADS</b>\n\n"
    for j in jobs:
        position = j.get("position", "Role").replace("<", "&lt;").replace(">", "&gt;")
        company = j.get("company", "Company").replace("<", "&lt;").replace(">", "&gt;")
        url = j.get("url", "https://remoteok.com")
        tags = ", ".join(j.get("tags", [])[:3])
        msg += f"🔹 <b>{position}</b> at {company}\n🏷 <code>{tags}</code>\n👉 <a href='{url}'>Apply / Pitch Direct</a>\n\n"

    msg += "⚡ <i>Automated by JeevanStack Radar</i>"

    tg_url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
    res = requests.post(tg_url, json={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })
    print("Telegram Status:", res.status_code, res.text)

if __name__ == "__main__":
    fetch_and_send()
