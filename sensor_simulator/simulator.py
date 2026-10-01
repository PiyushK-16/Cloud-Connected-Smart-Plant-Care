"""Virtual IoT plant sensor. Moisture drifts down, rises while the cloud
switches the pump ON, temperature/humidity drift smoothly, light follows day/night.
Usage: python sensor_simulator/simulator.py --device PLANT-001 --type TOMATO --interval 2"""
import argparse, json, logging, math, os, random, time, datetime as dt
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sensor")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api", default=os.getenv("API_URL", "http://localhost:8000"))
    p.add_argument("--key", default=os.getenv("API_KEY", "dev-key"))
    p.add_argument("--device", default="PLANT-001")
    p.add_argument("--plant-name", default="Tomato Plant")
    p.add_argument("--type", default="TOMATO")
    p.add_argument("--interval", type=float, default=2.0, help="seconds between readings")
    p.add_argument("--start-moisture", type=float, default=55.0)
    p.add_argument("--drop", type=float, default=3.0, help="moisture lost per tick")
    p.add_argument("--offline", action="store_true", help="write to sample_data/offline.jsonl instead of sending")
    a = p.parse_args()
    H = {"X-API-Key": a.key}

    moisture, temp, hum, tank, pump = a.start_moisture, 27.0, 60.0, 100.0, False
    backlog = []  # readings buffered while the network/API is down

    if not a.offline:
        try:  # auto-register device (409 = already exists, fine)
            requests.post(f"{a.api}/api/devices", headers=H, timeout=5, json={
                "device_id": a.device, "plant_name": a.plant_name, "plant_type": a.type})
        except requests.RequestException as e:
            log.warning("Could not register device yet: %s", e)

    def send(reading):
        for attempt in range(3):  # retry with exponential backoff
            try:
                r = requests.post(f"{a.api}/api/sensors/data", json=reading, headers=H, timeout=5)
                if r.status_code in (200, 201):
                    return r.json()
                log.error("API error %s: %s", r.status_code, r.text[:120])
                if r.status_code < 500:
                    return None  # client error: retrying will not help
            except requests.RequestException as e:
                log.warning("Network error (try %d): %s", attempt + 1, e)
            time.sleep(2 ** attempt * 0.5)
        return None

    log.info("Simulator started for %s (interval %ss)", a.device, a.interval)
    while True:
        try:
            now = dt.datetime.now(dt.timezone.utc)
            hour = now.hour + now.minute / 60
            moisture += 6.0 if pump else -a.drop + random.uniform(-0.5, 0.5)   # watering vs drying
            moisture = max(0.0, min(100.0, moisture))
            temp += random.uniform(-0.3, 0.3) + (27 + 6 * math.sin((hour - 9) / 24 * 2 * math.pi) - temp) * 0.05
            hum += random.uniform(-0.8, 0.8) + (60 - (temp - 27) * 2 - hum) * 0.05
            hum = max(30.0, min(90.0, hum))
            light = max(0.0, math.sin((hour - 6) / 12 * math.pi)) * 100
            if pump: tank = max(0.0, tank - 0.8)
            reading = {"device_id": a.device, "soil_moisture": round(moisture, 1), "temperature": round(temp, 1),
                       "humidity": round(hum, 1), "light_level": round(light, 1),
                       "water_tank_level": round(tank, 1), "timestamp": now.isoformat()}
            if a.offline:
                os.makedirs("sample_data", exist_ok=True)
                with open("sample_data/offline.jsonl", "a") as f:
                    f.write(json.dumps(reading) + "\n")
                log.info("[offline] %s", reading)
            else:
                backlog.append(reading)
                while backlog:
                    resp = send(backlog[0])
                    if resp is None and len(backlog) and backlog[0] is reading and False:
                        break
                    if resp is None:
                        log.warning("Buffering %d reading(s); will retry", len(backlog))
                        backlog = backlog[-200:]
                        break
                    backlog.pop(0)
                    pump = resp["pump"] == "ON"
                    log.info("sent moisture=%.1f temp=%.1f pump=%s", reading["soil_moisture"], reading["temperature"], resp["pump"])
        except Exception:
            log.exception("Unexpected error; continuing")
        time.sleep(a.interval)

if __name__ == "__main__":
    main()
