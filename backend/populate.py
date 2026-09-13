import os
import random
from sqlalchemy.orm import Session
from backend.database import SessionLocal, init_db, PatientDT, HospitalDT, CommunicationDT

def populate_mock_data():
    db = SessionLocal()
    
    # Add hospitals
    hospitals = [
        {"id": "H1", "name": "City General Hospital", "capacity": 500, "occupancy": 450},
        {"id": "H2", "name": "Mercy Medical Center", "capacity": 250, "occupancy": 240},
        {"id": "H3", "name": "Westside Clinic", "capacity": 100, "occupancy": 40},
        {"id": "H4", "name": "St. Jude's ER", "capacity": 300, "occupancy": 295}, # high risk
    ]
    
    for h in hospitals:
        existing = db.query(HospitalDT).filter_by(id=h["id"]).first()
        if not existing:
            h_dt = HospitalDT(
                id=h["id"], 
                name=h["name"], 
                capacity=h["capacity"], 
                current_occupancy=h["occupancy"], 
                status="OVERLOADED" if (h["occupancy"]/h["capacity"] > 0.9) else "NORMAL"
            )
            db.add(h_dt)
        else:
            existing.current_occupancy = h["occupancy"]
            
    # Add some mock patients
    for i in range(1, 15):
        pid = f"PAT-SIM-{i}"
        severity = random.choice([0, 1, 1, 2]) # skew towards moderate/high for demo
        hr = random.uniform(60, 100) if severity == 0 else random.uniform(100, 140)
        spo2 = random.uniform(95, 100) if severity == 0 else random.uniform(85, 94)
        rr = random.uniform(12, 20) if severity == 0 else random.uniform(20, 35)
        temp = random.uniform(36.5, 37.5) if severity == 0 else random.uniform(37.5, 39.5)
        
        risk = "HIGH" if severity == 2 else "MODERATE" if severity == 1 else "LOW"
        
        existing = db.query(PatientDT).filter_by(id=pid).first()
        if not existing:
            p_dt = PatientDT(
                id=pid,
                heart_rate=hr,
                spo2=spo2,
                respiratory_rate=rr,
                temperature=temp,
                wheeze_probability=random.uniform(0, 1),
                risk_level=risk
            )
            db.add(p_dt)
            
    # Add network
    net = db.query(CommunicationDT).filter_by(id="primary").first()
    if not net:
        db.add(CommunicationDT(id="primary", network_status="WIFI"))
        
    db.commit()
    db.close()
    print("Successfully populated SQLite DB with demo Hospitals and Patients!")

if __name__ == "__main__":
    populate_mock_data()
