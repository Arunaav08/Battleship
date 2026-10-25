from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from game import Game
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

games = {}          # room_id -> Game instance
room_to_sids = {}   # room_id -> {'p1': sid, 'p2': sid}
room_meta = {}      # room_id -> {'p1': username, 'p2': username}
waiting_queue = []  # [{'sid':..., 'username':...}]
tokens = {}         # token -> {'room':..., 'player_id':..., 'username':...}

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def find_room(sid):
    """Return (room_id, player_id) for a socket, or None."""
    for r, sids in room_to_sids.items():
        if sid in sids.values():
            pid = [k for k, v in sids.items() if v == sid][0]
            return r, pid
    return None

def get_state_view(game, player_id):
    view = game.view_for(player_id)
    opponent_id = game._other(player_id)
    view["opponent_here"]  = len(game.players) == 2
    view["you_ready"]      = game.players[player_id]["ready"]
    view["opponent_ready"] = game.players[opponent_id]["ready"] if opponent_id else False
    return view

def send_state(room):
    if room not in games:
        return
    game = games[room]
    for pid, sid in room_to_sids.get(room, {}).items():
        if sid:
            emit("state", get_state_view(game, pid), to=sid)

def handle_player_leaving(sid):
    for i, p in enumerate(waiting_queue):
        if p["sid"] == sid:
            waiting_queue.pop(i)
            return

    for r, sids in list(room_to_sids.items()):
        if sid in sids.values():
            leaving_pid  = [k for k, v in sids.items() if v == sid][0]
            leaving_user = room_meta[r][leaving_pid]
            opponent_pid = "p2" if leaving_pid == "p1" else "p1"
            opponent_sid = sids[opponent_pid]

            if opponent_sid:
                emit("opponent_left", {"username": leaving_user}, to=opponent_sid)
                emit("chat_message",
                     {"sys": True, "text": leaving_user + " left the channel."},
                     to=opponent_sid)

            del games[r]
            del room_to_sids[r]
            del room_meta[r]
            return

@app.route("/")
def index():
    return render_template("index.html")   # lobby

@app.route("/game")
def game_page():
    token = request.args.get("token")
    if not token or token not in tokens:
        return redirect(url_for("index"))
    return render_template("game.html", token=token)

@socketio.on("disconnect")
def handle_disconnect():
    handle_player_leaving(request.sid)

@socketio.on("leave_game")
def handle_leave_game():
    handle_player_leaving(request.sid)

@socketio.on("join_queue")
def handle_join_queue(data):
    sid = request.sid
    username = (data.get("username") or "Commander").strip()[:20]

    if any(p["sid"] == sid for p in waiting_queue):
        return
    waiting_queue.append({"sid": sid, "username": username})
    emit("queue_status", {"status": "waiting"})

    if len(waiting_queue) >= 2:
        p1 = waiting_queue.pop(0)
        p2 = waiting_queue.pop(0)

        room_id = f"game_{len(games) + 1}_{random.randint(1000, 9999)}"
        games[room_id] = Game()
        games[room_id].add_player("p1")
        games[room_id].add_player("p2")

        room_to_sids[room_id] = {"p1": p1["sid"], "p2": p2["sid"]}
        room_meta[room_id]    = {"p1": p1["username"], "p2": p2["username"]}

        t1, t2 = generate_token(), generate_token()
        tokens[t1] = {"room": room_id, "player_id": "p1", "username": p1["username"]}
        tokens[t2] = {"room": room_id, "player_id": "p2", "username": p2["username"]}

        emit("match_found", {"token": t1, "room": room_id}, to=p1["sid"])
        emit("match_found", {"token": t2, "room": room_id}, to=p2["sid"])

@socketio.on("leave_queue")
def handle_leave_queue():
    handle_player_leaving(request.sid)

@socketio.on("authenticate")
def handle_auth(data):
    sid   = request.sid
    token = data.get("token")
    if token in tokens:
        info = tokens[token]
        room, pid = info["room"], info["player_id"]
        room_to_sids[room][pid] = sid
        join_room(room)
        send_state(room)
        emit("chat_message",
             {"sys": True, "text": info["username"] + " connected to the channel."},
             to=room)
    else:
        emit("auth_failed", {})

@socketio.on("chat_message")
def handle_chat_message(data):
    found = find_room(request.sid)
    if not found:
        return
    room, pid = found
    text = (data.get("text") or "").strip()[:200]   # cap length, drop empties
    if not text:
        return
    # Echo to the WHOLE room (sender included) so both sides render identically
    emit("chat_message",
         {"pid": pid, "username": room_meta[room][pid], "text": text},
         to=room)

@socketio.on("voice_signal")
def handle_voice_signal(data):
    found = find_room(request.sid)
    if found:
        emit("voice_signal", data, to=found[0], include_self=False)

@socketio.on("place_ships")
def handle_place_ships():
    found = find_room(request.sid)
    if not found:
        return
    room, pid = found
    games[room].place_ships_random(pid)
    send_state(room)

@socketio.on("fire")
def handle_fire(data):
    found = find_room(request.sid)
    if not found:
        return
    room, pid = found
    result = games[room].fire(pid, data["r"], data["c"])
    if "error" in result:
        emit("error_msg", result, to=request.sid)
        return
    emit("shot_result", result, to=room)
    send_state(room)

if __name__ == "__main__":
    socketio.run(app, debug=True)