# Project Report: Cloud-Connected Smart Plant Care & Watering System

**Author:** <your name> · **Course:** Cloud Computing · **Date:** <date>

## 1. Abstract
This project implements a cloud-connected plant monitoring and automated watering platform. Virtual IoT sensors (a Python simulator) send soil moisture, temperature, humidity, light and tank-level readings to a REST API. The backend stores history in a database, decides when to water using plant-specific thresholds and safety limits, raises alerts, detects offline devices and shows everything on a live dashboard. The cloud side is independent of the sensor source, so the simulator can later be replaced by an ESP32.

## 2. Introduction
IoT systems depend on cloud services for data collection, storage, automation and remote access. This project demonstrates that IoT-to-cloud pipeline without physical hardware, using synthetic data only.

## 3. Problem Statement
Manual plant watering wastes water, is easy to forget, and offers no remote visibility or history. Hardware-based solutions are costly for students, so a software-simulated, cloud-style implementation is needed.

## 4. Objectives
- Simulate realistic sensor data and send it to a cloud-style API.
- Store historical readings and watering events.
- Automate watering with safeguards against overwatering.
- Provide a live dashboard, alerts and device health monitoring.
- Apply basic security, testing and failure handling.

## 5. Existing System
Manual watering, or basic timer-based irrigation that ignores actual soil conditions and offers no monitoring or history.

## 6. Proposed System
A sensor-driven system: readings flow to the API, the watering engine reacts to real moisture values, and users monitor and control plants remotely through a dashboard.

## 7. Industry Relevance
The same pattern is used in smart agriculture, precision farming, greenhouses, nurseries, hydroponics, smart homes and commercial landscaping to cut water waste, enable remote monitoring and support data-driven care.

## 8. Cloud Computing Concepts
REST APIs, cloud database and time-series history, event-driven automation (each reading can trigger a decision), API-key authentication, secrets via environment variables, logging, monitoring and alerting, stateless services that scale horizontally, and a deployable web service. SaaS-style dashboard access from any browser; PaaS hosting is the intended deployment target.

## 9. IoT Concepts
Sensor telemetry, heartbeat/last-seen monitoring, actuator control (virtual pump), a device identity (`device_id`), and a command returned in the API response (`pump: ON/OFF`).

## 10. Technology Stack
Python, FastAPI, Pydantic, SQLite (swappable with Postgres), HTML/CSS/JavaScript, Chart.js, pytest, Git/GitHub.

## 11. Architecture
```
Sensor Simulator / ESP32 -> HTTPS REST API -> Backend -> Database
                                         \-> Watering Engine -> pump command in response
Dashboard (polls API every 3s) -> User
```

## 12. Sensor Simulation
The simulator runs in a loop with a configurable interval. Moisture decreases each tick and rises while the pump is ON; temperature and humidity drift gradually; light follows a day/night curve; tank level drops while pumping. It includes retry with exponential backoff, buffering when the API is unreachable, an offline mode that writes to a local file, and logs.

## 13. Database Design
Tables: users, devices, sensor_readings, watering_events, alerts. Devices belong to users; readings, events and alerts reference devices. An index on `(device_id, timestamp)` speeds history queries, and a unique constraint on the same pair rejects duplicate readings.

## 14. REST API
Endpoints: sensor ingestion, device create/list/get, latest reading, history, threshold and auto-water update, manual water, watering history, analytics, alerts list and acknowledge. All (except health) require an `X-API-Key` header. Errors use 401, 404, 409 and 422.

## 15. Watering Algorithm
Start the pump only if moisture < threshold, tank level is above the minimum, and the cooldown has passed. Stop when moisture reaches threshold + 15% or the maximum pump duration is reached. Each cycle is stored with moisture before/after and duration.

## 16. Plant Profiles
Succulent 20%, Herb 35%, Tomato 40%, Indoor 30%. Different plants need different soil moisture, so thresholds are profile-based and user-adjustable.

## 17. Dashboard
Cards for plant, moisture, temperature, humidity, light, pump, status and device state; line charts for moisture, temperature and humidity; watering history, alerts, analytics; manual water, auto-water toggle and threshold controls.

## 18. Alerts
Low soil moisture (WARNING), high temperature (CRITICAL), low water tank (WARNING), device offline (CRITICAL). Open alerts are not duplicated, resolve automatically when the condition clears, and can be acknowledged.

## 19. Device Monitoring
Each reading updates `last_seen`. If no data arrives within the configured interval (default 30 s) the device is shown OFFLINE and a critical alert is created. Heartbeat monitoring is essential because silent device failure would otherwise go unnoticed.

## 20. Cloud Deployment
The backend runs as a single web service (`uvicorn backend.app:app`). A free PaaS can host it with `API_KEY` set as a secret, and a free managed Postgres can replace SQLite by changing only `backend/db.py`. (Deployment status: <not yet deployed / deployed at URL>.)

## 21. Testing
11 automated pytest tests cover authentication, validation, storage, latest/history retrieval, duplicate handling, automatic watering and cooldown, low-tank blocking, manual watering, alerts and acknowledgement, offline detection, threshold updates and multiple devices. All pass. Manual end-to-end testing used the simulator and dashboard.

## 22. Security
API-key authentication with constant-time comparison, input validation, no hard-coded secrets (environment variables), `.env` excluded from Git. Production would add HTTPS, per-device credentials, user login with authorization, and rate limiting. Exposing an unauthenticated pump-control endpoint is dangerous because anyone could trigger watering or flood a plant.

## 23. Scalability
The API is stateless, so it can scale horizontally behind a load balancer. For many devices, the design would move to an IoT broker/API gateway, serverless functions or queues, a time-series or managed database, and data-retention policies. At current scale SQLite and polling are sufficient.

## 24. Analytics
Average/min/max moisture, average temperature and humidity, number of watering events, estimated water used (assumed pump flow), plant health status and device status.

## 25. Results
The full loop works in simulation: moisture falls, an alert appears, the pump starts automatically, moisture recovers, the pump stops and the event is saved; stopping the simulator produces an offline alert. <Add your own observed results and screenshots.>

## 26. Advantages
No hardware cost, fully reproducible, modular, safe watering logic, hardware-ready design.

## 27. Limitations
Simulated data only; SQLite and polling instead of a production database and MQTT/WebSockets; shared API key instead of per-user login; no real notification delivery (email/SMS).

## 28. Future Scope
Free-tier cloud deployment, MQTT ingestion, user accounts, email/push notifications, ESP32 hardware integration, weather-based watering, time-series database and analytics.

## 29. Conclusion
The project shows how an IoT workflow can be built end-to-end on cloud-computing principles: ingestion, storage, automation, monitoring, alerting, testing and secure configuration, with a clear path to real hardware and production-grade cloud services.
