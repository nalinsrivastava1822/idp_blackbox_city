import time
import json
import random
import paho.mqtt.client as mqtt

MQTT_BROKER = "test.mosquitto.org"
MQTT_TOPIC = "blackbox_city_vitish2026/vitals"

LORA_FALLBACK_MODE = False

def generate_vital():
    severity = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
    
    # 0 = normal, 1 = moderate, 2 = severe anomaly
    hr = random.uniform(60, 100) if severity == 0 else random.uniform(100, 150)
    spo2 = random.uniform(95, 100) if severity == 0 else random.uniform(85, 94)
    rr = random.uniform(12, 20) if severity == 0 else random.uniform(20, 35)
    temp = random.uniform(36.5, 37.5) if severity == 0 else random.uniform(37.5, 40.0)
    pm25 = random.uniform(10, 50) if severity == 0 else random.uniform(100, 300)
    
    return {
        "patient_id": f"PAT-{random.randint(100, 999)}",
        "heart_rate": hr,
        "spo2": spo2,
        "respiratory_rate": rr,
        "temperature": temp,
        "pm25_exposure": pm25,
        "network_path": "LORA_MESH" if LORA_FALLBACK_MODE else "WIFI",
        "timestamp": time.time()
    }

def main():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, 1883, 60)
    
    print("Starting Edge Simulator...")
    print(f"Publishing to {MQTT_BROKER} on topic {MQTT_TOPIC}")
    
    while True:
        data = generate_vital()
        client.publish(MQTT_TOPIC, json.dumps(data))
        print(f"Published: {data['patient_id']} (Path: {data['network_path']})")
        
        # LoRa mesh is much slower
        delay = 5.0 if LORA_FALLBACK_MODE else 1.0
        time.sleep(delay)

if __name__ == "__main__":
    main()
