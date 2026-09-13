import json
import joblib
import numpy as np
import threading
from pathlib import Path
from backend.llm_inference import explain_patient

MODEL_PATH = Path(__file__).resolve().parent / "models" / "patient_risk_model.joblib"
# Use the existing demo model if it's there
if not MODEL_PATH.exists():
    MODEL_PATH = Path(__file__).resolve().parent / "models" / "synthetic_vital_risk_model.joblib"

class CommandEngine:
    def __init__(self):
        try:
            package = joblib.load(MODEL_PATH)
            self.ml_model = package["model"]
            self.features = package.get("features", ["heart_rate", "spo2", "respiratory_rate", "temperature", "wheeze_probability"])
        except Exception as e:
            print(f"Warning: Could not load ML model: {e}")
            self.ml_model = None

    def assess_risk(self, patient_data: dict) -> dict:
        if not self.ml_model:
            return {"risk_level": "UNKNOWN", "confidence": 0.0}
        
        row = np.array([[patient_data.get(f, 0) for f in self.features]])
        try:
            probs = self.ml_model.predict_proba(row)[0]
            classes = getattr(self.ml_model, "classes_", ["LOW", "MODERATE", "HIGH"])
            prob_dict = {str(c): float(p) for c, p in zip(classes, probs)}
            level = max(prob_dict, key=prob_dict.get)
            return {
                "risk_level": level,
                "confidence": prob_dict[level],
                "class_probabilities": prob_dict
            }
        except Exception as e:
            print(f"Prediction error: {e}")
            return {"risk_level": "UNKNOWN", "confidence": 0.0}

    def generate_explanation(self, combined_data: dict, timeout: int = 30) -> dict:
        result = {}
        
        def run_llm():
            try:
                resp = explain_patient(combined_data)
                result["data"] = json.loads(resp)
            except Exception as e:
                result["error"] = str(e)
                
        thread = threading.Thread(target=run_llm)
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            # Timeout hit
            return {
                "summary": "Explanation pending/unavailable (Timeout).",
                "risk_assessment": {"level": combined_data.get("risk_level", "UNKNOWN")},
                "recommended_action": "Follow standard protocol for raw risk level.",
                "explanation_unavailable": True
            }
        
        if "error" in result:
             return {
                "summary": f"Explanation pending/unavailable (Error).",
                "risk_assessment": {"level": combined_data.get("risk_level", "UNKNOWN")},
                "recommended_action": "Follow standard protocol for raw risk level.",
                "explanation_unavailable": True
            }
            
        return result.get("data", {})

    def run_what_if_simulation(self, scenario: str, current_hospitals: list) -> list:
        # Lightweight rule-based heuristics
        simulated_hospitals = []
        for h in current_hospitals:
            h_sim = dict(h)
            if "capacity drops" in scenario.lower() and h_sim.get("capacity", 0) > 0:
                h_sim["capacity"] = max(10, int(h_sim["capacity"] * 0.7))
            
            if h_sim["current_occupancy"] > h_sim["capacity"]:
                h_sim["status"] = "OVERLOADED"
                
            simulated_hospitals.append(h_sim)
        return simulated_hospitals
