"""
Desktop Integration Example

This file demonstrates how to integrate the backend API client
with a desktop application UI (using basic console example).

For GUI integration, replace console I/O with your framework's
components (Electron IPC, Qt Signals, Tkinter events, etc.)
"""

import sys
import os
import time
import logging
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desktop.services.backend_client import BackendClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DesktopAssistantExample:
    """
    Example desktop application integrating with backend API.
    
    This is a console-based example. For GUI applications:
    - Replace print() with UI label/text updates
    - Replace input() with button clicks or text fields
    - Use callbacks to update UI components
    """
    
    def __init__(self, backend_url: str = "http://localhost:5000"):
        """
        Initialize desktop assistant.
        
        Args:
            backend_url: URL of the backend API service
        """
        self.backend = BackendClient(backend_url)
        self.is_running = False
        self.pending_confirmation = None
        
        # Register event callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self):
        """Setup callbacks for backend events"""
        
        # Connection events
        self.backend.register_callback('on_connect', self._on_connected)
        self.backend.register_callback('on_disconnect', self._on_disconnected)
        self.backend.register_callback('on_connect_error', self._on_connection_error)
        
        # Voice and command events
        self.backend.register_callback('on_voice_input', self._on_voice_input)
        self.backend.register_callback('on_command_result', self._on_command_result)
        
        # Confirmation events
        self.backend.register_callback('on_confirmation_required', self._on_confirmation_required)
        self.backend.register_callback('on_confirmation_result', self._on_confirmation_result)
        
        # Status events
        self.backend.register_callback('on_listening_status', self._on_listening_status)
        self.backend.register_callback('on_speech_complete', self._on_speech_complete)
        
        # Error events
        self.backend.register_callback('on_error', self._on_error)
    
    # ============== Event Handlers ==============
    
    def _on_connected(self):
        """Handle connection established"""
        print("\n✓ Connected to backend API")
        print("=" * 60)
    
    def _on_disconnected(self):
        """Handle disconnection"""
        print("\n✗ Disconnected from backend")
        print("=" * 60)
    
    def _on_connection_error(self, data):
        """Handle connection error"""
        print(f"\n✗ Connection error: {data}")
        print("=" * 60)
    
    def _on_voice_input(self, data: Dict[str, Any]):
        """
        Handle voice input detected.
        
        In GUI: Update transcription label/text area
        """
        text = data.get('text', '')
        print(f"\n🎤 You said: {text}")
    
    def _on_command_result(self, data: Dict[str, Any]):
        """
        Handle command processing result.
        
        In GUI: Update result display, show success/error indicators
        """
        status = data.get('status', 'unknown')
        message = data.get('message', 'No message')
        
        print(f"\n🤖 Assistant: {message}")
        print(f"   Status: {status}")
        
        # Show additional data if available
        if 'data' in data:
            print(f"   Data: {data['data']}")
    
    def _on_confirmation_required(self, data: Dict[str, Any]):
        """
        Handle confirmation request.
        
        In GUI: Show modal dialog with Yes/No buttons
        """
        message = data.get('message', 'Confirm this action?')
        self.pending_confirmation = data
        
        print("\n" + "=" * 60)
        print("⚠️  CONFIRMATION REQUIRED")
        print("=" * 60)
        print(f"Action: {message}")
        print("\nType 'yes' to approve or 'no' to reject:")
        print("=" * 60)
    
    def _on_confirmation_result(self, data: Dict[str, Any]):
        """
        Handle confirmation result.
        
        In GUI: Update UI to show action completed/cancelled
        """
        status = data.get('status', 'unknown')
        message = data.get('message', 'Action processed')
        
        print(f"\n✓ Confirmation processed: {message}")
        print(f"   Status: {status}")
        self.pending_confirmation = None
    
    def _on_listening_status(self, data: Dict[str, Any]):
        """
        Handle listening status change.
        
        In GUI: Update microphone icon/animation
        """
        listening = data.get('listening', False)
        if listening:
            print("\n🎤 Listening... (speak now)")
        else:
            print("\n🔇 Stopped listening")
    
    def _on_speech_complete(self, data: Dict[str, Any]):
        """
        Handle TTS completion.
        
        In GUI: Hide speaking indicator/animation
        """
        text = data.get('text', '')
        logger.debug(f"Speech complete: {text}")
    
    def _on_error(self, data: Dict[str, Any]):
        """
        Handle errors from backend.
        
        In GUI: Show error notification/dialog
        """
        message = data.get('message', 'Unknown error')
        source = data.get('source', 'unknown')
        
        print(f"\n✗ Error ({source}): {message}")
    
    # ============== User Actions ==============
    
    def start(self):
        """Start the desktop application"""
        print("\n" + "=" * 60)
        print("  AI Voice Assistant - Desktop Integration Example")
        print("=" * 60)
        
        # Check backend health
        print("\n⏳ Checking backend health...")
        health = self.backend.health_check()
        
        if health.get('status') != 'healthy':
            print(f"✗ Backend is not healthy: {health}")
            print("\nMake sure the backend API is running:")
            print("  python backend/api_service.py")
            return False
        
        print(f"✓ Backend is healthy: {health.get('service', 'Unknown')}")
        
        # Connect to WebSocket
        print("\n⏳ Connecting to backend...")
        if not self.backend.connect():
            print("✗ Failed to connect to backend")
            return False
        
        # Wait for connection
        if not self.backend.wait_for_connection(timeout=5):
            print("✗ Connection timeout")
            return False
        
        self.is_running = True
        self.show_menu()
        return True
    
    def stop(self):
        """Stop the application"""
        print("\n⏳ Shutting down...")
        
        # Stop listening if active
        status = self.backend.get_status()
        if status.get('listening'):
            self.backend.stop_listening()
        
        # Disconnect
        self.backend.disconnect()
        self.is_running = False
        
        print("✓ Goodbye!")
    
    def show_menu(self):
        """Display interactive menu"""
        while self.is_running:
            print("\n" + "-" * 60)
            print("Commands:")
            print("  1. Start voice listening")
            print("  2. Stop voice listening")
            print("  3. Send text command")
            print("  4. Check status")
            print("  5. Make assistant speak")
            print("  0. Exit")
            print("-" * 60)
            
            # Handle pending confirmation
            if self.pending_confirmation:
                self._handle_confirmation_input()
                continue
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == '1':
                self.start_listening()
            elif choice == '2':
                self.stop_listening()
            elif choice == '3':
                self.send_command()
            elif choice == '4':
                self.check_status()
            elif choice == '5':
                self.speak()
            elif choice == '0':
                self.stop()
                break
            else:
                print("Invalid choice. Try again.")
    
    def _handle_confirmation_input(self):
        """Handle confirmation input from user"""
        response = input().strip().lower()
        
        if response in ['yes', 'y', 'confirm', 'approve']:
            print("\n✓ Approving action...")
            result = self.backend.confirm_action(True)
        elif response in ['no', 'n', 'cancel', 'reject']:
            print("\n✗ Rejecting action...")
            result = self.backend.confirm_action(False)
        else:
            print("Invalid response. Type 'yes' or 'no'.")
    
    def start_listening(self):
        """Start voice listening mode"""
        print("\n⏳ Starting voice listening...")
        result = self.backend.start_listening()
        
        if 'error' in result:
            print(f"✗ Error: {result['error']}")
        else:
            print(f"✓ {result.get('message', 'Listening started')}")
    
    def stop_listening(self):
        """Stop voice listening mode"""
        print("\n⏳ Stopping voice listening...")
        result = self.backend.stop_listening()
        
        if 'error' in result:
            print(f"✗ Error: {result['error']}")
        else:
            print(f"✓ {result.get('message', 'Listening stopped')}")
    
    def send_command(self):
        """Send a text command"""
        command = input("\nEnter command: ").strip()
        
        if not command:
            print("No command entered.")
            return
        
        print(f"\n⏳ Processing: {command}")
        result = self.backend.process_command(command)
        
        # Result will be handled by callback
    
    def check_status(self):
        """Check backend status"""
        print("\n⏳ Checking status...")
        status = self.backend.get_status()
        
        print("\nBackend Status:")
        print(f"  Status: {status.get('status', 'unknown')}")
        print(f"  Listening: {status.get('listening', False)}")
        print(f"  Pending Confirmation: {status.get('pending_confirmation', False)}")
        
        if status.get('confirmation_details'):
            print(f"  Confirmation: {status['confirmation_details'].get('message', '')}")
    
    def speak(self):
        """Make assistant speak text"""
        text = input("\nEnter text to speak: ").strip()
        
        if not text:
            print("No text entered.")
            return
        
        print(f"\n🔊 Speaking: {text}")
        result = self.backend.speak(text)
        
        if 'error' in result:
            print(f"✗ Error: {result['error']}")
        else:
            print(f"✓ {result.get('message', 'Speech completed')}")


# ============== MAIN ENTRY POINT ==============

def main():
    """Main entry point for example application"""
    
    # You can change this to match your backend URL
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:5000')
    
    # Create and start the application
    app = DesktopAssistantExample(backend_url)
    
    try:
        if app.start():
            # Application runs in the menu loop
            pass
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        app.stop()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        app.stop()


if __name__ == '__main__':
    main()
