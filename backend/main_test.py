from fastapi.testclient import TestClient
from main import app, r, init_state
import json

client = TestClient(app)

def setup_function():
    # Reset Redis before each test.
    r.set("board", json.dumps([None] * 9))
    r.set("x_is_next", json.dumps(True))

def test_get_state():
    response = client.get("/api/state")
    assert response.status_code == 200
    data = response.json()
    assert "board" in data
    assert "x_is_next" in data
    assert isinstance(data["board"], list)
    assert isinstance(data["x_is_next"], bool)

def test_make_valid_move():
    response = client.post("/api/move/0")
    data = response.json()
    assert data["board"][0] in ["X", "O"]
    assert isinstance(data["x_is_next"], bool)
    assert data["status"] == "playing"

def test_make_invalid_move():
    client.post("/api/move/0")  # First move
    response = client.post("/api/move/0")  # Invalid move
    assert "error" in response.json()

def test_reset_game():
    client.post("/api/move/0")  # Make a move
    response = client.post("/api/reset", json={"reset_stats": True})
    data = response.json()
    assert response.status_code == 200
    assert data["board"] == [None] * 9
    assert data["x_is_next"] is True
    assert data["scores"] == {"X": 0, "O": 0, "draws": 0}
    assert data["history"] == []

def test_win_scenario():
    # X -> 0, O -> 3, X -> 1, O -> 4, X -> 2 (X wins)
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

def test_draw_scenario():
    client.post("/api/reset")

    # Sequence of moves that ends in a draw
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

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"games_played_total" in response.content