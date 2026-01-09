from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "tajna"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/join")
def join():
    username = (request.form.get("username") or "").strip()
    room = (request.form.get("room") or "").strip()

    if not username or not room:
        return render_template("index.html", error="Ime i soba su obavezni.")

    session["username"] = username
    session["room"] = room
    return redirect(url_for("chat"))

@app.get("/chat")
def chat():
    username = session.get("username")
    room = session.get("room")
    if not username or not room:
        return redirect(url_for("index"))
    return render_template("chat.html", username=username, room=room)

@app.get("/leave")
def leave():
    session.pop("username", None)
    session.pop("room", None)
    return redirect(url_for("index"))

@socketio.on("join")
def on_join(data):
    username = (data.get("username") or "").strip()
    room = (data.get("room") or "").strip()
    if not username or not room:
        return

    join_room(room)
    emit("system", {"msg": f"{username} se pridružio sobi."}, to=room)

@socketio.on("chat_message")
def on_chat_message(data):
    username = (data.get("username") or "").strip()
    room = (data.get("room") or "").strip()
    msg = (data.get("msg") or "").strip()

    if not username or not room or not msg:
        return

    emit("chat_message", {"username": username, "msg": msg}, to=room)

@socketio.on("disconnect_request")
def on_disconnect_request(data):
    username = (data.get("username") or "").strip()
    room = (data.get("room") or "").strip()
    if room:
        leave_room(room)
        emit("system", {"msg": f"{username} je napustio sobu."}, to=room)

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True, allow_unsafe_werkzeug=True)
