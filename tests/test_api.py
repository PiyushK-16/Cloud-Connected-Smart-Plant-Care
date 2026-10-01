import datetime as dt
from fastapi.testclient import TestClient
from backend.app import app
from backend.db import session

c = TestClient(app)
H = {"X-API-Key": "k"}

def dev(i, t="TOMATO"):
    return c.post("/api/devices", headers=H, json={"device_id": i, "plant_name": "P", "plant_type": t})

def read(i, m, temp=25, tank=80, ts=None):
    b = {"device_id": i, "soil_moisture": m, "temperature": temp, "humidity": 60, "light_level": 50, "water_tank_level": tank}
    if ts: b["timestamp"] = ts
    return c.post("/api/sensors/data", headers=H, json=b)

def test_unauthorized():
    assert c.get("/api/devices").status_code == 401

def test_profile_threshold_and_update():
    assert dev("T1", "SUCCULENT").json()["moisture_threshold"] == 20
    r = c.put("/api/devices/T1/threshold", headers=H, json={"moisture_threshold": 25})
    assert r.json()["moisture_threshold"] == 25

def test_invalid_reading_rejected():
    dev("T2")
    assert read("T2", 150).status_code == 422

def test_store_latest_history():
    dev("T3")
    assert read("T3", 60).status_code == 201
    assert c.get("/api/devices/T3/latest", headers=H).json()["soil_moisture"] == 60
    assert len(c.get("/api/devices/T3/history", headers=H).json()) == 1

def test_duplicate_ignored():
    dev("T4")
    ts = "2026-01-01T00:00:00+00:00"
    read("T4", 60, ts=ts)
    assert read("T4", 60, ts=ts).json()["status"] == "duplicate_ignored"

def test_auto_water_cycle_and_cooldown():
    dev("T5")  # tomato threshold 40
    assert read("T5", 60).json()["pump"] == "OFF"
    assert read("T5", 35).json()["pump"] == "ON"        # below threshold -> pump ON
    assert read("T5", 60).json()["pump"] == "OFF"       # >= 55 -> pump OFF
    ev = c.get("/api/devices/T5/watering-history", headers=H).json()
    assert ev[0]["moisture_before"] == 35 and ev[0]["moisture_after"] == 60
    assert read("T5", 30).json()["pump"] == "OFF"       # cooldown blocks rewatering

def test_low_tank_blocks_watering():
    dev("T6")
    assert read("T6", 10, tank=5).json()["pump"] == "OFF"

def test_manual_water_and_conflict():
    dev("T7"); read("T7", 60)
    assert c.post("/api/devices/T7/water", headers=H).status_code == 200
    assert c.post("/api/devices/T7/water", headers=H).status_code == 409

def test_alert_generated_and_acknowledged():
    dev("T8"); read("T8", 10, tank=5)
    a = [x for x in c.get("/api/alerts", headers=H).json() if x["device_id"] == "T8"]
    assert {"LOW_MOISTURE", "LOW_WATER_TANK"} <= {x["alert_type"] for x in a}
    r = c.put(f"/api/alerts/{a[0]['alert_id']}/acknowledge", headers=H)
    assert r.json()["status"] == "acknowledged"

def test_offline_detection():
    dev("T9"); read("T9", 60)
    old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=5)).isoformat()
    with session() as s:
        s.execute("UPDATE devices SET last_seen=? WHERE device_id='T9'", (old,))
    d = [x for x in c.get("/api/devices", headers=H).json() if x["device_id"] == "T9"][0]
    assert d["status"] == "OFFLINE"
    assert any(x["alert_type"] == "DEVICE_OFFLINE" and x["device_id"] == "T9" for x in c.get("/api/alerts", headers=H).json())

def test_multiple_devices():
    dev("M1"); dev("M2")
    ids = {d["device_id"] for d in c.get("/api/devices", headers=H).json()}
    assert {"M1", "M2"} <= ids
