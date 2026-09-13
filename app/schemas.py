from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Scenario(StrEnum):
    NORMAL = "NORMAL"
    RESPIRATORY_OUTBREAK = "RESPIRATORY_OUTBREAK"
    FLOOD = "FLOOD"
    HOSPITAL_OVERLOAD = "HOSPITAL_OVERLOAD"
    NETWORK_FAILURE = "NETWORK_FAILURE"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class SimulationStart(BaseModel):
    scenario: Scenario = Scenario.NORMAL
    seed: int = Field(default=42, ge=0, le=2_147_483_647)


class VitalObservation(BaseModel):
    heart_rate: float = Field(ge=20, le=260)
    spo2: float = Field(ge=50, le=100)
    respiratory_rate: float = Field(ge=4, le=80)
    temperature: float = Field(ge=30, le=45)
    wheeze_probability: float = Field(ge=0, le=1)


class RiskAssessment(BaseModel):
    risk_level: RiskLevel
    model_confidence: float = Field(ge=0, le=1)
    class_probabilities: dict[RiskLevel, float]
    model_status: str
    safety_note: str = "Synthetic prototype output only — not a clinical diagnosis or treatment recommendation."


class Patient(BaseModel):
    patient_id: str
    region: str
    age: int
    observation: VitalObservation
    assessment: RiskAssessment
    trend: str
    alerts: list[str]
    updated_at: datetime
