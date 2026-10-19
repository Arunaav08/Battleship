import random
BOARD_SIZE  = 10
SHIPS       = {"Carrier": 5, "Battleship": 4, "Cruiser": 3,
               "Submarine": 3, "Destroyer": 2}
WATER, SHIP, HIT, MISS = "~", "S", "X", "O"


def create_board():
    board = []  # empty list
    for _ in range(BOARD_SIZE):   # for each row
        row = [WATER] * BOARD_SIZE  # it's like ["~", "~", "~", .......]
        board.append(row)   # [["~", "~", "~", ...], ["~", "~", "~", .......], ["~", "~", "~", .......], ....]
    return board

def randomly_place_ship(board, ship_list, name):
    length =  SHIPS[name]
    while True:
        row, column = random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)
        #name = random.choice(list(SHIPS))
        horizontal = random.choice([True, False])
        if can_place(board, row, column, length, name, horizontal):
            place_ship(board, ship_list, row, column, name, horizontal)
            break

def place_all_ships(board, ship_list):
    for name in SHIPS:
        randomly_place_ship (board, ship_list, name)

def can_place(board, row, col, length, name, horizontal):
    # if ship length exceeds the board size vertically or horizontally
    if horizontal and col + length > BOARD_SIZE:
        return False
    if not horizontal and row + length > BOARD_SIZE:
        return False
    
    for i in range(length):
        # a = b if condition else c(like: a = c)
        r = row if horizontal else row + i
        c = col + i if horizontal else col
        if board[r][c] != WATER: # if overlapping another ship
            return False
    return True


def place_ship(board, ship_list, row, col, name, horizontal):
    length = SHIPS[name]
    cells = []
    for i in range(length):
        r = row if horizontal else row + i
        c = col + i if horizontal else col
        board[r][c] = SHIP
        cells.append((r, c)) # cells is list of tupples each one storing the coordinates of each tile of the ship
    ship_list.append({"name": name, "cells": cells, "hits": 0}) # ships is a list of dictionary storing details for each ship
    
    # EXAMPLE OF DESTROYER: ships = [{"name": "Destroyer", "cells": [(0, 0), (0, 1)], "hits": 0}]

def all_ships_sunk(ship_list):
    return all(ship["hits"] == len(ship["cells"]) for ship in ship_list) # the parameter for this function is ships dictionary



def fire_on_board(board, ship_list, row, col):
    cell = board[row][col]
    if cell in (HIT, MISS): # shorthand for if cell == HIT or cell == MISS
        return {"result": "already"} # the result is for giving the info to the caller
    if cell == WATER:
        board[row][col] = MISS
        return {"result": "miss"}
    
    board[row][col] = HIT
    for ship in ship_list:
        if (row, col) in ship["cells"]:
            ship["hits"] += 1
            if ship["hits"] == len(ship["cells"]):
                if all_ships_sunk(ship_list): # if all ships are sunk
                    return {"result": "sunk", "ship": ship["name"], "win": True} # Player wins
                return {"result": "sunk", "ship": ship["name"]} # result is sunk only for that ship
            return {"result": "hit", "ship": ship["name"]} # else only hit is done

def hide_unhit_ships(board):
    new_board = []
    for row in board:
        new_row = []
        for cell in row:
            if cell == SHIP:
                new_row.append(WATER)
            else:
                new_row.append(cell)
        new_board.append(new_row)
    return new_board


class Game:

    def __init__(self):
        self.players = {}        # {"p1": <player dict>, "p2": <player dict>}
        self.turn    = None      # "p1" or "p2" — set once both are ready
        self.over    = False
        self.winner  = None


    def add_player(self, player_id):
        # player_id is something the server gives you (e.g. a socket id)
        # Only allow up to 2 players.
        if len(self.players) >= 2 or player_id in self.players:
            return False
        self.players[player_id] = {
        
            "board":  create_board(),
            "ships":  [],          # same list-of-dicts as your original
            "ready":  False
        }
        # Once the second player joins, decide who goes first.
        if len(self.players) == 2 and self.turn is None:
            self.turn = next(iter(self.players))
        return True
    
    def _other(self, player_id):
        for pid in self.players:
            if pid != player_id:
                return pid
        return None


    def place_ships_random(self, player_id):
        # Reuse the ported functions above.
        player = self.players[player_id]
        if player["ready"] == True: #if player is already ready
            return
        place_all_ships(player["board"], player["ships"])
        player["ready"] = True


    def fire(self, player_id, row, col):
        # --- Guards: reject anything illegal ---
        if self.over:                       
            return {"error": "game over"}
        if player_id not in self.players:   
            return {"error": "not a player"}
        if not all(p["ready"] for p in self.players.values()):       
            return {"error": "placement not done"}
        if player_id != self.turn:          
            return {"error": "not your turn"}

        # --- Apply the shot to the OPPONENT's board ---
        opponent_id = self._other(player_id)
        opponent = self.players[opponent_id]
        result = fire_on_board(opponent["board"], opponent["ships"], row, col)

        if result["result"] == "already":
            return result      # don't flip turn — bad input, try again

        # player 1 wins
        if result.get("win"):
            self.over   = True
            self.winner = player_id

        # Otherwise, flip the turn
        else:
            self.turn = opponent_id

        return result


    def view_for(self, player_id):
        """JSON-safe snapshot, hiding info this player shouldn't see."""
        me = self.players[player_id]
        opponent_id = self._other(player_id)
        opponent = self.players[opponent_id] if opponent_id else None

        return {
            "your_board":  me["board"],
            "enemy_board": hide_unhit_ships(opponent["board"]) if opponent else create_board(),
            "your_turn":   player_id == self.turn,
            "over":        self.over,
            "winner":      self.winner,
            "you_are":     player_id,
            "opponent_here":  opponent is not None,
            "you_ready":      me["ready"],
            "opponent_ready": opponent["ready"] if opponent else False,
        }

