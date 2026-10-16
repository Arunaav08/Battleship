# server.py (Day 3 preview)
result = fire(p2_board, p2_ships, row, col)
client.send(json.dumps(result))   # ← straight onto the network, unchanged