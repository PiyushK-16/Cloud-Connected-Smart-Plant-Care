import os, tempfile
os.environ.update(DB_PATH=os.path.join(tempfile.mkdtemp(), "test.db"), API_KEY="k",
                  COOLDOWN_S="3600", MAX_PUMP_S="30", OFFLINE_AFTER_S="30")
