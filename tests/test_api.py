from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_and_simulation_flow():
    assert client.get("/api/health").status_code == 200
    start = client.post("/api/simulation/start", json={"scenario": "FLOOD", "seed": 19})
    assert start.status_code == 200
    state = client.post("/api/simulation/step").json()
    assert state["simulation"]["step"] == 1
    assert state["city"]["road_status"] == "BLOCKED"
