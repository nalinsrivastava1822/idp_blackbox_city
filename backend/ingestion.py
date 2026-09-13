import pandas as pd
from sqlalchemy.orm import Session
from backend.database import PopulationDT, HospitalDT

def ingest_population_data(db: Session, csv_path: str):
    try:
        df = pd.read_csv(csv_path)
        # Attempt to map columns flexibly
        region_col = next((c for c in df.columns if "region" in c.lower() or "city" in c.lower() or "district" in c.lower()), None)
        score_col = next((c for c in df.columns if "score" in c.lower() or "health" in c.lower()), None)
        
        if not region_col:
            print("Fallback: could not find region column in population data.")
            return

        for _, row in df.iterrows():
            region = str(row[region_col])
            score = float(row[score_col]) if score_col else 0.0
            
            pop_dt = db.query(PopulationDT).filter_by(id=region).first()
            if not pop_dt:
                pop_dt = PopulationDT(id=region, region=region, anomaly_score=score, dominant_symptoms="None")
                db.add(pop_dt)
            else:
                pop_dt.anomaly_score = score
        db.commit()
    except Exception as e:
        print(f"Error ingesting population data: {e}")

def ingest_hospital_data(db: Session, csv_path: str):
    try:
        df = pd.read_csv(csv_path)
        name_col = next((c for c in df.columns if "name" in c.lower() or "hospital" in c.lower()), None)
        cap_col = next((c for c in df.columns if "cap" in c.lower() or "beds" in c.lower()), None)

        if not name_col:
            print("Fallback: could not find name column in hospital data.")
            return

        for _, row in df.iterrows():
            name = str(row[name_col])
            cap = int(row[cap_col]) if cap_col else 100
            
            h_dt = db.query(HospitalDT).filter_by(id=name).first()
            if not h_dt:
                h_dt = HospitalDT(id=name, name=name, capacity=cap, current_occupancy=0, status="NORMAL")
                db.add(h_dt)
            else:
                h_dt.capacity = cap
        db.commit()
    except Exception as e:
        print(f"Error ingesting hospital data: {e}")
