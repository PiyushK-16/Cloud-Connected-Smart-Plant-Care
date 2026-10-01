# LinkedIn Caption (replace <repo-link>)

I built a Cloud-Connected Smart Plant Care & Watering System as part of my Cloud Computing course. 🌱☁️

I don't own IoT hardware, so I simulated the sensors in Python and built the whole cloud side around them:

🔹 Virtual IoT sensors send soil moisture, temperature, humidity, light and tank level to a REST API (FastAPI)
🔹 Readings are stored as historical time-series data in a database
🔹 An automation engine decides when to water, using plant-specific thresholds, cooldown, tank checks and a max pump duration to prevent overwatering
🔹 A live dashboard shows charts, alerts, pump status and watering history, with manual and auto watering controls
🔹 Alerts for low moisture, high temperature, low tank, and offline devices (heartbeat monitoring)
🔹 API-key authentication, input validation, duplicate detection, retry with backoff, and 11 automated tests

The architecture is designed so the simulator can be swapped for a real ESP32 without changing the cloud side. All data is synthetic demo data.

What I learned: IoT-to-cloud data flow, REST API design, event-driven automation, failure handling, and why monitoring and security matter for connected devices.

Code and docs: <repo-link>

Next: cloud deployment on a free tier and MQTT support.

#CloudComputing #IoT #Python #FastAPI #SmartAgriculture #RESTAPI #StudentProject #GitHub #LearningInPublic

---

# Instagram Caption

Watching a virtual plant water itself ☁️🌱

Soil gets dry → the cloud spots it → pump turns ON → moisture recovers → pump OFF. No hardware, just Python, FastAPI and a live dashboard.

Built for my Cloud Computing course:
💧 Simulated IoT sensors
📊 Live charts + alerts
⚙️ Smart watering logic with safety limits
📴 Offline device detection

Full code on GitHub, link in bio.

#cloudcomputing #iot #python #smartfarming #coding #studentdeveloper #techstudent #fastapi #buildinpublic #learntocode

---

# Short Instagram text for carousel slides
1. "Plant gets dry" (image 04)
2. "Cloud triggers the pump" (image 04 / 05)
3. "Moisture recovers, event saved" (image 05)
4. "Two plants, two rules" (image 07)
