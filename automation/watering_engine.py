"""Pure watering decision logic (no DB access, easy to unit-test).
Safety: threshold + tank check + cooldown (no rapid re-watering)
+ max pump duration + stop at target (no overwatering)."""
import os

COOLDOWN_S = int(os.getenv("COOLDOWN_S", "60"))
MAX_PUMP_S = int(os.getenv("MAX_PUMP_S", "30"))
TARGET_MARGIN = 15.0   # stop when moisture >= threshold + margin
MIN_TANK = 10.0        # % minimum water in tank

def should_start(moisture, threshold, tank, last_watered, now):
    if moisture >= threshold:
        return False
    if tank is not None and tank <= MIN_TANK:
        return False
    if last_watered and (now - last_watered).total_seconds() < COOLDOWN_S:
        return False
    return True

def should_stop(moisture, threshold, started, now):
    if moisture >= threshold + TARGET_MARGIN:
        return True
    return bool(started) and (now - started).total_seconds() >= MAX_PUMP_S
