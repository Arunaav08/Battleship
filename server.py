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
        view = game.view_for(sid)
        emit("state", view, to=sid)

@socketio.on("join_game")
def handle_join_game():
    global waiting_room
    sid = request.sid
    if waiting_room is None:
        room = f"game_{len(games) + 1}"
        games[room] = Game()
        waitin_room = room
    else:
        room = waiting_room
        # clear waiting_room
        waiting_room = None
    
    game = games[room]
    game.add_player(sid)
    sid_to_room[sid] = room
            
    join_room(room)
    send_state(room)




def broadcast_state(room_id):
    game = games[room_id]
    for player_id in game.players:
        # Send each player their own customized view
        socketio.emit("state", game.view_for(player_id), to=player_id)
        


@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app, dedug = True)
    
