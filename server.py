from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
from game import Game

app = Flask(__name__)
socketio = SocketIO(app)

games = {}
sid_to_room = {}
waiting_room = None

def send_state(room):
    game = games[room]
    for sid in game.players:
        view = game.view_for(sid)#view for each sid
        print("STATE", sid, view["opponent_here"], view["you_ready"])   # new line
        emit("state", view, to=sid)#emit the state

@socketio.on("join_game")
def handle_join_game():
    global waiting_room
    sid = request.sid
    print("JOIN", sid, "waiting_room:", waiting_room)    # new line
    if waiting_room is None:
        room = f"game_{len(games) + 1}"
        games[room] = Game()
        waiting_room = room
    else:
        room = waiting_room
        # clear waiting_room
        waiting_room = None
    
    game = games[room]
    game.add_player(sid)
    sid_to_room[sid] = room
            
    join_room(room)
    send_state(room)

@socketio.on("place_ships")
def handle_place_ships():
    sid = request.sid
    room = sid_to_room[sid]
    game = games[room]
    game.place_ships_random(sid)
    send_state(room)

@socketio.on("fire")
def handle_fire(data):
    sid = request.sid
    room = sid_to_room[sid]
    game = games[room]
    result = game.fire(sid,data["r"],data["c"])

    if "error" in result:
        emit("error_msg", result, to=sid)
        return

    emit("shot_result", result, to=room)
    send_state(room)
        


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    socketio.run(app, debug = True)
    
