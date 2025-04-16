from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains to access the backend
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# In-memory data (for now)
game_state = {
    "board": [None] * 9,
    "x_is_next": True
}

@app.get("/api/state")
def get_state():
    return game_state

@app.post("/api/move/{index}")
def make_move(index: int):
    if game_state["board"][index] is not None:
        return {"error": "Invalid move"}
    game_state["board"][index] = "X" if game_state["x_is_next"] else "O"
    game_state["x_is_next"] = not game_state["x_is_next"]
    return game_state

@app.post("/api/reset")
def reset_game():
    game_state["board"] = [None] * 9
    game_state["x_is_next"] = True
    return game_state

@app.get("/health")
def health_check():
    return {"status": "ok"}
