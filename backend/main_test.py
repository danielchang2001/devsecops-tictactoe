from fastapi.testclient import TestClient
from main import app, r, init_state
import json

client = TestClient(app)

# Reset Redis before each test to ensure a clean state
def setup_function():
    r.set("board", json.dumps([None] * 9))
    r.set("x_is_next", json.dumps(True))

# Test retrieving the current game state
def test_get_state():
    response = client.get("/api/state")
    assert response.status_code == 200
    data = response.json()
    assert "board" in data
    assert "x_is_next" in data
    assert isinstance(data["board"], list)
    assert isinstance(data["x_is_next"], bool)

# Test making a valid move updates the board correctly
def test_make_valid_move():
    response = client.post("/api/move/0")
    data = response.json()
    assert data["board"][0] in ["X", "O"]
    assert isinstance(data["x_is_next"], bool)
    assert data["status"] == "playing"

# Test making an invalid move (on an already occupied cell) returns an error
def test_make_invalid_move():
    client.post("/api/move/0")  # First move
    response = client.post("/api/move/0")  # Try move again on same cell
    assert "error" in response.json()

# Test resetting the game clears board state, scores, and history
def test_reset_game():
    client.post("/api/move/0")  # Make a move
    response = client.post("/api/reset", json={"reset_stats": True})
    data = response.json()
    assert response.status_code == 200
    assert data["board"] == [None] * 9
    assert data["x_is_next"] is True
    assert data["scores"] == {"X": 0, "O": 0, "draws": 0}
    assert data["history"] == []

# Test a full win scenario (X wins)
def test_win_scenario():
    # Board:
    #  X | X | X  <---
    #  0 | O | .
    #  . | . | .
    client.post("/api/reset")
    client.post("/api/move/0")
    client.post("/api/move/3")
    client.post("/api/move/1")
    client.post("/api/move/4")
    response = client.post("/api/move/2")
    data = response.json()
    assert data["status"] == "won"
    assert data["winner"] == "X"
    assert "winning_line" in data

# Test a full draw scenario (no winners)
def test_draw_scenario():
    client.post("/api/reset")
    # Board:
    #  X | O | X
    #  O | O | X
    #  X | X | O
    moves = [0, 1, 2, 3, 5, 4, 6, 8, 7]

    for i, move in enumerate(moves):
        response = client.post(f"/api/move/{move}")
        assert response.status_code == 200
        if i == len(moves) - 1:
            data = response.json()
            assert data["status"] == "draw"

# Test backend health check endpoint
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Test Prometheus metrics endpoint is exposed
def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"games_played_total" in response.content