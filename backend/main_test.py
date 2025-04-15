from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_state():
    response = client.get("/api/state")
    assert response.status_code == 200
    assert "board" in response.json()
    assert len(response.json()["board"]) == 9

def test_make_valid_move():
    client.post("/api/reset")  # Reset before move
    response = client.post("/api/move/0")
    data = response.json()
    assert data["board"][0] == "X" or data["board"][0] == "O"

def test_make_invalid_move():
    client.post("/api/reset")
    client.post("/api/move/0")  # First move
    response = client.post("/api/move/0")  # Invalid move on same spot
    assert "error" in response.json()

def test_reset_game():
    client.post("/api/move/0")
    response = client.post("/api/reset")
    assert response.json()["board"] == [None] * 9
