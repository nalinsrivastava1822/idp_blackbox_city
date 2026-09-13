# BLACKBOX CITY - Command Center

An AI digital-twin command center for disaster-resilient public health response.

## Architecture

This monorepo consists of three layers:

1. **`backend/`**: FastAPI server, SQLAlchemy (SQLite), Digital Twin State Manager, ML/LLM engines, and MQTT listener.
2. **`frontend/`**: React + Vite live dashboard with WebSockets.
3. **`edge-sim/`**: Python script generating synthetic stethoscope vitals and simulating Wi-Fi/LoRa network fallback via MQTT.

## Setup Instructions

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```
*(The backend connects to the public `test.mosquitto.org` broker, so no local MQTT installation is required!)*

### 2. Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```

### 3. Edge Simulator (Data Generator)
In a third terminal:
```bash
cd edge-sim
pip install paho-mqtt
python simulator.py
```

Open the frontend URL (usually `http://localhost:5173`) to view the real-time command center dashboard.

### Fallback/LoRa Mode
To simulate a network degradation (which drops transmission speed and updates the UI indicator), edit `edge-sim/simulator.py` and set `LORA_FALLBACK_MODE = True`.
