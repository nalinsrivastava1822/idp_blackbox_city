from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, JSON, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./blackbox_city.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class PatientDT(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, index=True)
    heart_rate = Column(Float)
    spo2 = Column(Float)
    respiratory_rate = Column(Float)
    temperature = Column(Float)
    wheeze_probability = Column(Float)
    risk_level = Column(String, default="LOW")
    llm_explanation = Column(JSON, default={})
    last_updated = Column(DateTime, default=datetime.utcnow)

class HospitalDT(Base):
    __tablename__ = "hospitals"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    capacity = Column(Integer)
    current_occupancy = Column(Integer)
    status = Column(String, default="NORMAL") # NORMAL, OVERLOADED
    location = Column(String) # JSON or string coords

class PopulationDT(Base):
    __tablename__ = "population"
    id = Column(String, primary_key=True, index=True)
    region = Column(String)
    anomaly_score = Column(Float, default=0.0)
    dominant_symptoms = Column(String)

class RoadDT(Base):
    __tablename__ = "roads"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="CLEAR") # CLEAR, BLOCKED, FLOODED

class WeatherDT(Base):
    __tablename__ = "weather"
    id = Column(String, primary_key=True, index=True)
    temperature = Column(Float)
    pm25 = Column(Float)
    condition = Column(String)

class CommunicationDT(Base):
    __tablename__ = "communication"
    id = Column(String, primary_key=True, index=True)
    network_status = Column(String, default="WIFI") # WIFI, LORA_MESH, OFFLINE

def init_db():
    Base.metadata.create_all(bind=engine)
