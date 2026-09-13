from app.schemas import VitalObservation
from app.services.risk_engine import SyntheticRiskEngine, train_demo_model


def test_demo_model_trains_and_returns_probabilities(tmp_path, monkeypatch):
    import app.services.risk_engine as module
    monkeypatch.setattr(module, "MODEL_PATH", tmp_path / "model.joblib")
    result = train_demo_model(seed=7)
    assessment = SyntheticRiskEngine().assess(VitalObservation(heart_rate=75, spo2=98, respiratory_rate=15, temperature=36.8, wheeze_probability=0.05))
    assert result["samples"] == 3000
    assert assessment.model_status == "SYNTHETIC_DEMO_MODEL"
    assert abs(sum(assessment.class_probabilities.values()) - 1) < 0.001
