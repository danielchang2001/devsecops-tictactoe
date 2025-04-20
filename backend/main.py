from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import os

from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

app = FastAPI()

# Allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains to access the backend
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Connect to Redis (use service name inside cluster)
redis_host = os.getenv("REDIS_HOST", "redis")  # update to your service name
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

# Prometheus Metrics
games_played = Counter("games_played_total", "Total number of games played")
game_resets = Counter("game_resets_total", "Total number of game resets")
invalid_moves = Counter("invalid_moves_total", "Total number of invalid moves")
x_wins = Counter("x_wins_total", "Total wins by player X")
o_wins = Counter("o_wins_total", "Total wins by player O")

# Initialize game state in Redis if missing
def init_state():
    if not r.exists("board"):
        r.set("board", json.dumps([None] * 9))
        r.set("x_is_next", json.dumps(True))

# Helper to get game state from Redis
def get_state():
    init_state()
    board = json.loads(r.get("board"))
    x_is_next = json.loads(r.get("x_is_next"))
    return board, x_is_next

# Helper to save game state back to Redis
def save_state(board, x_is_next):
    r.set("board", json.dumps(board))
    r.set("x_is_next", json.dumps(x_is_next))

def calculate_winner(board):
    # All winning line combinations
    winning_combos = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
        [0, 4, 8], [2, 4, 6]              # diagonals
    ]
    
    for combo in winning_combos:
        a, b, c = combo
        if board[a] and board[a] == board[b] == board[c]:
            return {"winner": board[a], "line": combo}
    
    return None

def check_draw(board):
    return all(cell is not None for cell in board)


# GET current state
@app.get("/api/state")
def api_get_state():
    board, x_is_next = get_state()
    result = calculate_winner(board)
    
    if result:
        return {
            "board": board,
            "x_is_next": x_is_next,
            "status": "won",
            "winner": result["winner"],
            "winning_line": result["line"]
        }
    elif check_draw(board):
        return {
            "board": board,
            "x_is_next": x_is_next,
            "status": "draw"
        }
    else:
        return {
            "board": board,
            "x_is_next": x_is_next,
            "status": "playing"
        }

# POST make a move
@app.post("/api/move/{index}")
def make_move(index: int):
    board, x_is_next = get_state()
    if board[index] is not None:
        invalid_moves.inc()
        return {"error": "Invalid move"}

    board[index] = "X" if x_is_next else "O"
    x_is_next = not x_is_next
    save_state(board, x_is_next)

    # Determine game status
    result = calculate_winner(board)
    if result:
        games_played.inc()
        winner = result["winner"]
        if winner == "X":
            x_wins.inc()
        elif winner == "O":
            o_wins.inc()
        return {
            "board": board,
            "x_is_next": x_is_next,
            "status": "won",
            "winner": result["winner"],
            "winning_line": result["line"]
        }

    if check_draw(board):
        games_played.inc()
        return {
            "board": board,
            "x_is_next": x_is_next,
            "status": "draw"
        }

    return {
        "board": board,
        "x_is_next": x_is_next,
        "status": "playing"
    }

# POST reset game
@app.post("/api/reset")
def reset_game():
    game_resets.inc()
    save_state([None] * 9, True)
    return {"board": [None] * 9, "x_is_next": True}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Prometheus metrics endpoint
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
