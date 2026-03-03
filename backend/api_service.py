"""
Backend API Service for Voice Assistant

This service exposes REST API endpoints and WebSocket connections
to allow the desktop application to interact with the backend functionality.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path to support running from any directory
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from backend.core.assistant_controller import AssistantController
from backend.voice_engine.audio_pipeline import listen, speak
from backend.config.logger import logger
import threading
from typing import Optional, Dict, Any

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
controller = AssistantController()
is_listening = False
pending_confirmation: Optional[Dict[str, Any]] = None
listening_thread: Optional[threading.Thread] = None


# ============== REST API ENDPOINTS ==============

@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Get current assistant status
    
    Returns:
        JSON with status, listening state, and confirmation state
    """
    return jsonify({
        'status': 'online',
        'listening': is_listening,
        'pending_confirmation': pending_confirmation is not None,
        'confirmation_details': pending_confirmation if pending_confirmation else None
    })


@app.route('/api/process_command', methods=['POST'])
def process_command():
    """
    Process a text command
    
    Request Body:
        {
            "command": "string"
        }
    
    Returns:
        JSON with command processing result
    """
    data = request.json
    command = data.get('command', '')
    
    if not command:
        return jsonify({'error': 'No command provided'}), 400
    
    try:
        logger.info(f"[API] Processing command: {command}")
        result = controller.process(command)
        
        # Check if confirmation is required
        if result.get('status') == 'confirmation_required':
            global pending_confirmation
            pending_confirmation = result
            # Notify WebSocket clients
            socketio.emit('confirmation_required', result)
        
        # Send result to all connected clients
        socketio.emit('command_result', result)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"[API] Error processing command: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error processing command: {str(e)}'
        }), 500


@app.route('/api/start_listening', methods=['POST'])
def start_listening():
    """
    Start voice listening mode
    
    Returns:
        JSON confirmation of listening state
    """
    global is_listening, listening_thread
    
    if is_listening:
        return jsonify({'message': 'Already listening', 'listening': True}), 200
    
    is_listening = True
    listening_thread = threading.Thread(target=voice_loop, daemon=True)
    listening_thread.start()
    
    logger.info("[API] Voice listening started")
    socketio.emit('listening_status', {'listening': True})
    
    return jsonify({'message': 'Listening started', 'listening': True})


@app.route('/api/stop_listening', methods=['POST'])
def stop_listening():
    """
    Stop voice listening mode
    
    Returns:
        JSON confirmation of listening state
    """
    global is_listening
    
    if not is_listening:
        return jsonify({'message': 'Not currently listening', 'listening': False}), 200
    
    is_listening = False
    
    logger.info("[API] Voice listening stopped")
    socketio.emit('listening_status', {'listening': False})
    
    return jsonify({'message': 'Listening stopped', 'listening': False})


@app.route('/api/confirm', methods=['POST'])
def confirm_action():
    """
    Confirm or reject a pending action
    
    Request Body:
        {
            "approved": boolean
        }
    
    Returns:
        JSON with confirmation result
    """
    global pending_confirmation
    
    data = request.json
    approved = data.get('approved', False)
    
    if pending_confirmation is None:
        return jsonify({'error': 'No pending confirmation'}), 400
    
    try:
        logger.info(f"[API] Action {'approved' if approved else 'rejected'}")
        result = controller.confirm_action(approved)
        pending_confirmation = None
        
        # Notify clients
        socketio.emit('confirmation_result', result)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"[API] Error confirming action: {e}", exc_info=True)
        pending_confirmation = None
        return jsonify({
            'status': 'error',
            'message': f'Error confirming action: {str(e)}'
        }), 500


@app.route('/api/speak', methods=['POST'])
def speak_text():
    """
    Make the assistant speak text
    
    Request Body:
        {
            "text": "string"
        }
    
    Returns:
        JSON confirmation
    """
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        logger.info(f"[API] Speaking: {text}")
        speak(text)
        
        socketio.emit('speech_complete', {'text': text})
        
        return jsonify({'message': 'Speech completed', 'text': text})
    except Exception as e:
        logger.error(f"[API] Error speaking: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error speaking: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    Returns:
        JSON with service health status
    """
    return jsonify({
        'status': 'healthy',
        'service': 'voice-assistant-api',
        'version': '1.0.0'
    })


# ============== WEBSOCKET EVENTS ==============

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('[WebSocket] Client connected')
    emit('connection_status', {
        'status': 'connected',
        'listening': is_listening,
        'pending_confirmation': pending_confirmation is not None
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('[WebSocket] Client disconnected')


@socketio.on('send_command')
def handle_command(data):
    """
    Handle command sent via WebSocket
    
    Args:
        data: Dictionary containing 'command' key
    """
    command = data.get('command', '')
    
    if not command:
        emit('error', {'message': 'No command provided'})
        return
    
    try:
        logger.info(f"[WebSocket] Processing command: {command}")
        result = controller.process(command)
        
        # Check if confirmation is required
        if result.get('status') == 'confirmation_required':
            global pending_confirmation
            pending_confirmation = result
            emit('confirmation_required', result, broadcast=True)
        else:
            emit('command_result', result, broadcast=True)
            
    except Exception as e:
        logger.error(f"[WebSocket] Error processing command: {e}", exc_info=True)
        emit('error', {'message': str(e)})


@socketio.on('ping')
def handle_ping():
    """Handle ping from client"""
    emit('pong', {'timestamp': 'now'})


# ============== VOICE LOOP (Background Thread) ==============

def voice_loop():
    """
    Background voice listening loop
    Runs in a separate thread when listening is enabled
    """
    global is_listening, pending_confirmation
    
    logger.info('[Voice Loop] Started')
    
    while is_listening:
        try:
            # Listen for voice input
            text = listen()
            
            if not text:
                continue
            
            logger.info(f"[Voice Loop] Heard: {text}")
            
            # Send transcription to all connected clients
            socketio.emit('voice_input', {'text': text, 'timestamp': 'now'})
            
            normalized = text.lower().strip()
            
            # Check for exit commands
            if normalized in ["exit", "quit", "shutdown", "stop assistant"]:
                logger.info("[Voice Loop] Exit command received")
                is_listening = False
                socketio.emit('assistant_shutdown', {'message': 'Shutting down'})
                speak("Shutting down.")
                break
            
            # Process the command
            result = controller.process(text)
            logger.info(f"[Voice Loop] Result: {result}")
            
            # Handle confirmation requirement
            if result.get('status') == 'confirmation_required':
                pending_confirmation = result
                socketio.emit('confirmation_required', result)
                # Don't speak yet, wait for user confirmation via UI
            else:
                # Get response message
                response = result.get('message', 'Command processed')
                
                # Speak the response
                speak(response)
                
                # Send result to clients
                socketio.emit('command_result', result)
                
        except KeyboardInterrupt:
            logger.info("[Voice Loop] Interrupted")
            is_listening = False
            break
            
        except Exception as e:
            logger.error(f'[Voice Loop] Error: {e}', exc_info=True)
            socketio.emit('error', {
                'message': str(e),
                'source': 'voice_loop'
            })
    
    logger.info('[Voice Loop] Stopped')
    socketio.emit('listening_status', {'listening': False})


# ============== MAIN ENTRY POINT ==============

def run_api_service(host='0.0.0.0', port=5000, debug=False):
    """
    Run the API service
    
    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to listen on (default: 5000)
        debug: Enable debug mode (default: False)
    """
    logger.info(f'API Service starting on http://{host}:{port}')
    logger.info('Available endpoints:')
    logger.info('  GET  /api/health - Health check')
    logger.info('  GET  /api/status - Get current status')
    logger.info('  POST /api/process_command - Process text command')
    logger.info('  POST /api/start_listening - Start voice listening')
    logger.info('  POST /api/stop_listening - Stop voice listening')
    logger.info('  POST /api/confirm - Confirm/reject pending action')
    logger.info('  POST /api/speak - Make assistant speak')
    logger.info('WebSocket events:')
    logger.info('  connect - Client connection')
    logger.info('  send_command - Send command via WebSocket')
    logger.info('  ping - Ping server')
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_api_service(debug=True)
