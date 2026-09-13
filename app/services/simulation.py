from __future__ import annotations

from datetime import UTC, datetime
import random

from app.schemas import Patient, Scenario, VitalObservation
from app.services.risk_engine import SyntheticRiskEngine


PATIENTS = [("PT-001", "North", 34), ("PT-002", "North", 51), ("PT-003", "East", 47), ("PT-004", "East", 29), ("PT-005", "Central", 63), ("PT-006", "Central", 42), ("PT-007", "South", 55), ("PT-008", "South", 38), ("PT-009", "West", 68), ("PT-010", "West", 46), ("PT-011", "North", 31), ("PT-012", "Central", 59)]


class CitySimulation:
    def __init__(self) -> None:
        self.engine = SyntheticRiskEngine()
        self.reset()

    def reset(self) -> dict:
        self.scenario, self.seed, self.rng, self.step_number = Scenario.NORMAL, 42, random.Random(42), 0
        self.events, self.patients = ["Simulation reset — all data below is simulated."], []
        self._refresh_patients()
        return self.dashboard()

    def start(self, scenario: Scenario, seed: int) -> dict:
        self.scenario, self.seed, self.rng, self.step_number = scenario, seed, random.Random(seed), 0
        self.events = [f"{scenario.replace('_', ' ').title()} scenario started — simulated data."]
        self._refresh_patients()
        return self.dashboard()

    def step(self) -> dict:
        self.step_number += 1
        self._refresh_patients()
        self.events.append(f"Timestep {self.step_number}: twin state recalculated from simulated inputs.")
        return self.dashboard()

    def _scenario_pressure(self, index: int) -> int:
        if self.scenario == Scenario.RESPIRATORY_OUTBREAK: return 1 if index % 3 else 2
        if self.scenario == Scenario.FLOOD: return 1 if index % 4 else 2
        if self.scenario == Scenario.HOSPITAL_OVERLOAD: return 1 if index % 2 else 2
        if self.scenario == Scenario.NETWORK_FAILURE: return 1 if index % 5 else 2
        return 1 if index == 0 and self.step_number > 2 else 0

    def _refresh_patients(self) -> None:
        previous, now, refreshed = {p.patient_id: p for p in self.patients}, datetime.now(UTC), []
        for index, (patient_id, region, age) in enumerate(PATIENTS):
            pressure = self._scenario_pressure(index)
            observation = VitalObservation(heart_rate=round(74 + pressure * 17 + self.rng.uniform(-6, 6), 1), spo2=round(98 - pressure * 3.4 + self.rng.uniform(-1, 1), 1), respiratory_rate=round(15 + pressure * 5 + self.rng.uniform(-2, 2), 1), temperature=round(36.8 + pressure * 0.7 + self.rng.uniform(-0.25, 0.25), 1), wheeze_probability=round(min(1, max(0, 0.08 + pressure * 0.34 + self.rng.uniform(-0.08, 0.08))), 2))
            assessment = self.engine.assess(observation)
            prior = previous.get(patient_id)
            trend = "INITIAL_ASSESSMENT" if not prior else ("DETERIORATING" if assessment.risk_level.value > prior.assessment.risk_level.value else "STABLE")
            alerts = (["HIGH_DEMO_SIGNAL"] if assessment.risk_level.value == "HIGH" else []) + (["RISK_ESCALATION"] if trend == "DETERIORATING" else [])
            refreshed.append(Patient(patient_id=patient_id, region=region, age=age, observation=observation, assessment=assessment, trend=trend, alerts=alerts, updated_at=now))
        self.patients = refreshed

    def dashboard(self) -> dict:
        high = [p for p in self.patients if p.assessment.risk_level.value == "HIGH"]
        regions: dict[str, int] = {}
        for patient in high: regions[patient.region] = regions.get(patient.region, 0) + 1
        anomaly = round(min(1, len(high) / len(self.patients) * 2.5), 2)
        pressure = {Scenario.NORMAL: 0, Scenario.RESPIRATORY_OUTBREAK: 16, Scenario.FLOOD: 20, Scenario.HOSPITAL_OVERLOAD: 31, Scenario.NETWORK_FAILURE: 12}[self.scenario]
        return {"disclaimer": "Every value in this command center is simulated prototype data unless explicitly labelled otherwise.", "simulation": {"scenario": self.scenario, "seed": self.seed, "step": self.step_number, "events": self.events[-8:]}, "patients": [p.model_dump(mode="json") for p in self.patients], "health": {"population": len(self.patients), "high_demo_signals": len(high), "anomaly_score": anomaly, "regional_high_signals": regions}, "city": {"hospital_capacity_percent": min(99, 53 + pressure + self.step_number * 2), "road_status": "BLOCKED" if self.scenario == Scenario.FLOOD and self.step_number >= 1 else "NORMAL", "communication_status": "DEGRADED" if self.scenario == Scenario.NETWORK_FAILURE else "ONLINE", "ambulances_available": max(1, 8 - len(high) // 2)}}
