import asyncio
import json
import random
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import SessionLocal, init_db, PatientDT, HospitalDT, CommunicationDT

# ── Hardcoded demo data ────────────────────────────────────────────
DEMO_HOSPITALS = [
    {"id": "H1", "name": "City General Hospital",   "capacity": 500, "occupancy": 437},
    {"id": "H2", "name": "Mercy Medical Center",    "capacity": 250, "occupancy": 241},
    {"id": "H3", "name": "Westside Clinic",          "capacity": 100, "occupancy": 38},
    {"id": "H4", "name": "St. Jude's ER",            "capacity": 300, "occupancy": 288},
    {"id": "H5", "name": "Metro Trauma Institute",   "capacity": 180, "occupancy": 175},
]

DEMO_PATIENTS = [
    {"id": "PAT-001", "name": "Aarav Mehta",      "severity": 2},
    {"id": "PAT-002", "name": "Priya Sharma",     "severity": 1},
    {"id": "PAT-003", "name": "Rohan Gupta",      "severity": 0},
    {"id": "PAT-004", "name": "Neha Patel",       "severity": 2},
    {"id": "PAT-005", "name": "Vikram Singh",     "severity": 1},
    {"id": "PAT-006", "name": "Ananya Das",       "severity": 0},
    {"id": "PAT-007", "name": "Arjun Reddy",      "severity": 1},
    {"id": "PAT-008", "name": "Kavya Nair",       "severity": 2},
    {"id": "PAT-009", "name": "Ishaan Joshi",     "severity": 0},
    {"id": "PAT-010", "name": "Riya Kapoor",      "severity": 1},
    {"id": "PAT-011", "name": "Aditya Rao",       "severity": 2},
    {"id": "PAT-012", "name": "Simran Kaur",      "severity": 0},
]

connected_websockets: list[WebSocket] = []
network_mode = "WIFI"

# ── Helper: generate vitals based on severity ──────────────────────
def gen_vitals(severity: int):
    if severity == 0:
        return {
            "hr": round(random.uniform(62, 88), 1),
            "spo2": round(random.uniform(96, 100), 1),
            "rr": round(random.uniform(12, 18), 1),
            "temp": round(random.uniform(36.4, 37.2), 1),
            "wheeze": round(random.uniform(0.0, 0.15), 3),
        }
    elif severity == 1:
        return {
            "hr": round(random.uniform(90, 120), 1),
            "spo2": round(random.uniform(90, 95), 1),
            "rr": round(random.uniform(20, 28), 1),
            "temp": round(random.uniform(37.5, 38.5), 1),
            "wheeze": round(random.uniform(0.2, 0.55), 3),
        }
    else:
        return {
            "hr": round(random.uniform(120, 155), 1),
            "spo2": round(random.uniform(82, 90), 1),
            "rr": round(random.uniform(28, 40), 1),
            "temp": round(random.uniform(38.5, 40.5), 1),
            "wheeze": round(random.uniform(0.6, 0.95), 3),
        }

RISK_MAP = {0: "LOW", 1: "MODERATE", 2: "HIGH"}

def severity_to_explanation(sev, vitals):
    if sev == 2:
        return {
            "summary": f"Critical patient. HR {vitals['hr']} bpm is dangerously elevated, SpO2 {vitals['spo2']}% indicates hypoxemia, temperature {vitals['temp']}°C suggests high fever. Wheeze probability {vitals['wheeze']:.0%} signals respiratory distress.",
            "risk_assessment": {"level": "HIGH", "confidence": 0.92},
            "recommended_action": "Immediate ICU triage. Administer supplemental O2, start IV fluids, prepare for intubation if SpO2 drops below 85%.",
        }
    elif sev == 1:
        return {
            "summary": f"Moderate concern. HR {vitals['hr']} bpm is mildly elevated, SpO2 {vitals['spo2']}% is borderline, temperature {vitals['temp']}°C indicates low-grade fever. Monitor closely.",
            "risk_assessment": {"level": "MODERATE", "confidence": 0.78},
            "recommended_action": "Move to observation ward. Re-check vitals every 15 minutes. Administer antipyretics if temp exceeds 38.5°C.",
        }
    else:
        return {
            "summary": f"Stable patient. All vitals within normal range — HR {vitals['hr']} bpm, SpO2 {vitals['spo2']}%, temp {vitals['temp']}°C. No respiratory distress detected.",
            "risk_assessment": {"level": "LOW", "confidence": 0.95},
            "recommended_action": "Continue routine monitoring. Schedule next check-up in 1 hour.",
        }

# ── Seed the database ──────────────────────────────────────────────
def seed_db():
    db = SessionLocal()
    # Clear stale data
    db.query(PatientDT).delete()
    db.query(HospitalDT).delete()
    db.query(CommunicationDT).delete()
    db.commit()

    for h in DEMO_HOSPITALS:
        db.add(HospitalDT(
            id=h["id"], name=h["name"],
            capacity=h["capacity"], current_occupancy=h["occupancy"],
            status="OVERLOADED" if h["occupancy"]/h["capacity"] > 0.9 else "NORMAL"
        ))

    for p in DEMO_PATIENTS:
        v = gen_vitals(p["severity"])
        risk = RISK_MAP[p["severity"]]
        expl = severity_to_explanation(p["severity"], v)
        db.add(PatientDT(
            id=p["id"],
            heart_rate=v["hr"], spo2=v["spo2"],
            respiratory_rate=v["rr"], temperature=v["temp"],
            wheeze_probability=v["wheeze"],
            risk_level=risk,
            llm_explanation=json.dumps(expl),
        ))

    db.add(CommunicationDT(id="primary", network_status="WIFI"))
    db.commit()
    db.close()
    print(f"[OK] Seeded {len(DEMO_HOSPITALS)} hospitals, {len(DEMO_PATIENTS)} patients")

# ── Background task: simulate live vital drift ─────────────────────
async def simulate_vitals_loop():
    """Every 3 seconds, jitter a random patient's vitals and push to WS."""
    while True:
        await asyncio.sleep(3)
        db = SessionLocal()
        patients = db.query(PatientDT).all()
        if not patients:
            db.close()
            continue

        # Pick 2-3 random patients to update
        sample = random.sample(patients, min(3, len(patients)))
        for p in sample:
            # Find original severity from DEMO_PATIENTS
            orig = next((d for d in DEMO_PATIENTS if d["id"] == p.id), None)
            sev = orig["severity"] if orig else 0
            # Occasionally flip severity for drama
            if random.random() < 0.08:
                sev = min(2, sev + 1)
            v = gen_vitals(sev)
            p.heart_rate = v["hr"]
            p.spo2 = v["spo2"]
            p.respiratory_rate = v["rr"]
            p.temperature = v["temp"]
            p.wheeze_probability = v["wheeze"]
            p.risk_level = RISK_MAP[sev]
            p.llm_explanation = json.dumps(severity_to_explanation(sev, v))

        # Jitter a hospital occupancy too
        hosp = random.choice(db.query(HospitalDT).all())
        hosp.current_occupancy = max(0, min(hosp.capacity, hosp.current_occupancy + random.randint(-3, 3)))
        hosp.status = "OVERLOADED" if hosp.current_occupancy / hosp.capacity > 0.9 else "NORMAL"

        db.commit()

        # Push update to all connected websockets
        state = get_full_state(db)
        db.close()
        dead = []
        for ws in connected_websockets:
            try:
                await ws.send_json(state)
            except Exception:
                dead.append(ws)
        for ws in dead:
            connected_websockets.remove(ws)

# ── State helper ───────────────────────────────────────────────────
def get_full_state(db: Session):
    patients = []
    for p in db.query(PatientDT).all():
        patients.append({
            "id": p.id,
            "hr": p.heart_rate,
            "spo2": p.spo2,
            "rr": p.respiratory_rate,
            "temp": p.temperature,
            "risk": p.risk_level,
        })
    hospitals = []
    for h in db.query(HospitalDT).all():
        hospitals.append({
            "id": h.id, "name": h.name,
            "occupancy": h.current_occupancy, "capacity": h.capacity,
            "status": h.status,
        })
    net = db.query(CommunicationDT).filter_by(id="primary").first()
    return {
        "patients": patients,
        "hospitals": hospitals,
        "network": net.network_status if net else "WIFI",
    }

# ── Lifespan ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_db()
    task = asyncio.create_task(simulate_vitals_loop())
    print("[OK] Backend live - simulating vitals every 3s")
    yield
    task.cancel()

# ── App ────────────────────────────────────────────────────────────
app = FastAPI(title="BLACKBOX CITY Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/state")
def api_state(db: Session = Depends(get_db)):
    return get_full_state(db)

@app.get("/api/patients/{patient_id}")
def api_patient(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(PatientDT).filter_by(id=patient_id).first()
    if not p:
        return {"error": "Patient not found"}
    expl = {}
    try:
        expl = json.loads(p.llm_explanation) if isinstance(p.llm_explanation, str) else p.llm_explanation or {}
    except Exception:
        expl = {"summary": "Explanation unavailable", "recommended_action": "Follow standard protocol."}
    return {
        "id": p.id,
        "vitals": {"hr": p.heart_rate, "spo2": p.spo2, "temp": p.temperature, "rr": p.respiratory_rate},
        "risk_level": p.risk_level,
        "explanation": expl,
    }

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    # Send initial state immediately on connect
    db = SessionLocal()
    await websocket.send_json(get_full_state(db))
    db.close()
    try:
        while True:
            await websocket.receive_text()  # keep-alive
    except Exception:
        pass
    finally:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
