const $ = (id) => document.getElementById(id);
const title = (value) => value.replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
async function request(url, options) { const response = await fetch(url, options); if (!response.ok) throw new Error(await response.text()); return response.json(); }
function riskClass(level) { return level.toLowerCase(); }
function render(data) {
  const {simulation, health, city, patients} = data;
  $('scenario-title').textContent = title(simulation.scenario);
  $('scenario-detail').textContent = `Timestep ${simulation.step} · Seed ${simulation.seed} · deterministic simulation`;
  $('anomaly').textContent = health.anomaly_score.toFixed(2);
  $('population-label').textContent = `${health.population} simulated patients`;
  $('metrics').innerHTML = [ ['Population',health.population], ['High demo signals',health.high_demo_signals], ['Hospital capacity',`${city.hospital_capacity_percent}%`], ['Ambulances',city.ambulances_available] ].map(([label,value])=>`<article class="metric"><span>${label}</span><b>${value}</b></article>`).join('');
  $('patients').innerHTML = patients.map(p=>`<div class="patient"><div><b>${p.patient_id}</b><br><small>${p.region} · HR ${p.observation.heart_rate} · SpO₂ ${p.observation.spo2}%</small></div><span class="badge ${riskClass(p.assessment.risk_level)}">${p.assessment.risk_level}</span></div>`).join('');
  const regions = Object.entries(health.regional_high_signals);
  $('regions').innerHTML = regions.length ? regions.map(([region,value])=>`<div><div class="bar-label"><span>${region}</span><span>${value}</span></div><div class="bar"><i style="width:${Math.min(100,value*35)}%"></i></div></div>`).join('') : '<p>No elevated simulated regional signals.</p>';
  $('city').innerHTML = [['Hospital capacity',`${city.hospital_capacity_percent}%`],['Road status',city.road_status],['Communication',city.communication_status],['Ambulances available',city.ambulances_available]].map(([k,v])=>`<div class="city-row"><b>${k}</b><span>${v}</span></div>`).join('');
  $('events').innerHTML = simulation.events.map(event=>`<li>${event}</li>`).join('');
  $('system-status').textContent = city.communication_status === 'ONLINE' ? '● SYSTEM ONLINE' : '● NETWORK DEGRADED';
}
async function load(){ try { render(await request('/api/dashboard')); } catch(e) { $('system-status').textContent='● API UNAVAILABLE'; console.error(e); } }
$('start').onclick=async()=>render(await request('/api/simulation/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:$('scenario').value,seed:Number($('seed').value)})}));
$('step').onclick=async()=>render(await request('/api/simulation/step',{method:'POST'}));
$('reset').onclick=async()=>render(await request('/api/simulation/reset',{method:'POST'}));
load();
