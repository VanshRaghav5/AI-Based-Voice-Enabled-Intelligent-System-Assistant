import sys

print("Testing database init...")
try:
    print("1")
    sys.stdout.flush()
    from sqlalchemy import create_engine
    
    print("2")
    sys.stdout.flush()
    from sqlalchemy.pool import StaticPool
    
    print("3")
    sys.stdout.flush()
    import os
    DB_DIR = os.path.join(os.path.expanduser("~"), ".omniassist")
    DB_PATH = os.path.join(DB_DIR, "assistant.db")
    print("DB_PATH:", DB_PATH)
    sys.stdout.flush()
    
    print("4")
    sys.stdout.flush()
    os.makedirs(DB_DIR, exist_ok=True)
    
    print("5")
    sys.stdout.flush()
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    
    print("6")
    sys.stdout.flush()
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    print("7")
    sys.stdout.flush()
    engine.connect()
    
    print("All success!")
except Exception as e:
    print(f"Error: {e}")
