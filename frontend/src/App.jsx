import { useState, useEffect, useRef } from 'react'
import './index.css'

const PATIENT_NAMES = {
  "PAT-001": "Aarav Mehta",   "PAT-002": "Priya Sharma",
  "PAT-003": "Rohan Gupta",   "PAT-004": "Neha Patel",
  "PAT-005": "Vikram Singh",  "PAT-006": "Ananya Das",
  "PAT-007": "Arjun Reddy",   "PAT-008": "Kavya Nair",
  "PAT-009": "Ishaan Joshi",  "PAT-010": "Riya Kapoor",
  "PAT-011": "Aditya Rao",    "PAT-012": "Simran Kaur",
}

// Fixed map positions for hospitals and patients so they don't jump around
const HOSPITAL_POSITIONS = [
  { top: '18%', left: '30%' },
  { top: '45%', left: '65%' },
  { top: '72%', left: '25%' },
  { top: '30%', left: '78%' },
  { top: '60%', left: '45%' },
]

const PATIENT_POSITIONS = [
  { top: '12%', left: '45%' }, { top: '22%', left: '55%' },
  { top: '35%', left: '20%' }, { top: '28%', left: '42%' },
  { top: '50%', left: '35%' }, { top: '40%', left: '80%' },
  { top: '55%', left: '55%' }, { top: '65%', left: '75%' },
  { top: '75%', left: '50%' }, { top: '80%', left: '35%' },
  { top: '42%', left: '15%' }, { top: '68%', left: '60%' },
]

function App() {
  const [state, setState] = useState({ patients: [], hospitals: [], network: 'WIFI' })
  const [selectedPatient, setSelectedPatient] = useState(null)
  const [patientDetails, setPatientDetails] = useState(null)
  const [loading, setLoading] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const wsRef = useRef(null)

  useEffect(() => {
    let ws
    let retryTimeout

    const connect = () => {
      ws = new WebSocket('ws://localhost:8000/ws')
      wsRef.current = ws

      ws.onopen = () => {
        setWsConnected(true)
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setState(data)
        } catch (e) {
          console.error('Parse error:', e)
        }
      }

      ws.onclose = () => {
        setWsConnected(false)
        console.log('WebSocket disconnected, retrying in 2s...')
        retryTimeout = setTimeout(connect, 2000)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      clearTimeout(retryTimeout)
      if (ws) ws.close()
    }
  }, [])

  const fetchPatientDetails = async (id) => {
    setSelectedPatient(id)
    setPatientDetails(null)
    setLoading(true)
    try {
      const res = await fetch(`http://localhost:8000/api/patients/${id}`)
      const data = await res.json()
      setPatientDetails(data)
    } catch (e) {
      console.error(e)
      setPatientDetails(null)
    }
    setLoading(false)
  }

  const highCount = state.patients?.filter(p => p.risk === 'HIGH').length || 0
  const modCount = state.patients?.filter(p => p.risk === 'MODERATE').length || 0
  const totalPatients = state.patients?.length || 0

  const getVitalClass = (type, value) => {
    if (!value) return 'normal'
    if (type === 'hr') return value > 120 ? 'critical' : value > 100 ? 'warning' : 'normal'
    if (type === 'spo2') return value < 90 ? 'critical' : value < 95 ? 'warning' : 'normal'
    if (type === 'temp') return value > 39 ? 'critical' : value > 38 ? 'warning' : 'normal'
    if (type === 'rr') return value > 30 ? 'critical' : value > 24 ? 'warning' : 'normal'
    return 'normal'
  }

  return (
    <div className="dashboard">
      {/* ── Header ────────────────────────── */}
      <header className="header">
        <div className="header-left">
          <div className="logo-dot" />
          <h1>Blackbox City</h1>
        </div>
        <div className="header-right">
          <div className="stat-pill">
            <div className={`dot ${wsConnected ? 'dot-green' : 'dot-red'}`} />
            {wsConnected ? 'LIVE' : 'OFFLINE'}
          </div>
          <div className="stat-pill">
            <span style={{color: 'var(--accent-red)'}}>{highCount}</span> Critical
          </div>
          <div className="stat-pill">
            <span style={{color: 'var(--accent-orange)'}}>{modCount}</span> Moderate
          </div>
          <div className="stat-pill">
            {totalPatients} Patients
          </div>
          <div className={`network-badge network-${state.network || 'WIFI'}`}>
            {state.network || 'WIFI'}
          </div>
        </div>
      </header>

      {/* ── Main Content ──────────────────── */}
      <div className="main-content">

        {/* Left: Hospitals */}
        <div className="panel">
          <div className="panel-title">Hospital Capacity</div>
          {state.hospitals?.length === 0 && <div className="empty-state">No hospital data</div>}
          {state.hospitals?.map(h => {
            const ratio = h.occupancy / (h.capacity || 1)
            const fillClass = ratio > 0.9 ? 'fill-high' : ratio > 0.7 ? 'fill-med' : 'fill-low'
            return (
              <div key={h.id} className="hospital-card">
                <div className="hospital-name">{h.name}</div>
                <div className="hospital-meta">
                  <span>{h.occupancy} / {h.capacity} beds</span>
                  <span className={`hospital-status status-${h.status}`}>{h.status}</span>
                </div>
                <div className="capacity-bar">
                  <div className={`capacity-fill ${fillClass}`} style={{ width: `${Math.min(ratio * 100, 100)}%` }} />
                </div>
              </div>
            )
          })}
        </div>

        {/* Center: Map */}
        <div className="map-panel">
          <div className="map-grid" />
          <div className="map-overlay-text">Digital Twin — Live Map</div>

          {/* Hospital markers */}
          {state.hospitals?.map((h, i) => (
            <div
              key={h.id}
              className="map-marker marker-hospital"
              style={HOSPITAL_POSITIONS[i] || { top: '50%', left: '50%' }}
              title={h.name}
            />
          ))}

          {/* Patient markers */}
          {state.patients?.map((p, i) => (
            <div
              key={p.id}
              className={`map-marker marker-patient risk-${p.risk || 'LOW'}`}
              style={PATIENT_POSITIONS[i] || { top: `${30 + (i * 7) % 50}%`, left: `${20 + (i * 11) % 60}%` }}
              title={`${PATIENT_NAMES[p.id] || p.id} — ${p.risk}`}
              onClick={() => fetchPatientDetails(p.id)}
            />
          ))}
        </div>

        {/* Right: Patients & Command */}
        <div className="panel">
          <div className="panel-title">Active Patients</div>

          <div className="patients-list">
            {state.patients?.map(p => (
              <div
                key={p.id}
                className={`patient-card ${selectedPatient === p.id ? 'selected' : ''}`}
                onClick={() => fetchPatientDetails(p.id)}
              >
                <div className={`patient-avatar avatar-${p.risk || 'LOW'}`}>
                  {(PATIENT_NAMES[p.id] || p.id).split(' ').map(n => n[0]).join('').slice(0, 2)}
                </div>
                <div className="patient-info">
                  <div className="patient-name">{PATIENT_NAMES[p.id] || p.id}</div>
                  <div className="patient-id">{p.id}</div>
                  <div className="patient-vitals-mini">
                    HR {p.hr?.toFixed(0)} · SpO₂ {p.spo2?.toFixed(0)}% · {p.temp?.toFixed(1)}°C
                  </div>
                </div>
                <span className={`risk-badge risk-${p.risk || 'LOW'}`}>{p.risk || '—'}</span>
              </div>
            ))}
            {(!state.patients || state.patients.length === 0) && (
              <div className="empty-state">No live vitals detected.<br/>Waiting for data stream...</div>
            )}
          </div>

          {/* Command Engine Detail */}
          <div className="panel-title" style={{marginTop: '8px'}}>Command Engine</div>

          {selectedPatient ? (
            <div className="detail-section">
              <div className="detail-header">
                <h3>{PATIENT_NAMES[selectedPatient] || selectedPatient}</h3>
                {patientDetails && (
                  <span className={`risk-badge risk-${patientDetails.risk_level || 'UNKNOWN'}`}>
                    {patientDetails.risk_level || 'UNKNOWN'}
                  </span>
                )}
              </div>

              {loading ? (
                <div className="loading-spinner">
                  <div className="spinner" />
                  Requesting AI explanation...
                </div>
              ) : patientDetails ? (
                <>
                  <div className="vitals-grid">
                    <div className="vital-item">
                      <div className="vital-label">Heart Rate</div>
                      <div className={`vital-value ${getVitalClass('hr', patientDetails.vitals?.hr)}`}>
                        {patientDetails.vitals?.hr?.toFixed(0) || '—'} <span style={{fontSize: '0.6rem', fontWeight: 400}}>bpm</span>
                      </div>
                    </div>
                    <div className="vital-item">
                      <div className="vital-label">SpO₂</div>
                      <div className={`vital-value ${getVitalClass('spo2', patientDetails.vitals?.spo2)}`}>
                        {patientDetails.vitals?.spo2?.toFixed(1) || '—'}<span style={{fontSize: '0.6rem', fontWeight: 400}}>%</span>
                      </div>
                    </div>
                    <div className="vital-item">
                      <div className="vital-label">Temperature</div>
                      <div className={`vital-value ${getVitalClass('temp', patientDetails.vitals?.temp)}`}>
                        {patientDetails.vitals?.temp?.toFixed(1) || '—'}<span style={{fontSize: '0.6rem', fontWeight: 400}}>°C</span>
                      </div>
                    </div>
                    <div className="vital-item">
                      <div className="vital-label">Resp Rate</div>
                      <div className={`vital-value ${getVitalClass('rr', patientDetails.vitals?.rr)}`}>
                        {patientDetails.vitals?.rr?.toFixed(0) || '—'}<span style={{fontSize: '0.6rem', fontWeight: 400}}>/min</span>
                      </div>
                    </div>
                  </div>

                  {patientDetails.explanation && (
                    <div className="explanation-box">
                      <strong>AI Analysis</strong>
                      {patientDetails.explanation.summary || JSON.stringify(patientDetails.explanation)}
                      {patientDetails.explanation.recommended_action && (
                        <div className="explanation-action">
                          ⚡ {patientDetails.explanation.recommended_action}
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <div className="empty-state">Error loading patient details.</div>
              )}
            </div>
          ) : (
            <div className="empty-state">Select a patient to view AI-powered explanations and recommended actions.</div>
          )}
        </div>
      </div>

      {/* ── Footer ────────────────────────── */}
      <footer className="footer">
        PROTOTYPE SYSTEM — NOT FOR CLINICAL DIAGNOSIS · The LLM explanation layer does not override ML risk scores · VITISH 2026
      </footer>
    </div>
  )
}

export default App
