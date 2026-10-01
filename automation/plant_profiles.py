"""Plant profiles: default moisture thresholds (%) per plant type."""
PROFILES = {"SUCCULENT": 20, "TOMATO": 40, "HERB": 35, "INDOOR": 30}

def threshold_for(plant_type: str) -> float:
    return float(PROFILES.get(plant_type.upper(), PROFILES["INDOOR"]))
