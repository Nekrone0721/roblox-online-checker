from flask import Flask, render_template_string
import os
import requests
import sqlite3
import time
from datetime import datetime

app = Flask(__name__)

# ========= 設定 =========
USERS = [
    "0115tim",
    "Mycowbay877",
    "1104jimmy",
    "0115tim_EMO"
]

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1510870986679910410/f10cI7C2ps2K4pkF9cEqDEGcptr1WyZeBnZDUma0fpzyDJiDRbfbFvjwE2D5bBga5n7O"

# ========= 資料庫 =========
conn = sqlite3.connect("tracker.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    username TEXT,
    start_time REAL,
    end_time REAL,
    duration INTEGER
)
""")
conn.commit()

online_start = {}
last_seen = {}

# ========= Discord =========
def send_dc(msg):
    if not DISCORD_WEBHOOK:
        return
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg})
    except:
        pass

# ========= Roblox =========
def get_user_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    r = requests.post(url, json={
        "usernames": [username],
        "excludeBannedUsers": True
    })
    data = r.json()

    if data.get("data"):
        return data["data"][0]["id"]
    return None


def get_avatar(user_id):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=true"
    r = requests.get(url).json()
    return r["data"][0]["imageUrl"]


def get_presence(user_id):
    url = "https://presence.roblox.com/v1/presence/users"
    r = requests.post(url, json={"userIds": [user_id]})
    return r.json()["userPresences"][0]

# ========= 統計 =========
def get_today_time(username):
    today = datetime.now().strftime("%Y-%m-%d")

    c.execute("""
        SELECT SUM(duration)
        FROM sessions
        WHERE username = ?
    """, (username,))

    total = c.fetchone()[0]

    if not total:
        return 0

    return total


def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

# ========= HTML =========
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="20">
<title>Roblox 在線監控</title>

<style>
body {
    background:#111;
    color:white;
    font-family:Arial;
    padding:20px;
}

.user {
    display:flex;
    gap:20px;
    padding:15px;
    margin:10px 0;
    background:#222;
    border-radius:15px;
}

img {
    width:80px;
    height:80px;
    border-radius:50%;
}

.online {color:lime;font-weight:bold;}
.offline {color:red;font-weight:bold;}
.info {color:#aaa;}
</style>
</head>

<body>

<h1>🎮 Roblox 在線監控</h1>

{% for u in users %}
<div class="user">
    <img src="{{u.avatar}}">
    <div>
        <h2>{{u.name}}</h2>
        <p class="{{u.status_class}}">{{u.status}}</p>
        <p class="info">今日在線：{{u.today}}</p>
        <p class="info">最後上線：{{u.last_seen}}</p>
    </div>
</div>
{% endfor %}

</body>
</html>
"""

# ========= 主頁 =========
@app.route("/")
def home():
    result = []

    for username in USERS:
        user_id = get_user_id(username)

        if not user_id:
            continue

        avatar = get_avatar(user_id)
        presence = get_presence(user_id)

        status = "離線"
        status_class = "offline"

        if presence:
            ptype = presence.get("userPresenceType", 0)

            if ptype in [1, 2, 3]:
                status = "在線"
                status_class = "online"

                if username not in online_start:
                    online_start[username] = time.time()
                    send_dc(f"🟢 {username} 上線了")

                last_seen_text = "現在在線"

            else:
                if username in online_start:
                    start = online_start.pop(username)
                    end = time.time()
                    duration = int(end - start)

                    c.execute("""
                        INSERT INTO sessions VALUES (?, ?, ?, ?)
                    """, (username, start, end, duration))
                    conn.commit()

                    send_dc(
                        f"🔴 {username} 離線了\\n在線時間：{format_time(duration)}"
                    )

                last_seen[username] = datetime.now()
                last_seen_text = last_seen[username].strftime("%H:%M:%S")
        else:
            last_seen_text = "未知"

        result.append({
            "name": username,
            "avatar": avatar,
            "status": status,
            "status_class": status_class,
            "today": format_time(get_today_time(username)),
            "last_seen": last_seen_text
        })

    return render_template_string(HTML, users=result)
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
