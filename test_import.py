import sys
import os
from pathlib import Path
print("Starting trace 2...")

try:
    project_root = Path(__file__).parent
    print("Loading dotenv...")
    from backend.api_service import _load_dotenv, _get_or_generate_secret, _get_allowed_origins
    
    print("Creating Flask app...")
    from flask import Flask
    app = Flask(__name__)
    APP_SECRET_KEY = _get_or_generate_secret("OMNIASSIST_FLASK_SECRET_KEY")
    ALLOWED_ORIGINS = _get_allowed_origins()
    app.config['SECRET_KEY'] = APP_SECRET_KEY
    
    print("Setting up CORS...")
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})
    
    print("Setting up SocketIO...")
    from flask_socketio import SocketIO
    socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS)
    
    print("Setting up Limiter...")
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    print("Initializing Database...")
    from backend.api_service import initialize_database
    initialize_database()

    print("Checking wake word...")
    # we don't start the wake word thread here to avoid complications

    print("All initializations successful!")
except Exception as e:
    print(f"Error during init: {e}")
