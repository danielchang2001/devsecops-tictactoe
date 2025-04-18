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
    assert isinstance(data, list)
    assert len(data) == 2
    assert len(data[0]) == 9  # board
    assert isinstance(data[1], bool)  # x_is_next

def test_make_valid_move():
    response = client.post("/api/move/0")
    data = response.json()
    assert data["board"][0] in ["X", "O"]
    assert isinstance(data["x_is_next"], bool)

def test_make_invalid_move():
    client.post("/api/move/0")  # First move
    response = client.post("/api/move/0")  # Invalid move
    assert "error" in response.json()

def test_reset_game():
    client.post("/api/move/0")  # Make a move
    response = client.post("/api/reset")
    data = response.json()
    assert data["board"] == [None] * 9
    assert data["x_is_next"] == True

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}