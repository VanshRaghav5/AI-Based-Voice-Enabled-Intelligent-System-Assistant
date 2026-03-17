import sys
import os
import time

def log(msg):
    with open("trace.log", "a") as f:
        f.write(msg + "\n")
    print(msg)
    sys.stdout.flush()

try:
    os.remove("trace.log")
except:
    pass

log("Direct import trace...")

try:
    log("1. Importing core events")
    from backend.core import runtime_events
    
    log("2. Importing logger")
    from backend.config.logger import logger
    
    log("3. Importing persona")
    from backend.core.persona import persona
    
    log("4. Importing config")
    from backend.config.assistant_config import assistant_config
    
    log("5. Importing auth")
    from backend.auth.auth_service import AuthService
    
    log("6. Importing db")
    from backend.database import SessionLocal, init_db

    log("7. Checking Flask")
    from flask import Flask

    log("All imports successful!")
except Exception as e:
    log(f"Error: {e}")
