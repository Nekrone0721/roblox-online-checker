from flask import Flask, render_template_string
import requests

app = Flask(__name__)

USERS = [
    "0115tim",
    "Mycowbay877",
    "1104jimmy",
    "0115tim_EMO"
]

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

.online {
    color:lime;
    font-weight:bold;
}

.offline {
    color:red;
    font-weight:bold;
}
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
    </div>
</div>
{% endfor %}

</body>
</html>
"""

# 取得 user id
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


# 頭像
def get_avatar(user_id):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=true"
    r = requests.get(url).json()
    return r["data"][0]["imageUrl"]


# 在線狀態
def get_presence(user_id):
    url = "https://presence.roblox.com/v1/presence/users"
    r = requests.post(url, json={"userIds": [user_id]})
    return r.json()["userPresences"][0]


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

        result.append({
            "name": username,
            "avatar": avatar,
            "status": status,
            "status_class": status_class
        })

    return render_template_string(HTML, users=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)