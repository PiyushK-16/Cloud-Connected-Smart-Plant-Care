"""SQLite data layer (swap for Postgres/Supabase in the cloud version)."""
import os, sqlite3, datetime as dt
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, created_at TEXT);
CREATE TABLE IF NOT EXISTS devices(
  device_id TEXT PRIMARY KEY, user_id INTEGER DEFAULT 1 REFERENCES users(user_id),
  plant_name TEXT, plant_type TEXT, location TEXT, moisture_threshold REAL,
  auto_water INTEGER DEFAULT 1, last_seen TEXT, pump_on INTEGER DEFAULT 0,
  pump_started TEXT, last_watered TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS sensor_readings(
  reading_id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT REFERENCES devices(device_id),
  soil_moisture REAL, temperature REAL, humidity REAL, light_level REAL,
  water_tank_level REAL, timestamp TEXT, UNIQUE(device_id, timestamp));
CREATE INDEX IF NOT EXISTS idx_readings_dev_ts ON sensor_readings(device_id, timestamp);
CREATE TABLE IF NOT EXISTS watering_events(
  event_id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT REFERENCES devices(device_id),
  trigger_type TEXT, moisture_before REAL, moisture_after REAL, duration REAL, timestamp TEXT);
CREATE TABLE IF NOT EXISTS alerts(
  alert_id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT REFERENCES devices(device_id),
  alert_type TEXT, level TEXT, message TEXT, status TEXT DEFAULT 'open', created_at TEXT);
"""

def _conn():
    c = sqlite3.connect(os.getenv("DB_PATH", "plant.db"))
    c.row_factory = sqlite3.Row
    return c

@contextmanager
def session():
    c = _conn()
    try:
        yield c
        c.commit()
    finally:
        c.close()

def init():
    with session() as c:
        c.executescript(SCHEMA)
        c.execute("INSERT OR IGNORE INTO users(user_id,name,email,created_at) VALUES(1,'Demo User','demo@example.com',?)",
                  (dt.datetime.now(dt.timezone.utc).isoformat(),))
