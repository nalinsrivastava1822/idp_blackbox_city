from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.schemas import RiskAssessment, RiskLevel, VitalObservation


FEATURES = ["heart_rate", "spo2", "respiratory_rate", "temperature", "wheeze_probability"]
MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "synthetic_vital_risk_model.joblib"
SAFETY_NOTE = "Synthetic prototype output only — not a clinical diagnosis or treatment recommendation."


def _synthetic_training_set(seed: int = 42, rows: int = 3000) -> tuple[np.ndarray, np.ndarray]:
    """Create labelled simulation data, never clinical training data."""
    rng = np.random.default_rng(seed)
    severity = rng.choice([0, 1, 2], size=rows, p=[0.62, 0.25, 0.13])
    heart_rate = rng.normal(76 + severity * 15, 7, rows).clip(45, 185)
    spo2 = rng.normal(98 - severity * 3.2, 1.0, rows).clip(70, 100)
    respiratory_rate = rng.normal(15 + severity * 5, 2.0, rows).clip(8, 48)
    temperature = rng.normal(36.8 + severity * 0.75, 0.35, rows).clip(34, 42)
    wheeze_probability = rng.beta(1 + severity * 2.8, 8 - severity * 1.6, rows).clip(0, 1)
    features = np.column_stack((heart_rate, spo2, respiratory_rate, temperature, wheeze_probability))
    labels = np.array(["LOW", "MODERATE", "HIGH"], dtype=object)[severity]
    return features, labels


def train_demo_model(seed: int = 42) -> dict[str, object]:
    """Train and persist the clearly-labelled synthetic demo model."""
    X, y = _synthetic_training_set(seed)
    model = RandomForestClassifier(n_estimators=160, max_depth=10, random_state=seed, class_weight="balanced")
    model.fit(X, y)
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES, "kind": "SYNTHETIC_DEMO", "seed": seed}, MODEL_PATH)
    return {"model_status": "SYNTHETIC_DEMO_TRAINED", "samples": len(y), "features": FEATURES, "seed": seed}


class SyntheticRiskEngine:
    def __init__(self) -> None:
        if not MODEL_PATH.exists():
            train_demo_model()
        package = joblib.load(MODEL_PATH)
        self.model = package["model"]

    def assess(self, observation: VitalObservation) -> RiskAssessment:
        row = np.array([[getattr(observation, feature) for feature in FEATURES]])
        probabilities = self.model.predict_proba(row)[0]
        probability_by_class = {str(label): float(value) for label, value in zip(self.model.classes_, probabilities, strict=True)}
        level = max(probability_by_class, key=probability_by_class.get)
        return RiskAssessment(
            risk_level=RiskLevel(level),
            model_confidence=round(probability_by_class[level], 4),
            class_probabilities={RiskLevel(key): round(value, 4) for key, value in probability_by_class.items()},
            model_status="SYNTHETIC_DEMO_MODEL",
            safety_note=SAFETY_NOTE,
        )
