from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import os
from datetime import datetime
from pydantic import BaseModel

from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST, Info
from fastapi.responses import Response as FastAPIResponse

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
app_info = Info("app_info", "Basic app metadata")
app_info.info({
    "version": "1.0.0",
    "language": "python",
    "framework": "fastapi"
})
games_played = Counter("games_played_total", "Total number of games played")
full_game_resets_total = Counter("full_game_resets_total", "Total number of game resets")
x_wins = Counter("x_wins_total", "Total wins by player X")
o_wins = Counter("o_wins_total", "Total wins by player O")
draws = Counter("draws_total", "Total number of drawn games")

invalid_moves = Counter(
    "invalid_moves_total", 
    "Total number of invalid moves", 
    ["reason"]
)

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

def get_scores():
    if r.exists("scores"):
        return json.loads(r.get("scores"))
    return {"X": 0, "O": 0, "draws": 0}

def save_scores(scores):
    r.set("scores", json.dumps(scores))

def get_history():
    if r.exists("history"):
        return json.loads(r.get("history"))
    return []

def save_history(history):
    r.set("history", json.dumps(history))

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
    if index < 0 or index >= 9:
        invalid_moves.labels(reason="out_of_bounds").inc()
        return {"error": "Invalid move - index out of bounds"}

    board, x_is_next = get_state()

    if board[index] is not None:
        invalid_moves.labels(reason="cell_taken").inc()
        return {"error": "Invalid move - cell_taken"}

    board[index] = "X" if x_is_next else "O"
    x_is_next = not x_is_next
    save_state(board, x_is_next)

    # Determine game status
    result = calculate_winner(board)
    if result:
        games_played.inc()
        winner = result["winner"]

        scores = get_scores()
        scores[winner] += 1
        save_scores(scores)

        history = get_history()
        history.append({
            "winner": winner,
            "board": board,
            "timestamp": str(datetime.utcnow())
        })
        save_history(history)

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
        draws.inc()
        games_played.inc()

        scores = get_scores()
        scores["draws"] += 1
        save_scores(scores)

        history = get_history()
        history.append({
            "winner": None,
            "board": board,
            "timestamp": str(datetime.utcnow())
        })
        save_history(history)

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

@app.get("/api/scores")
def get_score_data():
    return get_scores()

@app.get("/api/history")
def get_game_history():
    return get_history()

class ResetRequest(BaseModel):
    reset_stats: bool = False

@app.post("/api/reset")
def reset_game(payload: ResetRequest):
    save_state([None] * 9, True)

    response = {
        "board": [None] * 9,
        "x_is_next": True
    }

    if payload.reset_stats:
        full_game_resets_total.inc()
        save_scores({"X": 0, "O": 0, "draws": 0})
        save_history([])
        response["scores"] = get_scores()
        response["history"] = get_history()

    return response

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Prometheus metrics endpoint
@app.get("/metrics")
def metrics():
    return FastAPIResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
        headers={"Cache-Control": "no-store"}
    )