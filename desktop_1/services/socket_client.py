import socketio
from socketio.exceptions import ConnectionError as SocketIOConnectionError
from services.api_client import load_token

sio = socketio.Client()

def connect():
    """Connect to the backend server.
    
    Returns:
        bool: True if connected successfully, False otherwise.
    """
    try:
        if not sio.connected:
            token, _ = load_token()
            if not token:
                print("Failed to connect to backend: missing auth token")
                return False

            sio.connect("http://127.0.0.1:5000", auth={"token": token})
            return True
        return True
    except (SocketIOConnectionError, Exception) as e:
        print(f"Failed to connect to backend: {e}")
        return False

def disconnect():
    """Disconnect from the backend server."""
    try:
        if sio.connected:
            sio.disconnect()
    except Exception as e:
        print(f"Error disconnecting: {e}")

def is_connected():
    """Check if connected to backend."""
    return sio.connected