import sys
print("Direct import trace...")

try:
    print("1. Importing core events")
    from backend.core import runtime_events
    
    print("2. Importing logger")
    from backend.config.logger import logger
    
    print("3. Importing persona (THIS MIGHT HANG?)")
    from backend.core.persona import persona
    
    print("4. Importing config")
    from backend.config.assistant_config import assistant_config
    
    print("5. Importing auth")
    from backend.auth.auth_service import AuthService
    
    print("6. Importing db")
    from backend.database import SessionLocal, init_db
    
except Exception as e:
    print(f"Error: {e}")
