"""
Backend Client for Desktop Application

This module provides a client interface to communicate with the backend API service
via REST endpoints and WebSocket connections for real-time updates.
"""

import requests
import socketio
from typing import Callable, Dict, Any, Optional
import logging
import threading
import time

logger = logging.getLogger(__name__)


class BackendClient:
    """
    Client for communicating with the backend API service.
    
    Provides methods for:
    - Sending commands (text or voice)
    - Starting/stopping voice listening
    - Confirming/rejecting actions
    - Real-time event handling via WebSocket
    
    Example:
        client = BackendClient()
        client.register_callback('on_command_result', my_handler)
        client.connect()
        client.process_command("open notepad")
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the backend client.
        
        Args:
            base_url: Base URL of the backend API (default: http://localhost:5000)
        """
        self.base_url = base_url
        self.sio = socketio.Client(reconnection=True, reconnection_attempts=5, reconnection_delay=2)
        self.callbacks = {}
        self.connected = False
        self.connection_thread: Optional[threading.Thread] = None
        
        # Setup WebSocket event handlers
        self._setup_socket_handlers()
    
    def _setup_socket_handlers(self):
        """Setup WebSocket event handlers for real-time updates"""
        
        @self.sio.on('connect')
        def on_connect():
            logger.info('✓ Connected to backend API')
            self.connected = True
            if 'on_connect' in self.callbacks:
                self.callbacks['on_connect']()
        
        @self.sio.on('connect_error')
        def on_connect_error(data):
            logger.error(f'✗ Connection error: {data}')
            self.connected = False
            if 'on_connect_error' in self.callbacks:
                self.callbacks['on_connect_error'](data)
        
        @self.sio.on('disconnect')
        def on_disconnect():
            logger.info('✗ Disconnected from backend')
            self.connected = False
            if 'on_disconnect' in self.callbacks:
                self.callbacks['on_disconnect']()
        
        @self.sio.on('connection_status')
        def on_connection_status(data):
            logger.info(f'Connection status: {data}')
            if 'on_connection_status' in self.callbacks:
                self.callbacks['on_connection_status'](data)
        
        @self.sio.on('voice_input')
        def on_voice_input(data):
            logger.info(f"🎤 Voice input: {data.get('text', '')}")
            if 'on_voice_input' in self.callbacks:
                self.callbacks['on_voice_input'](data)
        
        @self.sio.on('command_result')
        def on_command_result(data):
            logger.info(f"✓ Command result: {data.get('status', 'unknown')}")
            if 'on_command_result' in self.callbacks:
                self.callbacks['on_command_result'](data)
        
        @self.sio.on('confirmation_required')
        def on_confirmation_required(data):
            logger.info(f"⚠ Confirmation required: {data.get('message', '')}")
            if 'on_confirmation_required' in self.callbacks:
                self.callbacks['on_confirmation_required'](data)
        
        @self.sio.on('confirmation_result')
        def on_confirmation_result(data):
            logger.info(f"✓ Confirmation result: {data.get('status', 'unknown')}")
            if 'on_confirmation_result' in self.callbacks:
                self.callbacks['on_confirmation_result'](data)
        
        @self.sio.on('listening_status')
        def on_listening_status(data):
            logger.info(f"🎤 Listening status: {data.get('listening', False)}")
            if 'on_listening_status' in self.callbacks:
                self.callbacks['on_listening_status'](data)
        
        @self.sio.on('speech_complete')
        def on_speech_complete(data):
            logger.info(f"🔊 Speech complete: {data.get('text', '')}")
            if 'on_speech_complete' in self.callbacks:
                self.callbacks['on_speech_complete'](data)
        
        @self.sio.on('assistant_shutdown')
        def on_assistant_shutdown(data):
            logger.info(f"⚠ Assistant shutdown: {data.get('message', '')}")
            if 'on_assistant_shutdown' in self.callbacks:
                self.callbacks['on_assistant_shutdown'](data)
        
        @self.sio.on('error')
        def on_error(data):
            logger.error(f"✗ Backend error: {data.get('message', 'Unknown error')}")
            if 'on_error' in self.callbacks:
                self.callbacks['on_error'](data)
        
        @self.sio.on('pong')
        def on_pong(data):
            logger.debug('Pong received')
            if 'on_pong' in self.callbacks:
                self.callbacks['on_pong'](data)
    
    def connect(self, async_connect: bool = False) -> bool:
        """
        Connect to the backend WebSocket.
        
        Args:
            async_connect: If True, connect in a background thread (default: False)
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.connected:
            logger.warning('Already connected to backend')
            return True
        
        if async_connect:
            self.connection_thread = threading.Thread(target=self._connect_sync, daemon=True)
            self.connection_thread.start()
            return True
        else:
            return self._connect_sync()
    
    def _connect_sync(self) -> bool:
        """Internal synchronous connection method"""
        try:
            logger.info(f'Connecting to backend at {self.base_url}...')
            self.sio.connect(self.base_url)
            return True
        except Exception as e:
            logger.error(f'Connection failed: {e}')
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the backend WebSocket"""
        if self.connected:
            logger.info('Disconnecting from backend...')
            self.sio.disconnect()
            self.connected = False
    
    def register_callback(self, event: str, callback: Callable):
        """
        Register a callback function for specific events.
        
        Args:
            event: Event name (e.g., 'on_voice_input', 'on_command_result')
            callback: Function to call when event occurs
        
        Available events:
            - on_connect: Connection established
            - on_disconnect: Connection lost
            - on_connect_error: Connection failed
            - on_voice_input: Voice input detected
            - on_command_result: Command processed
            - on_confirmation_required: Action needs confirmation
            - on_confirmation_result: Confirmation processed
            - on_listening_status: Listening state changed
            - on_speech_complete: TTS finished speaking
            - on_assistant_shutdown: Assistant shutting down
            - on_error: Error occurred
        """
        self.callbacks[event] = callback
        logger.debug(f'Registered callback for event: {event}')
    
    def unregister_callback(self, event: str):
        """
        Unregister a callback for an event.
        
        Args:
            event: Event name to unregister
        """
        if event in self.callbacks:
            del self.callbacks[event]
            logger.debug(f'Unregistered callback for event: {event}')
    
    # ============== API METHODS (REST) ==============
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the backend service is healthy.
        
        Returns:
            Dictionary with health status
        """
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current backend status.
        
        Returns:
            Dictionary containing:
                - status: 'online' or 'error'
                - listening: True/False
                - pending_confirmation: True/False
                - confirmation_details: Details if pending
        """
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process a text command through the backend.
        
        Args:
            command: The command text to process
        
        Returns:
            Dictionary with command result:
                - status: 'success', 'error', or 'confirmation_required'
                - message: Response message
                - Additional fields depending on command type
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/process_command",
                json={'command': command},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to process command: {e}")
            return {'status': 'error', 'message': f'API Error: {str(e)}'}
    
    def start_listening(self) -> Dict[str, Any]:
        """
        Start voice listening mode in the backend.
        
        Returns:
            Dictionary with result
        """
        try:
            response = requests.post(f"{self.base_url}/api/start_listening", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to start listening: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def stop_listening(self) -> Dict[str, Any]:
        """
        Stop voice listening mode in the backend.
        
        Returns:
            Dictionary with result
        """
        try:
            response = requests.post(f"{self.base_url}/api/stop_listening", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to stop listening: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def confirm_action(self, approved: bool) -> Dict[str, Any]:
        """
        Confirm or reject a pending action.
        
        Args:
            approved: True to approve, False to reject
        
        Returns:
            Dictionary with confirmation result
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/confirm",
                json={'approved': approved},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to confirm action: {e}")
            return {'status': 'error', 'message': f'API Error: {str(e)}'}
    
    def speak(self, text: str) -> Dict[str, Any]:
        """
        Make the assistant speak text via TTS.
        
        Args:
            text: Text to speak
        
        Returns:
            Dictionary with result
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/speak",
                json={'text': text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to speak: {e}")
            return {'status': 'error', 'error': str(e)}
    
    # ============== WEBSOCKET METHODS ==============
    
    def send_command_socket(self, command: str):
        """
        Send a command via WebSocket (real-time).
        
        Args:
            command: The command to send
        """
        if not self.connected:
            logger.error('Not connected to backend. Cannot send command via WebSocket.')
            return
        
        try:
            self.sio.emit('send_command', {'command': command})
            logger.info(f'Sent command via WebSocket: {command}')
        except Exception as e:
            logger.error(f'Failed to send command via WebSocket: {e}')
    
    def ping(self):
        """Send a ping to the server"""
        if self.connected:
            self.sio.emit('ping')
    
    # ============== UTILITY METHODS ==============
    
    def is_connected(self) -> bool:
        """
        Check if connected to backend.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected
    
    def wait_for_connection(self, timeout: int = 10) -> bool:
        """
        Wait for connection to be established.
        
        Args:
            timeout: Maximum seconds to wait
        
        Returns:
            True if connected within timeout, False otherwise
        """
        start_time = time.time()
        while not self.connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        return self.connected


# ============== CONVENIENCE FUNCTIONS ==============

def create_client(base_url: str = "http://localhost:5000", auto_connect: bool = True) -> BackendClient:
    """
    Create and optionally connect a backend client.
    
    Args:
        base_url: Backend API URL
        auto_connect: Automatically connect (default: True)
    
    Returns:
        Configured BackendClient instance
    """
    client = BackendClient(base_url)
    if auto_connect:
        client.connect()
    return client


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create client
    client = BackendClient()
    
    # Register callbacks
    def on_voice(data):
        print(f"Voice: {data.get('text')}")
    
    def on_result(data):
        print(f"Result: {data.get('message')}")
    
    client.register_callback('on_voice_input', on_voice)
    client.register_callback('on_command_result', on_result)
    
    # Connect
    if client.connect():
        print("Connected!")
        
        # Test health check
        health = client.health_check()
        print(f"Health: {health}")
        
        # Test command
        result = client.process_command("what time is it")
        print(f"Command result: {result}")
        
        # Keep alive for WebSocket events
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nDisconnecting...")
            client.disconnect()
