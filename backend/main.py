from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import os

app = FastAPI()

# Allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains to access the backend
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Connect to Redis (use service name inside cluster)
redis_host = os.getenv("REDIS_HOST", "redis-service")  # update to your service name
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

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

# GET current state
@app.get("/api/state")
def api_get_state():
    board, x_is_next = get_state()
    return {"board": board, "x_is_next": x_is_next}

# POST make a move
@app.post("/api/move/{index}")
def make_move(index: int):
    board, x_is_next = get_state()
    if board[index] is not None:
        return {"error": "Invalid move"}

    board[index] = "X" if x_is_next else "O"
    x_is_next = not x_is_next
    save_state(board, x_is_next)

    return {"board": board, "x_is_next": x_is_next}

# POST reset game
@app.post("/api/reset")
def reset_game():
    save_state([None] * 9, True)
    return {"board": [None] * 9, "x_is_next": True}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}