import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "tajna"
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

DEFAULT_ROOMS = ["Općenito", "Škola", "Igrice", "Tehnologija", "Random"]
rooms = {r: {} for r in DEFAULT_ROOMS}

def safe_color(value, default):
    v = (value or "").strip()
    if len(v) == 7 and v.startswith("#"):
        ok = all(c in "0123456789abcdefABCDEF" for c in v[1:])
        return v if ok else default
    return default

def allowed_file(filename):
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    return ext in {"png", "jpg", "jpeg", "gif", "webp"}

def user_payload(u):
    return {
        "username": u.get("username", ""),
        "nameColor": u.get("nameColor", "#0d6efd"),
        "bubbleColor": u.get("bubbleColor", "#f1f3f5"),
        "avatarUrl": u.get("avatarUrl") or "/static/default.jpg",
    }


def room_stats():
    return {r: len(rooms.get(r, {})) for r in DEFAULT_ROOMS}

def broadcast_users(room):
    users = []
    for sid, u in rooms.get(room, {}).items():
        users.append({"sid": sid, **user_payload(u)})
    emit("user_list", {"room": room, "users": users}, to=room)
    emit("room_stats", {"stats": room_stats()}, broadcast=True)

@app.get("/")
def index():
    return render_template("index.html", rooms=DEFAULT_ROOMS, stats=room_stats())

@app.post("/join")
def join():
    username = (request.form.get("username") or "").strip()
    room = (request.form.get("room") or "").strip()

    if not username:
        return render_template("index.html", rooms=DEFAULT_ROOMS, stats=room_stats(), error="Ime je obavezno.")

    if room not in DEFAULT_ROOMS:
        return render_template("index.html", rooms=DEFAULT_ROOMS, stats=room_stats(), error="Neispravna soba.")

    session["username"] = username
    session["room"] = room
    return redirect(url_for("chat"))

@app.get("/chat")
def chat():
    username = session.get("username")
    room = session.get("room")
    if not username or not room:
        return redirect(url_for("index"))
    if room not in DEFAULT_ROOMS:
        return redirect(url_for("index"))
    return render_template("chat.html", username=username, room=room, rooms=DEFAULT_ROOMS)

@app.get("/leave")
def leave():
    session.pop("username", None)
    session.pop("room", None)
    return redirect(url_for("index"))

@app.post("/upload")
def upload():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "Nema datoteke."}), 400

    f = request.files["file"]
    if not f or f.filename == "":
        return jsonify({"ok": False, "error": "Prazna datoteka."}), 400

    if not allowed_file(f.filename):
        return jsonify({"ok": False, "error": "Dozvoljeno: png, jpg, jpeg, gif, webp."}), 400

    ext = f.filename.rsplit(".", 1)[-1].lower()
    name = secure_filename(f"{uuid.uuid4().hex}.{ext}")
    path = os.path.join(app.config["UPLOAD_FOLDER"], name)
    f.save(path)

    url = url_for("static", filename=f"uploads/{name}", _external=False)
    return jsonify({"ok": True, "url": url})

@socketio.on("join")
def on_join(data):
    username = (data.get("username") or "").strip()
    room = (data.get("room") or "").strip()
    if not username or room not in DEFAULT_ROOMS:
        return

    sid = request.sid

    if room not in rooms:
        rooms[room] = {}

    rooms[room][sid] = {
        "username": username,
        "nameColor": "#0d6efd",
        "bubbleColor": "#f1f3f5",
        "avatarUrl": "",
    }

    join_room(room)
    emit("system", {"msg": f"{username} se pridružio sobi."}, to=room)
    broadcast_users(room)

@socketio.on("update_profile")
def on_update_profile(data):
    room = (data.get("room") or "").strip()
    if room not in DEFAULT_ROOMS:
        return

    sid = request.sid
    u = rooms.get(room, {}).get(sid)
    if not u:
        return

    new_username = (data.get("username") or "").strip()
    if new_username:
        u["username"] = new_username

    u["nameColor"] = safe_color(data.get("nameColor"), u.get("nameColor", "#0d6efd"))
    u["bubbleColor"] = safe_color(data.get("bubbleColor"), u.get("bubbleColor", "#f1f3f5"))

    avatar = (data.get("avatarUrl") or "").strip()
    if avatar.startswith("/static/uploads/") or avatar == "":
        u["avatarUrl"] = avatar

    broadcast_users(room)

@socketio.on("chat_message")
def on_chat_message(data):
    room = (data.get("room") or "").strip()
    msg = (data.get("msg") or "").strip()
    if room not in DEFAULT_ROOMS or not msg:
        return

    sid = request.sid
    u = rooms.get(room, {}).get(sid)
    if not u:
        return

    emit(
        "chat_message",
        {
            "sid": sid,
            "room": room,
            "msg": msg,
            "user": user_payload(u),
        },
        to=room,
    )

@socketio.on("switch_room")
def on_switch_room(data):
    new_room = (data.get("newRoom") or "").strip()
    old_room = (data.get("oldRoom") or "").strip()

    if new_room not in DEFAULT_ROOMS or old_room not in DEFAULT_ROOMS:
        return

    sid = request.sid
    u = rooms.get(old_room, {}).pop(sid, None)
    if not u:
        return

    leave_room(old_room)
    emit("system", {"msg": f"{u.get('username','Korisnik')} je napustio sobu."}, to=old_room)
    broadcast_users(old_room)

    join_room(new_room)
    rooms[new_room][sid] = u
    emit("system", {"msg": f"{u.get('username','Korisnik')} se pridružio sobi."}, to=new_room)
    broadcast_users(new_room)

@socketio.on("disconnect_request")
def on_disconnect_request(data):
    room = (data.get("room") or "").strip()
    sid = request.sid

    if room in DEFAULT_ROOMS:
        u = rooms.get(room, {}).pop(sid, None)
        leave_room(room)
        if u:
            emit("system", {"msg": f"{u.get('username','Korisnik')} je napustio sobu."}, to=room)
        broadcast_users(room)

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    for room in DEFAULT_ROOMS:
        if sid in rooms.get(room, {}):
            u = rooms[room].pop(sid, None)
            if u:
                emit("system", {"msg": f"{u.get('username','Korisnik')} je napustio sobu."}, to=room)
            broadcast_users(room)

@socketio.on("get_room_stats")
def on_get_room_stats():
    emit("room_stats", {"stats": room_stats()}, to=request.sid)


if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5000, debug=True, allow_unsafe_werkzeug=True)
