from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-change-me"
socketio = SocketIO(app, cors_allowed_origins="*")

# Connected users: key = socket id, value = {sid, username, avatar}
users = {}


def broadcast_users():
    emit("user_list", list(users.values()), broadcast=True)


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def handle_connect():
    username = f"User_{random.randint(1000, 9999)}"
    gender = random.choice(["girl", "boy"])
    avatar_url = f"https://avatar.iran.liara.run/public/{gender}?username={username}"
    users[request.sid] = {"sid": request.sid, "username": username, "avatar": avatar_url}
    emit("user_joined", {"sid": request.sid, "username": username, "avatar": avatar_url}, broadcast=True)
    emit("set_username", {"username": username})
    broadcast_users()


@socketio.on("disconnect")
def handle_disconnect():
    user = users.pop(request.sid, None)
    if user:
        emit("user_left", {"username": user["username"]}, broadcast=True)
        broadcast_users()


@socketio.on("send_message")
def handle_message(data):
    user = users.get(request.sid)
    message = (data or {}).get("message", "").strip()[:500]
    if user and message:
        emit("new_message", {
            "sid": request.sid,
            "username": user["username"],
            "avatar": user["avatar"],
            "message": message,
        }, broadcast=True)


@socketio.on("update_username")
def handle_update_username(data):
    user = users.get(request.sid)
    new_username = (data or {}).get("username", "").strip()[:24]
    if user and new_username and new_username != user["username"]:
        old_username = user["username"]
        user["username"] = new_username
        emit("username_updated", {
            "sid": request.sid,
            "old_username": old_username,
            "new_username": new_username,
        }, broadcast=True)
        broadcast_users()


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
