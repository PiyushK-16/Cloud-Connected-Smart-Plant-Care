# Step-by-Step Run Guide + Screenshots to Capture

Open 3 terminals in the project folder. Windows: activate venv with `venv\Scripts\activate`.
Save screenshots in `screenshots/` using the exact filenames below.

## Step 1: Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
No screenshot.

## Step 2: Run tests
```bash
pytest -v
```
Expect `11 passed`.
- Capture `01-tests-passing.png` (GitHub)

## Step 3: Start backend (Terminal 1)
```bash
uvicorn backend.app:app --port 8000
```
Open http://localhost:8000/docs
- Capture `02-api-docs.png` (GitHub): all endpoints visible

## Step 4: Start simulator (Terminal 2)
Open the dashboard at http://localhost:8000 first, then:
```bash
python sensor_simulator/simulator.py --device PLANT-001 --type TOMATO --interval 2
```
- Capture `03-simulator-and-dashboard.png` (GitHub): terminal + dashboard side by side, moisture ~55%, Healthy

## Step 5: Watch automatic watering (about 10 seconds later)
Moisture drops below 40%, low-moisture alert appears, pump ON, moisture rises, pump OFF, event saved.
- Capture `04-auto-watering-triggered.png` (LinkedIn + Instagram): pump ON, alert visible, chart dipping
- Capture `05-watering-history.png` (GitHub + LinkedIn): pump OFF, chart drop and recovery, history row with before/after
- Screen recording `demo.mp4` (LinkedIn + Instagram Reel): 20-30 s from moisture dropping to pump OFF

## Step 6: Manual controls
Click Manual Water, change threshold to 50 and Save, toggle Auto water.
- Capture `06-manual-and-threshold.png` (GitHub): controls + a MANUAL row in history

## Step 7: Second plant (Terminal 3)
```bash
python sensor_simulator/simulator.py --device PLANT-002 --plant-name "Cactus" --type SUCCULENT --start-moisture 40
```
Switch plants with the dropdown (cactus threshold is 20%).
- Capture `07-multi-device.png` (GitHub + LinkedIn)

## Step 8: Offline detection
Press Ctrl+C on the PLANT-001 simulator, wait ~35 s.
- Capture `08-offline-alert.png` (GitHub): OFFLINE status + CRITICAL alert

## Step 9: Push to GitHub
```bash
git init
git add .
git commit -m "Initialize smart plant cloud project"
git branch -M main
git remote add origin https://github.com/<your-username>/Cloud-Connected-Smart-Plant-Care.git
git push -u origin main
```
Create the empty repo on GitHub first (no README).
- Capture `09-github-repo.png` (LinkedIn): repo page after the push

## Where to post
| Platform | Post |
|---|---|
| GitHub | images 01, 02, 03, 05, 06, 07, 08 in screenshots/, best 4 (03, 05, 07, 08) embedded in README |
| LinkedIn | demo.mp4 (or image 04), 05, 07, 09 + caption from SOCIAL_CAPTIONS.md |
| Instagram | demo.mp4 as a Reel, or carousel of 04, 05, 07 |

## Before posting
- Do not show your real API key; `dev-key` is a local demo default only.
- Hide bookmarks, other tabs and personal info. Dark terminal + zoomed browser read better on phones.
