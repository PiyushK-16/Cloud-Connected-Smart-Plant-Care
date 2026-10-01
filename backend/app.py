"""FastAPI backend: REST API + automation + alerts + offline detection."""
import os, secrets, datetime as dt
from typing import Optional
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from backend.db import session, init
from automation.plant_profiles import threshold_for
from automation import watering_engine as eng

API_KEY = os.getenv("API_KEY", "dev-key")          # set a real one in .env / host secrets
OFFLINE_AFTER_S = int(os.getenv("OFFLINE_AFTER_S", "30"))
HIGH_TEMP = float(os.getenv("HIGH_TEMP_C", "38"))
WATER_ML_PER_S = 25                                # assumed mini-pump flow

init()
app = FastAPI(title="Cloud Smart Plant Care API")

def now(): return dt.datetime.now(dt.timezone.utc)
def parse(s):
    if not s: return None
    t = dt.datetime.fromisoformat(s)
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)

def auth(x_api_key: str = Header(default="")):
    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(401, "Invalid or missing API key")

class Reading(BaseModel):
    device_id: str
    soil_moisture: float = Field(ge=0, le=100)
    temperature: float = Field(ge=-20, le=80)
    humidity: float = Field(ge=0, le=100)
    light_level: Optional[float] = Field(None, ge=0, le=100)
    water_tank_level: Optional[float] = Field(None, ge=0, le=100)
    timestamp: Optional[str] = None

class DeviceIn(BaseModel):
    device_id: str
    plant_name: str
    plant_type: str = "INDOOR"
    location: str = "Home"
    moisture_threshold: Optional[float] = Field(None, ge=0, le=100)

class SettingsIn(BaseModel):
    moisture_threshold: Optional[float] = Field(None, ge=0, le=100)
    auto_water: Optional[bool] = None

# ---------- helpers ----------
def get_device(c, did):
    d = c.execute("SELECT * FROM devices WHERE device_id=?", (did,)).fetchone()
    if not d: raise HTTPException(404, f"Device {did} not found")
    return d

def view(d):
    out = dict(d)
    ls = parse(d["last_seen"])
    out["status"] = "ONLINE" if ls and (now() - ls).total_seconds() <= OFFLINE_AFTER_S else "OFFLINE"
    out["pump"] = "ON" if d["pump_on"] else "OFF"
    out["auto_water"] = bool(d["auto_water"])
    return out

def raise_alert(c, did, typ, level, msg):
    if c.execute("SELECT 1 FROM alerts WHERE device_id=? AND alert_type=? AND status!='resolved'", (did, typ)).fetchone():
        return  # no duplicate open alerts
    c.execute("INSERT INTO alerts(device_id,alert_type,level,message,status,created_at) VALUES(?,?,?,?, 'open',?)",
              (did, typ, level, msg, now().isoformat()))

def resolve_alert(c, did, typ):
    c.execute("UPDATE alerts SET status='resolved' WHERE device_id=? AND alert_type=? AND status!='resolved'", (did, typ))

def check_offline(c):
    for d in c.execute("SELECT * FROM devices WHERE last_seen IS NOT NULL").fetchall():
        gap = (now() - parse(d["last_seen"])).total_seconds()
        if gap > OFFLINE_AFTER_S:
            raise_alert(c, d["device_id"], "DEVICE_OFFLINE", "CRITICAL",
                        f"No sensor data received from {d['device_id']} for {int(gap)}s.")

def start_pump(c, did, trigger, moisture):
    t = now().isoformat()
    c.execute("UPDATE devices SET pump_on=1, pump_started=? WHERE device_id=?", (t, did))
    c.execute("INSERT INTO watering_events(device_id,trigger_type,moisture_before,duration,timestamp) VALUES(?,?,?,0,?)",
              (did, trigger, moisture, t))

def stop_pump(c, d, moisture):
    t = now()
    dur = (t - parse(d["pump_started"])).total_seconds()
    c.execute("UPDATE devices SET pump_on=0, last_watered=? WHERE device_id=?", (t.isoformat(), d["device_id"]))
    c.execute("""UPDATE watering_events SET moisture_after=?, duration=? WHERE event_id=
                 (SELECT MAX(event_id) FROM watering_events WHERE device_id=?)""", (moisture, dur, d["device_id"]))

def run_automation(c, d, r):
    did, th, m = d["device_id"], d["moisture_threshold"], r.soil_moisture
    if m < th:
        raise_alert(c, did, "LOW_MOISTURE", "WARNING", f"{d['plant_name']} moisture dropped below {th:.0f}% (now {m:.0f}%).")
    else:
        resolve_alert(c, did, "LOW_MOISTURE")
    if r.temperature > HIGH_TEMP:
        raise_alert(c, did, "HIGH_TEMPERATURE", "CRITICAL", f"{d['plant_name']} temperature exceeded {HIGH_TEMP:.0f}C.")
    else:
        resolve_alert(c, did, "HIGH_TEMPERATURE")
    if r.water_tank_level is not None and r.water_tank_level <= eng.MIN_TANK:
        raise_alert(c, did, "LOW_WATER_TANK", "WARNING", f"Water tank for {d['plant_name']} is low.")
    else:
        resolve_alert(c, did, "LOW_WATER_TANK")
    resolve_alert(c, did, "DEVICE_OFFLINE")  # device is talking again
    if d["pump_on"]:
        if eng.should_stop(m, th, parse(d["pump_started"]), now()):
            stop_pump(c, d, m)
    elif d["auto_water"] and eng.should_start(m, th, r.water_tank_level, parse(d["last_watered"]), now()):
        start_pump(c, did, "AUTO", m)

# ---------- routes ----------
@app.get("/api/health")
def health(): return {"status": "ok"}

@app.post("/api/sensors/data", status_code=201)
def ingest(r: Reading, _=Depends(auth)):
    with session() as c:
        d = get_device(c, r.device_id)
        ts = r.timestamp or now().isoformat()
        try:
            c.execute("""INSERT INTO sensor_readings(device_id,soil_moisture,temperature,humidity,light_level,water_tank_level,timestamp)
                         VALUES(?,?,?,?,?,?,?)""", (r.device_id, r.soil_moisture, r.temperature, r.humidity,
                                                    r.light_level, r.water_tank_level, ts))
        except Exception:  # UNIQUE(device_id,timestamp) -> duplicate reading
            return {"status": "duplicate_ignored", "pump": "ON" if d["pump_on"] else "OFF"}
        c.execute("UPDATE devices SET last_seen=? WHERE device_id=?", (now().isoformat(), r.device_id))
        run_automation(c, get_device(c, r.device_id), r)
        d = get_device(c, r.device_id)
        return {"status": "stored", "pump": "ON" if d["pump_on"] else "OFF"}

@app.get("/api/devices")
def list_devices(_=Depends(auth)):
    with session() as c:
        check_offline(c)
        return [view(d) for d in c.execute("SELECT * FROM devices ORDER BY device_id")]

@app.post("/api/devices", status_code=201)
def add_device(b: DeviceIn, _=Depends(auth)):
    with session() as c:
        if c.execute("SELECT 1 FROM devices WHERE device_id=?", (b.device_id,)).fetchone():
            raise HTTPException(409, "Device already exists")
        th = b.moisture_threshold if b.moisture_threshold is not None else threshold_for(b.plant_type)
        c.execute("""INSERT INTO devices(device_id,plant_name,plant_type,location,moisture_threshold,created_at)
                     VALUES(?,?,?,?,?,?)""", (b.device_id, b.plant_name, b.plant_type.upper(), b.location, th, now().isoformat()))
        return view(get_device(c, b.device_id))

@app.get("/api/devices/{did}")
def one_device(did: str, _=Depends(auth)):
    with session() as c:
        return view(get_device(c, did))

@app.get("/api/devices/{did}/latest")
def latest(did: str, _=Depends(auth)):
    with session() as c:
        get_device(c, did)
        r = c.execute("SELECT * FROM sensor_readings WHERE device_id=? ORDER BY timestamp DESC LIMIT 1", (did,)).fetchone()
        if not r: raise HTTPException(404, "No readings yet")
        return dict(r)

@app.get("/api/devices/{did}/history")
def history(did: str, limit: int = 100, _=Depends(auth)):
    limit = max(1, min(limit, 1000))
    with session() as c:
        get_device(c, did)
        rows = c.execute("SELECT * FROM sensor_readings WHERE device_id=? ORDER BY timestamp DESC LIMIT ?", (did, limit)).fetchall()
        return [dict(r) for r in reversed(rows)]

@app.put("/api/devices/{did}/threshold")
def settings(did: str, b: SettingsIn, _=Depends(auth)):
    with session() as c:
        get_device(c, did)
        if b.moisture_threshold is not None:
            c.execute("UPDATE devices SET moisture_threshold=? WHERE device_id=?", (b.moisture_threshold, did))
        if b.auto_water is not None:
            c.execute("UPDATE devices SET auto_water=? WHERE device_id=?", (int(b.auto_water), did))
        return view(get_device(c, did))

@app.post("/api/devices/{did}/water")
def manual_water(did: str, _=Depends(auth)):
    with session() as c:
        d = get_device(c, did)
        if d["pump_on"]:
            raise HTTPException(409, "Pump already running")
        r = c.execute("SELECT soil_moisture FROM sensor_readings WHERE device_id=? ORDER BY timestamp DESC LIMIT 1", (did,)).fetchone()
        start_pump(c, did, "MANUAL", r["soil_moisture"] if r else None)
        return {"status": "pump_started", "max_duration_s": eng.MAX_PUMP_S}

@app.get("/api/devices/{did}/watering-history")
def watering_history(did: str, _=Depends(auth)):
    with session() as c:
        get_device(c, did)
        return [dict(r) for r in c.execute("SELECT * FROM watering_events WHERE device_id=? ORDER BY event_id DESC LIMIT 50", (did,))]

@app.get("/api/devices/{did}/analytics")
def analytics(did: str, _=Depends(auth)):
    with session() as c:
        d = get_device(c, did)
        s = c.execute("""SELECT COUNT(*) n, AVG(soil_moisture) avg_m, MIN(soil_moisture) min_m, MAX(soil_moisture) max_m,
                         AVG(temperature) avg_t, AVG(humidity) avg_h FROM sensor_readings WHERE device_id=?""", (did,)).fetchone()
        w = c.execute("SELECT COUNT(*) n, COALESCE(SUM(duration),0) secs FROM watering_events WHERE device_id=?", (did,)).fetchone()
        last = c.execute("SELECT soil_moisture FROM sensor_readings WHERE device_id=? ORDER BY timestamp DESC LIMIT 1", (did,)).fetchone()
        health = "Unknown" if not last else ("Healthy" if last[0] >= d["moisture_threshold"] else "Needs Water")
        rnd = lambda v: None if v is None else round(v, 1)
        return {"readings": s["n"], "avg_moisture": rnd(s["avg_m"]), "min_moisture": rnd(s["min_m"]),
                "max_moisture": rnd(s["max_m"]), "avg_temperature": rnd(s["avg_t"]), "avg_humidity": rnd(s["avg_h"]),
                "watering_events": w["n"], "estimated_water_ml": round(w["secs"] * WATER_ML_PER_S),
                "plant_health": health, "device_status": view(d)["status"]}

@app.get("/api/alerts")
def alerts(status: Optional[str] = None, _=Depends(auth)):
    with session() as c:
        check_offline(c)
        q, p = "SELECT * FROM alerts", ()
        if status: q, p = q + " WHERE status=?", (status,)
        return [dict(r) for r in c.execute(q + " ORDER BY alert_id DESC LIMIT 50", p)]

@app.put("/api/alerts/{aid}/acknowledge")
def ack(aid: int, _=Depends(auth)):
    with session() as c:
        if not c.execute("SELECT 1 FROM alerts WHERE alert_id=?", (aid,)).fetchone():
            raise HTTPException(404, "Alert not found")
        c.execute("UPDATE alerts SET status='acknowledged' WHERE alert_id=? AND status='open'", (aid,))
        return dict(c.execute("SELECT * FROM alerts WHERE alert_id=?", (aid,)).fetchone())

# Dashboard (mounted last so /api routes win)
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend"), html=True), name="ui")
