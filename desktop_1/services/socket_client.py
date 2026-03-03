import socketio
from socketio.exceptions import ConnectionError as SocketIOConnectionError

sio = socketio.Client()

def connect():
    """Connect to the backend server.
    
    Returns:
        bool: True if connected successfully, False otherwise.
    """
    try:
        if not sio.connected:
            sio.connect("http://127.0.0.1:5000")
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