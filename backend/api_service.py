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

from backend.config.secrets import ensure_runtime_secrets

# Auto-provision required secrets for first-run local desktop UX.
ensure_runtime_secrets()

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from backend.core.assistant_controller import AssistantController
from backend.core.controller_manager import ControllerManager
from backend.core.response_formatter import ResponseFormatter
from backend.voice_engine.audio_pipeline import listen_for_gui_adaptive, speak
from backend.voice_engine.wake_word_detector import WakeWordDetector
from backend.config.logger import logger
from backend.core.persona import persona
from backend.config.assistant_config import assistant_config
from backend.auth.auth_service import AuthService, PasswordHasher
from backend.middleware.auth_middleware import login_required, admin_required
from backend.middleware.validation import (
    LoginSchema,
    RegisterSchema,
    CommandSchema,
    SettingsSchema,
    ScheduleTaskSchema,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema,
)
from backend.database import SessionLocal, init_db
from backend.database.models import User
from backend.scheduling.natural_language import parse_natural_schedule_command
from backend.scheduling.task_scheduler import TaskSchedulerService
import threading
from typing import Optional, Dict, Any
from functools import lru_cache
from marshmallow import ValidationError
import time


def _get_required_env(name: str) -> str:
    """Read a required environment variable and fail fast if missing."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it before starting the API service."
        )
    return value


def _get_allowed_origins() -> list:
    """Parse trusted CORS origins from environment."""
    raw = os.environ.get(
        "OMNIASSIST_CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:5000,http://localhost:5000",
    )
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["http://127.0.0.1:5000", "http://localhost:5000"]


APP_SECRET_KEY = _get_required_env("OMNIASSIST_FLASK_SECRET_KEY")
ALLOWED_ORIGINS = _get_allowed_origins()

app = Flask(__name__)
app.config['SECRET_KEY'] = APP_SECRET_KEY
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})
socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Global state
controller_manager = ControllerManager(controller_factory=AssistantController)
task_scheduler = TaskSchedulerService(controller_manager=controller_manager, socketio=socketio, session_factory=SessionLocal)
response_formatter = ResponseFormatter()
is_listening = False
listening_user_id: Optional[int] = None
listening_thread: Optional[threading.Thread] = None
wake_word_detector: Optional[WakeWordDetector] = None

# Cache for recent commands to avoid duplicate processing
_command_cache = {}
_cache_timeout = 1.0  # 1 second cache for duplicate commands
_socket_users: Dict[str, Dict[str, Any]] = {}


def _get_user_scope(user_id: Any) -> str:
    """Create a stable controller scope key for a user."""
    return f"user:{user_id}"


def _get_voice_scope() -> str:
    """Return the dedicated scope used by the voice loop."""
    return "voice"


def _get_controller_for_http_request() -> AssistantController:
    """Return the controller scoped to the authenticated HTTP user."""
    return controller_manager.get_controller(_get_user_scope(request.current_user.id))


def _get_controller_for_socket() -> AssistantController:
    """Return the controller scoped to the authenticated socket user."""
    socket_user = _socket_users.get(request.sid, {})
    return controller_manager.get_controller(_get_user_scope(socket_user.get("id", request.sid)))


def _get_voice_controller() -> AssistantController:
    """Return the controller used for voice-driven interactions."""
    return controller_manager.get_controller(_get_voice_scope())


def _format_task_preview(task: dict) -> str:
    task_id = task.get("id")
    name = task.get("name") or "Scheduled task"
    next_run = task.get("next_run_at") or "not scheduled"
    return f"#{task_id} {name} (next: {next_run})"


def _style_result(result: dict, status: str) -> dict:
    styled = response_formatter.format(result)
    styled["message"] = persona.stylize_response(styled.get("message", ""), status=status)
    return styled


def _handle_natural_schedule_command(command: str, user_id: Optional[int], language: Optional[str] = None):
    """Handle user-friendly schedule commands before LLM planning."""
    intent = parse_natural_schedule_command(command)
    if not intent:
        return None

    if not user_id:
        return _style_result({
            "status": "error",
            "message": "Scheduling requires an authenticated user session.",
            "data": {},
        }, status="error")

    action = intent.get("action")

    if action == "invalid":
        return _style_result({
            "status": "error",
            "message": intent.get("message", "Invalid schedule request."),
            "data": {},
        }, status="error")

    if action == "list":
        tasks = task_scheduler.list_tasks_for_user(user_id)
        if not tasks:
            message = "You do not have any scheduled tasks yet."
        else:
            preview = "; ".join(_format_task_preview(task) for task in tasks[:5])
            message = f"Your scheduled tasks: {preview}"

        return _style_result({
            "status": "success",
            "message": message,
            "data": {"tasks": tasks},
        }, status="success")

    if action == "delete":
        task_id = intent.get("task_id")
        deleted = task_scheduler.delete_task(user_id, task_id)
        if not deleted:
            return _style_result({
                "status": "error",
                "message": f"Could not find schedule {task_id}.",
                "data": {"task_id": task_id},
            }, status="error")

        return _style_result({
            "status": "success",
            "message": f"Schedule {task_id} cancelled.",
            "data": {"task_id": task_id},
        }, status="success")

    if action == "create":
        task = task_scheduler.create_task(
            user_id=user_id,
            name=intent.get("name") or intent.get("command"),
            command=intent["command"],
            language=language,
            trigger_type=intent["trigger_type"],
            interval_seconds=intent.get("interval_seconds"),
            cron_expression=intent.get("cron_expression"),
        )
        return _style_result({
            "status": "success",
            "message": f"Scheduled '{intent['command']}' {intent.get('description', 'successfully')} as task #{task['id']}.",
            "data": {"task": task},
        }, status="success")

    return None


@app.after_request
def apply_security_headers(response):
    """Set baseline HTTP security headers for API responses."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "microphone=(), camera=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def _authenticate_socket(auth_payload):
    """Validate socket auth payload and return current user payload."""
    token = ""
    if isinstance(auth_payload, dict):
        token = str(auth_payload.get("token", "")).strip()

    if not token:
        return False, "Missing token", None

    db = SessionLocal()
    try:
        auth_service = AuthService(db)
        valid, message, payload = auth_service.verify_token(token)
        if not valid:
            return False, message, None

        user = auth_service.get_user_by_id(payload["user_id"])
        if not user or not user.is_active:
            return False, "User not found or inactive", None

        return True, "ok", {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
    finally:
        db.close()


def emit_execution_steps(plan_data):
    """Emit execution steps to connected clients.
    
    Args:
        plan_data: The plan data containing steps to execute
    """
    if not plan_data or not isinstance(plan_data, dict):
        return
    
    steps = plan_data.get('steps', [])
    if not steps:
        # Try alternative format
        if 'tool_calls' in plan_data:
            steps = plan_data['tool_calls']
    
    for i, step in enumerate(steps, 1):
        step_desc = ""
        if isinstance(step, dict):
            tool = step.get('tool', step.get('name', ''))
            params = step.get('parameters', step.get('params', {}))
            step_desc = f"{tool}"
            if params:
                # Create readable description from params
                param_str = ", ".join(f"{k}={v}" for k, v in list(params.items())[:2])
                step_desc = f"{tool} ({param_str})"
        else:
            step_desc = str(step)
        
        socketio.emit('execution_step', {
            'step': i,
            'description': step_desc,
            'status': 'running'
        })
        logger.info(f"[Execution] Step {i}: {step_desc}")


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
        'pending_confirmation': controller_manager.has_any_pending_confirmation(),
        'confirmation_details': controller_manager.get_pending_confirmation(_get_voice_scope())
    })


@app.route('/api/process_command', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
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
    data = request.json or {}
    command = data.get('command', '')
    language = data.get('language')

    try:
        schema = CommandSchema()
        validated = schema.load({'command': command})
        command = validated['command']
    except ValidationError as err:
        return jsonify({
            'status': 'error',
            'message': 'Validation failed',
            'errors': err.messages
        }), 400
    
    try:
        logger.info(f"[API] Processing command: {command}")
        
        # Check for exit commands
        normalized = command.lower().strip()
        if normalized in ["exit", "quit", "shutdown", "stop assistant", "goodbye", "close"]:
            logger.info(f"[API] Exit command received: {command}")
            
            # Emit shutdown event to all clients
            socketio.emit('assistant_shutdown', {
                'message': 'Shutting down assistant. Goodbye!',
                'command': command
            })
            
            # Return shutdown response
            return jsonify({
                'status': 'shutdown',
                'message': 'Shutting down assistant. Goodbye!',
                'data': {}
            })
        
        schedule_result = _handle_natural_schedule_command(command, request.current_user.id, language=language)
        if schedule_result:
            socketio.emit('command_result', schedule_result)
            return jsonify(schedule_result)

        # Don't duplicate LLM calls - let controller handle plan generation
        # Process the command (this handles plan generation internally)
        controller = _get_controller_for_http_request()
        result = controller.process(command, language=language)

        # Emit the actual executed plan steps from controller state
        executed_plan = controller.get_last_plan_data()
        if executed_plan and isinstance(executed_plan, dict):
            emit_execution_steps(executed_plan)
        
        # Check if confirmation is required
        if result.get('status') == 'confirmation_required':
            # Notify WebSocket clients
            socketio.emit('confirmation_required', result)
        else:
            # Emit command result
            socketio.emit('command_result', result)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"[API] Error processing command: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error processing command: {str(e)}'
        }), 500


@app.route('/api/start_listening', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def start_listening():
    """
    Start voice listening mode
    
    Returns:
        JSON confirmation of listening state
    """
    global is_listening, listening_thread, listening_user_id
    
    try:
        if is_listening:
            return jsonify({'message': 'Already listening', 'listening': True}), 200
        
        listening_user_id = request.current_user.id
        is_listening = True
        listening_thread = threading.Thread(target=voice_loop, daemon=True)
        listening_thread.start()
        
        logger.info("[API] Voice listening started")
        socketio.emit('listening_status', {'listening': True})
        
        return jsonify({'message': 'Listening started', 'listening': True})
    except Exception as e:
        logger.error(f"[API] Error starting voice listening: {e}", exc_info=True)
        is_listening = False
        return jsonify({'error': f'Failed to start listening: {str(e)}'}), 500


@app.route('/api/stop_listening', methods=['POST'])
@login_required
def stop_listening():
    """
    Stop voice listening mode
    
    Returns:
        JSON confirmation of listening state
    """
    global is_listening, listening_user_id
    
    try:
        if not is_listening:
            return jsonify({'message': 'Not currently listening', 'listening': False}), 200
        
        is_listening = False
        listening_user_id = None
        
        logger.info("[API] Voice listening stopped")
        socketio.emit('listening_status', {'listening': False})
        
        return jsonify({'message': 'Listening stopped', 'listening': False})
    except Exception as e:
        logger.error(f"[API] Error stopping voice listening: {e}", exc_info=True)
        return jsonify({'error': f'Failed to stop listening: {str(e)}'}), 500


@app.route('/api/wake_word/start', methods=['POST'])
@login_required
def start_wake_word():
    """
    Start wake word detection
    
    Returns:
        JSON confirmation of wake word detection state
    """
    global wake_word_detector
    
    try:
        if wake_word_detector is None:
            # Initialize wake word detector with callback
            wake_word_detector = WakeWordDetector(callback=on_wake_word_detected)
        
        if wake_word_detector.is_active:
            return jsonify({'message': 'Wake word detection already active', 'active': True}), 200
        
        wake_word_detector.start()
        logger.info("[API] Wake word detection started")
        socketio.emit('wake_word_status', {'active': True})
        
        return jsonify({'message': 'Wake word detection started', 'active': True})
    except Exception as e:
        logger.error(f"[API] Error starting wake word detection: {e}", exc_info=True)
        return jsonify({'error': f'Failed to start wake word detection: {str(e)}'}), 500


@app.route('/api/wake_word/stop', methods=['POST'])
@login_required
def stop_wake_word():
    """
    Stop wake word detection
    
    Returns:
        JSON confirmation of wake word detection state
    """
    global wake_word_detector
    
    try:
        if wake_word_detector is None or not wake_word_detector.is_active:
            return jsonify({'message': 'Wake word detection not active', 'active': False}), 200
        
        wake_word_detector.stop()
        logger.info("[API] Wake word detection stopped")
        socketio.emit('wake_word_status', {'active': False})
        
        return jsonify({'message': 'Wake word detection stopped', 'active': False})
    except Exception as e:
        logger.error(f"[API] Error stopping wake word detection: {e}", exc_info=True)
        return jsonify({'error': f'Failed to stop wake word detection: {str(e)}'}), 500


@app.route('/api/wake_word/status', methods=['GET'])
@login_required
def wake_word_status():
    """
    Get wake word detection status
    
    Returns:
        JSON with wake word detection state
    """
    global wake_word_detector
    
    is_active = wake_word_detector is not None and wake_word_detector.is_active
    wake_words = assistant_config.get('wake_word.words', ['otto'])
    
    return jsonify({
        'active': is_active,
        'wake_words': wake_words,
        'enabled_in_config': assistant_config.get('wake_word.enabled', False)
    })


@app.route('/api/confirm', methods=['POST'])
@login_required
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
    data = request.json
    approved = data.get('approved', False)

    controller = _get_controller_for_http_request()
    if not controller.has_pending_confirmation():
        return jsonify({'error': 'No pending confirmation'}), 400
    
    try:
        logger.info(f"[API] Action {'approved' if approved else 'rejected'}")
        result = controller.confirm_action(approved)
        
        # Notify clients
        socketio.emit('confirmation_result', result)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"[API] Error confirming action: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error confirming action: {str(e)}'
        }), 500


@app.route('/api/speak', methods=['POST'])
@login_required
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


@app.route('/api/settings', methods=['POST'])
@login_required
@admin_required
@limiter.limit("20 per minute")
def update_settings():
    """
    Update assistant settings (persona, language, memory, etc.)
    
    Request Body:
        {
            "persona": "friendly" | "professional" | "butler" | "concise",
            "language": "en" | "hi" | "hinglish" | "es" | "fr",
            "memory_enabled": true | false
        }
    
    Returns:
        JSON confirmation
    """
    data = request.json
    
    if not data:
        return jsonify({'error': 'No settings provided'}), 400
    
    try:
        updated = []
        errors = []
        
        # Update persona
        if 'persona' in data:
            try:
                persona_mode = data['persona']
                # Save to config first
                success = assistant_config.set('assistant.active_persona', persona_mode)
                if success:
                    # Reload persona engine to pick up changes
                    persona.reload(mode=persona_mode)
                    updated.append(f"persona={persona_mode}")
                    logger.info(f"[Settings] Persona updated to: {persona_mode}")
                else:
                    errors.append(f"persona: failed to save to config")
                    logger.error(f"[Settings] Failed to save persona to config")
            except Exception as e:
                errors.append(f"persona: {str(e)}")
                logger.error(f"[Settings] Error updating persona: {e}", exc_info=True)
        
        # Update language
        if 'language' in data:
            try:
                language = data['language']
                success = assistant_config.set('stt.language', language)
                if success:
                    updated.append(f"language={language}")
                    logger.info(f"[Settings] Language updated to: {language}")
                else:
                    errors.append(f"language: failed to save to config")
                    logger.error(f"[Settings] Failed to save language to config")
            except Exception as e:
                errors.append(f"language: {str(e)}")
                logger.error(f"[Settings] Error updating language: {e}", exc_info=True)
        
        # Update memory
        if 'memory_enabled' in data:
            try:
                memory_enabled = data['memory_enabled']
                success = assistant_config.set('memory.enabled', memory_enabled)
                if success:
                    updated.append(f"memory={memory_enabled}")
                    logger.info(f"[Settings] Memory updated to: {memory_enabled}")
                else:
                    errors.append(f"memory: failed to save to config")
                    logger.error(f"[Settings] Failed to save memory to config")
            except Exception as e:
                errors.append(f"memory: {str(e)}")
                logger.error(f"[Settings] Error updating memory: {e}", exc_info=True)
        
        # Note: assistant_config.set() already saves to disk, no need to call save()
        
        result = {
            'status': 'success' if not errors else 'partial' if updated else 'error',
            'updated': updated,
            'errors': errors,
            'message': f"Settings updated: {', '.join(updated)}" if updated else "No settings updated",
            'settings': {
                'persona': persona.mode,
                'language': assistant_config.get('stt.language', 'en'),
                'memory_enabled': assistant_config.get('memory.enabled', True)
            }
        }
        
        if errors:
            result['message'] += f"; Errors: {', '.join(errors)}"
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"[Settings] Error updating settings: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Error updating settings: {str(e)}'
        }), 500


@app.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    """
    Get current assistant settings
    
    Returns:
        JSON with current settings
    """
    return jsonify({
        'persona': persona.mode,
        'language': assistant_config.get('stt.language', 'en'),
        'memory_enabled': assistant_config.get('memory.enabled', True)
    })


@app.route('/api/schedules', methods=['GET'])
@login_required
def list_scheduled_tasks():
    """List scheduled tasks for the authenticated user."""
    tasks = task_scheduler.list_tasks_for_user(request.current_user.id)
    return jsonify({
        'status': 'success',
        'tasks': tasks,
    })


@app.route('/api/schedules', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def create_scheduled_task():
    """Create a one-time or recurring scheduled task for the authenticated user."""
    try:
        schema = ScheduleTaskSchema()
        data = schema.load(request.json or {})

        task = task_scheduler.create_task(
            user_id=request.current_user.id,
            name=data.get('name') or data['command'],
            command=data['command'],
            language=data.get('language'),
            trigger_type=data['trigger_type'],
            run_at=data.get('run_at'),
            interval_seconds=data.get('interval_seconds'),
            cron_expression=data.get('cron_expression'),
        )

        return jsonify({
            'status': 'success',
            'message': 'Scheduled task created successfully',
            'task': task,
        }), 201
    except ValidationError as err:
        return jsonify({
            'status': 'error',
            'message': 'Validation failed',
            'errors': err.messages,
        }), 400
    except ValueError as err:
        return jsonify({
            'status': 'error',
            'message': str(err),
        }), 400
    except Exception as e:
        logger.error(f"[Scheduler] Error creating task: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Failed to create scheduled task: {str(e)}'
        }), 500


@app.route('/api/schedules/<int:task_id>', methods=['DELETE'])
@login_required
def delete_scheduled_task(task_id: int):
    """Delete a scheduled task owned by the authenticated user."""
    deleted = task_scheduler.delete_task(request.current_user.id, task_id)
    if not deleted:
        return jsonify({
            'status': 'error',
            'message': 'Scheduled task not found',
        }), 404

    return jsonify({
        'status': 'success',
        'message': 'Scheduled task deleted successfully',
    })


# ============== AUTHENTICATION ENDPOINTS ==============

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    """
    Register a new user (self-registration enabled)
    
    First user registered will be ADMIN, subsequent users will be USERS
    
    Request Body:
        {
            "username": "string",
            "email": "string",
            "password": "string"
        }
    
    Returns:
        JSON with registration result
    """
    try:
        # Validate input
        schema = RegisterSchema()
        data = schema.load(request.json)
        
        db = SessionLocal()
        auth_service = AuthService(db)
        
        # Check if this is the first user (auto-admin)
        user_count = db.query(User).count()
        role = "admin" if user_count == 0 else "user"
        
        # Create user
        success, message, user = auth_service.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=role
        )
        
        if success:
            # Extract user data BEFORE closing session to avoid detached object errors
            user_username = user.username
            user_email = user.email
            user_role = user.role
            
            db.close()
            
            logger.info(f"[Auth] User registered: {data['username']} (role: {role})")
            return jsonify({
                'status': 'success',
                'message': message,
                'user': {
                    'username': user_username,
                    'email': user_email,
                    'role': user_role
                }
            }), 201
        else:
            db.close()
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
            
    except ValidationError as err:
        return jsonify({
            'status': 'error',
            'message': 'Validation failed',
            'errors': err.messages
        }), 400
    except Exception as e:
        logger.error(f"[Auth] Registration error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Registration failed: {str(e)}'
        }), 500


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    Login and receive JWT token
    
    Request Body:
        {
            "username": "string",
            "password": "string"
        }
    
    Returns:
        JSON with token and user info
    """
    try:
        # Validate input
        schema = LoginSchema()
        data = schema.load(request.json)
        
        db = SessionLocal()
        auth_service = AuthService(db)
        
        # Authenticate user
        success, message, user = auth_service.authenticate_user(
            username=data['username'],
            password=data['password']
        )
        
        if not success:
            db.close()
            return jsonify({
                'status': 'error',
                'message': message
            }), 401
        
        # Create JWT token
        token, expires_at = auth_service.create_token(
            user=user,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # Extract user data BEFORE closing session to avoid detached object errors
        user_id = user.id
        user_username = user.username
        user_email = user.email
        user_role = user.role
        
        db.close()
        
        logger.info(f"[Auth] User logged in: {user_username}")
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'token': token,
            'expires_at': expires_at.isoformat(),
            'user': {
                'id': user_id,
                'username': user_username,
                'email': user_email,
                'role': user_role
            }
        }), 200
        
    except ValidationError as err:
        return jsonify({
            'status': 'error',
            'message': 'Validation failed',
            'errors': err.messages
        }), 400
    except Exception as e:
        logger.error(f"[Auth] Login error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Login failed: {str(e)}'
        }), 500


@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    """
    Logout and revoke JWT token
    
    Returns:
        JSON confirmation
    """
    try:
        # Get token from request
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split()[1]
            
            db = SessionLocal()
            auth_service = AuthService(db)
            auth_service.revoke_token(token)
            db.close()
            
            logger.info(f"[Auth] User logged out: {request.current_user.username}")
        
        return jsonify({
            'status': 'success',
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"[Auth] Logout error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Logout failed: {str(e)}'
        }), 500


@app.route('/api/auth/verify', methods=['GET'])
@login_required
def verify_token():
    """
    Verify if current token is valid
    
    Returns:
        JSON with user info
    """
    return jsonify({
        'status': 'success',
        'message': 'Token is valid',
        'user': {
            'id': request.current_user.id,
            'username': request.current_user.username,
            'email': request.current_user.email,
            'role': request.current_user.role
        }
    }), 200


@app.route('/api/auth/password-reset/request', methods=['POST'])
@limiter.limit("5 per hour")
def password_reset_request():
    """Request a password reset email for an account."""
    try:
        schema = PasswordResetRequestSchema()
        data = schema.load(request.json)

        db = SessionLocal()
        auth_service = AuthService(db)
        success, message = auth_service.request_password_reset(
            email=data['email'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.close()

        if success:
            return jsonify({
                'status': 'success',
                'message': message
            }), 200

        return jsonify({
            'status': 'error',
            'message': message
        }), 500

    except ValidationError as err:
        return jsonify({
            'status': 'error',
            'message': 'Validation failed',
            'errors': err.messages
        }), 400
    except Exception as e:
        logger.error(f"[Auth] Password reset request error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Password reset request failed: {str(e)}'
        }), 500


@app.route('/api/auth/password-reset/confirm', methods=['POST'])
@limiter.limit("10 per hour")
def password_reset_confirm():
    """Confirm password reset with one-time token and a new password."""
    try:
        schema = PasswordResetConfirmSchema()
        data = schema.load(request.json)

        db = SessionLocal()
        auth_service = AuthService(db)
        success, message = auth_service.reset_password_with_token(
            token=data['token'],
            new_password=data['new_password']
        )
        db.close()

        if success:
            return jsonify({
                'status': 'success',
                'message': message
            }), 200

        return jsonify({
            'status': 'error',
            'message': message
        }), 400

    except ValidationError as err:
        return jsonify({
            'status': 'error',
            'message': 'Validation failed',
            'errors': err.messages
        }), 400
    except Exception as e:
        logger.error(f"[Auth] Password reset confirm error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Password reset failed: {str(e)}'
        }), 500


# ============== WEBSOCKET EVENTS ==============

@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection"""
    valid, message, socket_user = _authenticate_socket(auth)
    if not valid:
        logger.warning(f"[WebSocket] Authentication failed: {message}")
        return False

    _socket_users[request.sid] = socket_user
    controller = controller_manager.get_controller(_get_user_scope(socket_user['id']))
    logger.info(f"[WebSocket] Client connected: {socket_user['username']} ({request.sid})")
    emit('connection_status', {
        'status': 'connected',
        'listening': is_listening,
        'pending_confirmation': controller.has_pending_confirmation(),
        'wake_word_active': wake_word_detector is not None and wake_word_detector.is_active
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    _socket_users.pop(request.sid, None)
    logger.info(f"[WebSocket] Client disconnected: {request.sid}")


@socketio.on('send_command')
def handle_command(data):
    """
    Handle command sent via WebSocket
    
    Args:
        data: Dictionary containing 'command' key
    """
    command = data.get('command', '')
    language = data.get('language') if isinstance(data, dict) else None

    if request.sid not in _socket_users:
        emit('error', {'message': 'Authentication required'})
        return
    
    try:
        schema = CommandSchema()
        validated = schema.load({'command': command})
        command = validated['command']
    except ValidationError as err:
        emit('error', {'message': 'Validation failed', 'errors': err.messages})
        return

    try:
        socket_user = _socket_users.get(request.sid, {})
        schedule_result = _handle_natural_schedule_command(command, socket_user.get('id'), language=language)
        if schedule_result:
            emit('command_result', schedule_result)
            return

        controller = _get_controller_for_socket()
        result = controller.process(command, language=language)
        executed_plan = controller.get_last_plan_data()
        if executed_plan and isinstance(executed_plan, dict):
            emit_execution_steps(executed_plan)
        
        # Check if confirmation is required
        if result.get('status') == 'confirmation_required':
            emit('confirmation_required', result)
        else:
            emit('command_result', result)
            
    except Exception as e:
        logger.error(f"[WebSocket] Error processing command: {e}", exc_info=True)
        emit('error', {'message': str(e)})


@socketio.on('ping')
def handle_ping():
    """Handle ping from client"""
    emit('pong', {'timestamp': 'now'})


# ============== WAKE WORD CALLBACK ==============

def on_wake_word_detected(wake_word: str):
    """
    Callback when wake word is detected.
    Automatically starts voice listening.
    
    Args:
        wake_word: The wake word that was detected
    """
    global is_listening, listening_thread, wake_word_detector
    
    logger.info(f"[WakeWord] '{wake_word}' detected - starting voice listening")
    
    # Emit wake word detection event to clients
    socketio.emit('wake_word_detected', {'word': wake_word})
    
    # Start voice listening if not already active
    if not is_listening:
        is_listening = True
        listening_thread = threading.Thread(target=voice_loop, daemon=True)
        listening_thread.start()
        
        logger.info("[WakeWord] Voice listening started automatically")
        socketio.emit('listening_status', {'listening': True, 'triggered_by_wake_word': True})
    else:
        logger.debug("[WakeWord] Voice listening already active, ignoring detection")


# ============== VOICE LOOP (Background Thread) ==============

def voice_loop():
    """
    Background voice listening loop
    Runs in a separate thread when listening is enabled
    Uses adaptive/proximity-based listening (stops on silence, not fixed duration)
    """
    global is_listening, wake_word_detector, listening_user_id
    
    logger.info('[Voice Loop] Started (Adaptive mode - proximity-favored)')
    
    # Pause wake word detection during active listening
    if wake_word_detector and wake_word_detector.is_active:
        wake_word_detector.pause()
        logger.debug("[Voice Loop] Wake word detection paused during active listening")

    controller = _get_voice_controller()
    
    while is_listening:
        try:
            # Listen for voice input (adaptive mode - stops on silence)
            text = listen_for_gui_adaptive()
            
            if not text:
                logger.debug("[Voice Loop] No speech detected in this recording window")
                continue
            
            logger.info(f"[Voice Loop] Heard: {text}")
            
            # Filter out TTS feedback: repetitive or nonsensical transcriptions
            # These occur when microphone picks up speaker output
            words = text.lower().split()
            if len(words) > 10:
                # Check for excessive repetition (e.g., "1, 2, 1, 2, 1, 2...")
                unique_ratio = len(set(words)) / len(words)
                if unique_ratio < 0.3:  # Less than 30% unique words
                    logger.warning(f"[Voice Loop] Filtering TTS feedback (repetitive): {unique_ratio:.2%} unique")
                    continue
            
            # Skip very long rambling transcriptions (typical of TTS feedback)
            if len(text) > 300:
                logger.warning(f"[Voice Loop] Filtering TTS feedback (too long): {len(text)} chars")
                continue
            
            # Send transcription to all connected clients
            socketio.emit('voice_input', {'text': text, 'final': True})
            
            normalized = text.lower().strip()
            normalized_clean = " ".join(
                "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in normalized).split()
            )

            # Voice command: stop listening mode (without shutting down assistant)
            stop_listening_aliases = [
                "stop listening",
                "stp listening",
                "stop listning",
                "stop listen",
                "stop voice",
                "stop recording",
                "stop hearing",
                "thats all",
                "that's all",
            ]
            if any(alias in normalized_clean for alias in stop_listening_aliases):
                logger.info(f"[Voice Loop] Stop-listening command received: {text}")
                is_listening = False
                socketio.emit('command_result', {
                    'status': 'success',
                    'message': 'Listening stopped.'
                })
                speak("Stopping listening mode.")
                break
            
            # Check for exit commands
            if normalized_clean in ["exit", "quit", "shutdown", "stop assistant", "goodbye", "close"]:
                logger.info("[Voice Loop] Exit command received")
                is_listening = False
                socketio.emit('assistant_shutdown', {
                    'message': 'Shutting down assistant. Goodbye!',
                    'command': text
                })
                speak("Shutting down assistant. Goodbye!")
                break
            
            # Process scheduling commands directly before invoking the general planner
            schedule_result = _handle_natural_schedule_command(text, listening_user_id)
            if schedule_result:
                result = schedule_result
            else:
                # Process the command via controller's agent loop
                result = controller.process(text)

            # Emit steps from the loop's executed plan (single source of truth)
            executed_plan = controller.get_last_plan_data()
            if executed_plan and isinstance(executed_plan, dict):
                emit_execution_steps(executed_plan)

            logger.info(f"[Voice Loop] Result: {result}")
            
            # Handle confirmation requirement
            if result.get('status') == 'confirmation_required':
                socketio.emit('confirmation_required', result)
                # Don't speak yet, wait for user confirmation via UI
            else:
                # Get response message
                response = result.get('message', 'Command processed')
                
                # Speak the response
                speak(response)
                
                # Send result to clients
                socketio.emit('command_result', result)
                
                # Wait after speaking to prevent microphone from picking up TTS audio
                # This prevents feedback loop where mic captures speaker output
                logger.debug("[Voice Loop] Pausing to prevent TTS feedback...")
                time.sleep(1.5)
                
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
    listening_user_id = None
    socketio.emit('listening_status', {'listening': False})
    
    # Resume wake word detection after voice loop stops
    if wake_word_detector and wake_word_detector.is_active:
        wake_word_detector.resume()
        logger.debug("[Voice Loop] Wake word detection resumed")


# ============== MAIN ENTRY POINT ==============

def initialize_database():
    """Initialize database and optionally bootstrap an admin from env vars."""
    try:
        # Initialize database tables
        init_db()
        logger.info("[Database] Database initialized successfully")
        
        # Check if any users exist
        db = SessionLocal()
        user_count = db.query(User).count()
        
        if user_count == 0:
            bootstrap_username = os.environ.get('OMNIASSIST_BOOTSTRAP_ADMIN_USERNAME', '').strip()
            bootstrap_email = os.environ.get('OMNIASSIST_BOOTSTRAP_ADMIN_EMAIL', '').strip()
            bootstrap_password = os.environ.get('OMNIASSIST_BOOTSTRAP_ADMIN_PASSWORD', '').strip()

            if bootstrap_username and bootstrap_email and bootstrap_password:
                auth_service = AuthService(db)
                success, message, _ = auth_service.create_user(
                    username=bootstrap_username,
                    email=bootstrap_email,
                    password=bootstrap_password,
                    role="admin"
                )

                if success:
                    logger.info("[Auth] Bootstrap admin created from environment variables")
                    logger.info(f"[Auth] Bootstrap admin username: {bootstrap_username}")
                else:
                    logger.error(f"[Auth] Failed to create bootstrap admin: {message}")
            elif any([bootstrap_username, bootstrap_email, bootstrap_password]):
                logger.error(
                    "[Auth] Incomplete admin bootstrap configuration. "
                    "Set OMNIASSIST_BOOTSTRAP_ADMIN_USERNAME, OMNIASSIST_BOOTSTRAP_ADMIN_EMAIL, "
                    "and OMNIASSIST_BOOTSTRAP_ADMIN_PASSWORD together."
                )
            else:
                logger.warning(
                    "[Auth] No users found and no bootstrap admin configured. "
                    "Register the first user via /api/auth/register (first account becomes admin)."
                )
        else:
            logger.info(f"[Database] Found {user_count} existing user(s)")
        
        db.close()
        
    except Exception as e:
        logger.error(f"[Database] Initialization error: {e}", exc_info=True)


def initialize_wake_word():
    """Initialize wake-word detector at startup when enabled in config."""
    global wake_word_detector

    try:
        enabled = bool(assistant_config.get('wake_word.enabled', False))
        # Launcher can force-disable wake-word autostart for API stability.
        env_override = os.environ.get('OMNIASSIST_WAKE_WORD_AUTOSTART', '').strip().lower()
        if env_override in {'0', 'false', 'no', 'off'}:
            enabled = False
        elif env_override in {'1', 'true', 'yes', 'on'}:
            enabled = True

        if not enabled:
            logger.info('[WakeWord] Startup auto-enable is OFF')
            return

        if wake_word_detector is None:
            wake_word_detector = WakeWordDetector(callback=on_wake_word_detected)

        if not wake_word_detector.is_active:
            wake_word_detector.start()
            logger.info('[WakeWord] Startup auto-enable is ON. Detection started.')
        else:
            logger.info('[WakeWord] Detection already active at startup.')
    except Exception as e:
        logger.error(f"[WakeWord] Startup initialization error: {e}", exc_info=True)


def initialize_scheduler():
    """Start the task scheduler after the database is ready."""
    try:
        task_scheduler.start()
    except Exception as e:
        logger.error(f"[TaskScheduler] Startup initialization error: {e}", exc_info=True)


def run_api_service(host='0.0.0.0', port=5000, debug=False):
    """
    Run the API service
    
    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to listen on (default: 5000)
        debug: Enable debug mode (default: False)
    """
    # Initialize database and create default admin if needed
    initialize_database()
    initialize_scheduler()
    initialize_wake_word()
    
    logger.info(f'API Service starting on http://{host}:{port}')
    logger.info('Available endpoints:')
    logger.info('  GET  /api/health - Health check')
    logger.info('  GET  /api/status - Get current status')
    logger.info('  POST /api/process_command - Process text command (protected)')
    logger.info('  POST /api/start_listening - Start voice listening (protected)')
    logger.info('  POST /api/stop_listening - Stop voice listening')
    logger.info('  POST /api/confirm - Confirm/reject pending action')
    logger.info('  POST /api/speak - Make assistant speak')
    logger.info('  POST /api/settings - Update settings (protected)')
    logger.info('  GET  /api/settings - Get settings')
    logger.info('  GET  /api/schedules - List scheduled tasks (protected)')
    logger.info('  POST /api/schedules - Create scheduled task (protected)')
    logger.info('  DELETE /api/schedules/<id> - Delete scheduled task (protected)')
    logger.info('  POST /api/auth/register - Register new user')
    logger.info('  POST /api/auth/login - Login and get token')
    logger.info('  POST /api/auth/logout - Logout (protected)')
    logger.info('  GET  /api/auth/verify - Verify token (protected)')
    logger.info('WebSocket events:')
    logger.info('  connect - Client connection')
    logger.info('  send_command - Send command via WebSocket')
    logger.info('  ping - Ping server')
    
    # IMPORTANT: disable reloader for threaded background services (wake-word loop).
    # Flask reloader starts the app twice in debug mode, which duplicates detector threads.
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )


if __name__ == '__main__':
    # Keep debug off for stable background voice/wake-word threads.
    run_api_service(debug=False)
