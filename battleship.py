import random

BOARD_SIZE  = 10
SHIPS = {"Carrier": 5, "Battleship": 4, "Cruiser": 3, "Submarine": 3, "Destroyer": 2}

hide_ships = False

WATER, SHIP, HIT, MISS = "~", "S", "X", "O"
def create_board():
    board = []  # empty list
    for _ in range(BOARD_SIZE):   # for each row
        row = [WATER] * BOARD_SIZE  # it's like ["~", "~", "~", .......]
        board.append(row)   # [["~", "~", "~", ...], ["~", "~", "~", .......], ["~", "~", "~", .......], ....]
    return board

def randomly_place_ship(board, ships, name):
    length =  SHIPS[name]
    while True:
        row, column = random.randint(0, BOARD_SIZE-1), random.randint(0, BOARD_SIZE-1)
        #name = random.choice(list(SHIPS))
        horizontal = random.choice([True, False])
        if can_place(board, row, column, length, name, horizontal):
            place_ship(board, ships, row, column, name, horizontal)
            break

def place_all_ships(board, ships):
    for name in SHIPS:
        randomly_place_ship (board, ships, name)
    
        

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
    
    
def place_ship(board, ships, row, col, name, horizontal):
    length = SHIPS[name]
    cells = []
    for i in range(length):
        r = row if horizontal else row + i
        c = col + i if horizontal else col
        board[r][c] = SHIP
        cells.append((r, c)) # cells is list of tupples each one storing the coordinates of each tile of the ship
    ships.append({"name": name, "cells": cells, "hits": 0}) # ships is a list of dictionary storing details for each ship
    
    # EXAMPLE OF DESTROYER: ships = [{"name": "Destroyer", "cells": [(0, 0), (0, 1)], "hits": 0}]
    
    
def all_ships_sunk(ships):
    return all(ship["hits"] == len(ship["cells"]) for ship in ships) # the parameter for this function is ships dictionary


def fire(board, row, col, ships):
    cell = board[row][col]
    if cell in (HIT, MISS): # shorthand for if cell == HIT or cell == MISS
        return {"result": "already"} # the result is for giving the info to the caller
    if cell == WATER:
        board[row][col] = MISS
        return {"result": "miss"}
    
    board[row][col] = HIT
    for ship in ships:
        if (row, col) in ship["cells"]:
            ship["hits"] += 1
            if ship["hits"] == len(ship["cells"]):
                if all_ships_sunk(ships): # if all ships are sunk
                    return {"result": "sunk", "ship": ship["name"], "win": True} # Player wins
                return {"result": "sunk", "ship": ship["name"]} # result is sunk only for that ship
            return {"result": "hit", "ship": ship["name"]} # else only hit is done
        
def display_board(board, hide_ships):
    # for printing the grid numbers.
    header = " ".join(f"{c+1:>2}" for c in range(BOARD_SIZE))
    print("   " + header)
    for r in range(BOARD_SIZE):
        cells = []
        for c in range(BOARD_SIZE):
            cell = board[r][c]
            if hide_ships and cell == SHIP:
                cell = WATER
            cells.append(f"{cell:>2}")  # this f string ensure that cell(text) appends to the right instead of left
            
        print(f"{r+1:>2} " + " ".join(cells)) # joins the strings together and turns the list into a string like "~ ~ ~ ~ ....."
            
        
    
    
def ask_input(prompt, low, high):
    while True:
        try:
            value = int(input(prompt))
            if low <= value <= high:
                return value
        except ValueError:
            pass
        print(f"Give a value between {low} and {high}.")
    

board = create_board()
ships = []
place_all_ships(board, ships)
print(len(ships))
display_board(board, hide_ships=False)
