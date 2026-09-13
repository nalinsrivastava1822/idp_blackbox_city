from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import SimulationStart
from app.services.risk_engine import train_demo_model
from app.services.simulation import CitySimulation

ROOT = Path(__file__).resolve().parents[1]
app = FastAPI(title="BLACKBOX CITY", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
simulation = CitySimulation()

@app.get("/", include_in_schema=False)
def command_center(): return FileResponse(ROOT / "static" / "index.html")
@app.get("/api/health")
def health(): return {"status": "ok", "service": "BLACKBOX CITY prototype"}
@app.get("/api/dashboard")
def dashboard(): return simulation.dashboard()
@app.get("/api/patients")
def patients(): return simulation.dashboard()["patients"]
@app.get("/api/patients/{patient_id}")
def patient(patient_id: str):
    for item in simulation.dashboard()["patients"]:
        if item["patient_id"] == patient_id: return item
    raise HTTPException(status_code=404, detail="Patient Twin not found")
@app.get("/api/health/summary")
def health_summary(): return simulation.dashboard()["health"]
@app.get("/api/city/summary")
def city_summary(): return simulation.dashboard()["city"]
@app.post("/api/simulation/start")
def start_simulation(payload: SimulationStart): return simulation.start(payload.scenario, payload.seed)
@app.post("/api/simulation/step")
def simulation_step(): return simulation.step()
@app.post("/api/simulation/reset")
def reset_simulation(): return simulation.reset()
@app.post("/api/ml/train")
def train_model(seed: int = 42): return {**train_demo_model(seed), "warning": "Trained on generated demo data, not clinical data."}
