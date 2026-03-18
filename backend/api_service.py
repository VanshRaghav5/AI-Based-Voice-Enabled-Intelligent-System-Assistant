"""
Backend API Service for Voice Assistant

This service exposes REST API endpoints and WebSocket connections
to allow the desktop application to interact with the backend functionality.
"""

import sys
import os
from pathlib import Path
import secrets


def _load_dotenv(dotenv_path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file into the process environment.

    - Ignores blank lines and comments.
    - Does not override already-set environment variables.
    - Supports quoted values (single or double quotes).
    """
    try:
        if not dotenv_path.exists() or not dotenv_path.is_file():
            return

        for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                continue
            if key in os.environ and os.environ[key].strip():
                continue

            if (len(value) >= 2) and ((value[0] == value[-1]) and value[0] in ("\"", "'")):
                value = value[1:-1]

            os.environ[key] = value
    except Exception:
        # Never fail startup due to .env parsing issues.
        return

# Add project root to Python path to support running from any directory
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load local environment variables early (before importing modules that may read env vars).
_load_dotenv(project_root / ".env")

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from backend.core import runtime_events
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
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema,
)
from backend.database import SessionLocal, init_db
from backend.database.models import User
import threading
from typing import Optional, Dict, Any
from functools import lru_cache
from marshmallow import ValidationError
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.core.assistant_controller import AssistantController
    from backend.voice_engine.wake_word_detector import WakeWordDetector


def _get_required_env(name: str) -> str:
    """Read a required environment variable and fail fast if missing."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it before starting the API service."
        )
    return value


def _get_or_generate_secret(name: str) -> str:
    """Return env var value or generate a dev-friendly ephemeral secret.

    This prevents the backend from silently exiting when started in the background.
    """
    value = os.environ.get(name, "").strip()
    if value:
        return value

    generated = secrets.token_urlsafe(64)
    os.environ[name] = generated
    logger.warning(
        f"[Config] {name} is not set; using an ephemeral generated secret. "
        "Create a .env (see .env.example) to keep it stable across restarts."
    )
    return generated


def _get_allowed_origins() -> list:
    """Parse trusted CORS origins from environment."""
    raw = os.environ.get(
        "OMNIASSIST_CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:5000,http://localhost:5000",
    )
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["http://127.0.0.1:5000", "http://localhost:5000"]


APP_SECRET_KEY = _get_or_generate_secret("OMNIASSIST_FLASK_SECRET_KEY")
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
runtime_events.set_emitter(lambda event, payload: socketio.emit(event, payload))

# Global state
controller: Optional["AssistantController"] = None
is_listening = False
pending_confirmation: Optional[Dict[str, Any]] = None
listening_thread: Optional[threading.Thread] = None
wake_word_detector: Optional["WakeWordDetector"] = None


def _emit_wake_word_state(state: Dict[str, Any]):
    """Broadcast wake-word lifecycle state to all connected clients."""
    try:
        socketio.emit('wake_word_status', state)
    except Exception as e:
        logger.debug(f"[WakeWord] Failed to emit wake_word_status: {e}")


def get_controller() -> "AssistantController":
    """Lazy init of the assistant controller.

    This avoids doing heavy LLM/tool initialization during API startup, which makes
    auth + health endpoints responsive immediately.
    """
    global controller
    if controller is None:
        logger.info("[API] Initializing AssistantController (lazy)...")
        from backend.core.assistant_controller import AssistantController
        controller = AssistantController()
    return controller

# Cache for recent commands to avoid duplicate processing
_command_cache = {}
_cache_timeout = 1.0  # 1 second cache for duplicate commands
_socket_users: Dict[str, Dict[str, Any]] = {}


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
        'pending_confirmation': pending_confirmation is not None,
        'confirmation_details': pending_confirmation if pending_confirmation else None
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
        
        # Don't duplicate LLM calls - let controller handle plan generation
        # Process the command (this handles plan generation internally)
        result = get_controller().process(command, language=language)

        # Step progress is emitted in real-time by MultiExecutor via runtime_events.
        
        # Check if confirmation is required
        if result.get('status') == 'confirmation_required':
            global pending_confirmation
            pending_confirmation = result
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
    global is_listening, listening_thread
    
    try:
        if is_listening:
            return jsonify({'message': 'Already listening', 'listening': True}), 200
        
        is_listening = True
        listening_thread = threading.Thread(
            target=voice_loop,
            kwargs={"one_shot": True, "trigger": "manual"},
            daemon=True,
        )
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
    global is_listening
    
    try:
        if not is_listening:
            return jsonify({'message': 'Not currently listening', 'listening': False}), 200
        
        is_listening = False
        
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
            from backend.voice_engine.wake_word_detector import WakeWordDetector
            wake_word_detector = WakeWordDetector(
                callback=on_wake_word_detected,
                on_state_change=_emit_wake_word_state,
            )
        
        if wake_word_detector.status_snapshot().get("active"):
            return jsonify({'message': 'Wake word detection already active', **wake_word_detector.status_snapshot()}), 200
        
        wake_word_detector.start()
        time.sleep(0.15)
        status = wake_word_detector.status_snapshot()

        if not status.get("active"):
            logger.error(f"[API] Wake word failed to activate: {status}")
            return jsonify({
                'error': 'Wake word detection failed to activate',
                **status,
            }), 500

        logger.info("[API] Wake word detection started")
        _emit_wake_word_state(status)
        
        return jsonify({'message': 'Wake word detection started', **status})
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
        if wake_word_detector is None or not wake_word_detector.status_snapshot().get("active"):
            return jsonify({'message': 'Wake word detection not active', 'active': False}), 200
        
        wake_word_detector.stop()
        logger.info("[API] Wake word detection stopped")
        status = wake_word_detector.status_snapshot()
        _emit_wake_word_state(status)
        
        return jsonify({'message': 'Wake word detection stopped', **status})
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
    
    status = {
        'active': False,
        'configured_active': False,
        'thread_alive': False,
        'paused': False,
        'wake_words': assistant_config.get('wake_word.words', ['otto']),
        'consecutive_errors': 0,
        'last_error': '',
    }

    if wake_word_detector is not None:
        status.update(wake_word_detector.status_snapshot())

    status['enabled_in_config'] = assistant_config.get('wake_word.enabled', False)
    return jsonify(status)


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
    global pending_confirmation
    
    data = request.json
    approved = data.get('approved', False)
    
    if pending_confirmation is None:
        return jsonify({'error': 'No pending confirmation'}), 400
    
    try:
        logger.info(f"[API] Action {'approved' if approved else 'rejected'}")
        result = get_controller().confirm_action(approved)
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
        from backend.voice_engine.audio_pipeline import speak
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

        # Update timezone
        if 'timezone' in data:
            try:
                timezone = str(data['timezone']).strip() or os.environ.get('OMNIASSIST_TIMEZONE', 'IST')
                success = assistant_config.set('assistant.timezone', timezone)
                if success:
                    updated.append(f"timezone={timezone}")
                    logger.info(f"[Settings] Timezone updated to: {timezone}")
                else:
                    errors.append("timezone: failed to save to config")
            except Exception as e:
                errors.append(f"timezone: {str(e)}")
                logger.error(f"[Settings] Error updating timezone: {e}", exc_info=True)

        # Update primary email used by assistant workflows
        if 'primary_email' in data:
            try:
                primary_email = str(data['primary_email']).strip()
                success = assistant_config.set('assistant.primary_email', primary_email)
                if success:
                    updated.append(f"primary_email={primary_email}")
                    logger.info(f"[Settings] Primary email updated to: {primary_email}")
                else:
                    errors.append("primary_email: failed to save to config")
            except Exception as e:
                errors.append(f"primary_email: {str(e)}")
                logger.error(f"[Settings] Error updating primary email: {e}", exc_info=True)
        
        # Note: assistant_config.set() already saves to disk, no need to call save()
        
        result = {
            'status': 'success' if not errors else 'partial' if updated else 'error',
            'updated': updated,
            'errors': errors,
            'message': f"Settings updated: {', '.join(updated)}" if updated else "No settings updated",
            'settings': {
                'persona': persona.mode,
                'language': assistant_config.get('stt.language', 'en'),
                'memory_enabled': assistant_config.get('memory.enabled', True),
                'timezone': assistant_config.get('assistant.timezone', os.environ.get('OMNIASSIST_TIMEZONE', 'IST')),
                'primary_email': assistant_config.get('assistant.primary_email', ''),
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
        'memory_enabled': assistant_config.get('memory.enabled', True),
        'timezone': assistant_config.get('assistant.timezone', os.environ.get('OMNIASSIST_TIMEZONE', 'IST')),
        'primary_email': assistant_config.get('assistant.primary_email', getattr(request.current_user, 'email', '')),
    })


@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    """Return user-facing personalization profile for desktop clients."""
    user = request.current_user

    timezone = assistant_config.get('assistant.timezone', os.environ.get('OMNIASSIST_TIMEZONE', 'IST'))
    primary_email = assistant_config.get('assistant.primary_email', user.email)

    smtp_connected = bool(
        os.environ.get('SMTP_HOST') and os.environ.get('SMTP_USER') and os.environ.get('SMTP_PASSWORD')
    )

    connected_apps = [
        {
            'name': 'Email',
            'status': 'connected' if smtp_connected else 'not_connected',
            'details': os.environ.get('SMTP_USER', ''),
        },
        {
            'name': 'Wake Word',
            'status': 'enabled' if bool(assistant_config.get('wake_word.enabled', False)) else 'disabled',
            'details': ', '.join(assistant_config.get('wake_word.words', ['otto'])),
        },
        {
            'name': 'Memory',
            'status': 'enabled' if bool(assistant_config.get('memory.enabled', True)) else 'disabled',
            'details': 'Assistant long-term memory',
        },
    ]

    return jsonify({
        'profile': {
            'id': user.id,
            'name': user.username,
            'email': user.email,
            'role': user.role,
        },
        'preferences': {
            'persona': persona.mode,
            'language': assistant_config.get('stt.language', 'en'),
            'memory_enabled': assistant_config.get('memory.enabled', True),
            'timezone': timezone,
            'primary_email': primary_email,
        },
        'memory': {
            'name': user.username,
            'timezone': timezone,
            'primary_email': primary_email,
        },
        'connected_apps': connected_apps,
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

    wake_active = False
    if wake_word_detector is not None:
        try:
            wake_active = bool(wake_word_detector.status_snapshot().get("active"))
        except Exception:
            wake_active = bool(wake_word_detector.is_active)

    _socket_users[request.sid] = socket_user
    logger.info(f"[WebSocket] Client connected: {socket_user['username']} ({request.sid})")
    emit('connection_status', {
        'status': 'connected',
        'listening': is_listening,
        'pending_confirmation': pending_confirmation is not None,
        'wake_word_active': wake_active
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
    if not isinstance(data, dict):
        emit('error', {'message': 'Invalid payload'})
        return

    command = data.get('command', '')
    language = data.get('language')

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
        logger.info(f"[WebSocket] Processing command: {command}")

        # Mirror REST behavior for exit commands
        normalized = str(command).lower().strip()
        if normalized in ["exit", "quit", "shutdown", "stop assistant", "goodbye", "close"]:
            logger.info(f"[WebSocket] Exit command received: {command}")
            socketio.emit('assistant_shutdown', {
                'message': 'Shutting down assistant. Goodbye!',
                'command': command
            })
            emit('command_result', {
                'status': 'shutdown',
                'message': 'Shutting down assistant. Goodbye!',
                'data': {}
            })
            return

        # Process the command (plan generation + execution)
        result = get_controller().process(command, language=language)

        # Step progress is emitted in real-time by MultiExecutor via runtime_events.
        
        # Check if confirmation is required
        if result.get('status') == 'confirmation_required':
            global pending_confirmation
            pending_confirmation = result
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

    ack_message = str(assistant_config.get('wake_word.acknowledgement', 'Yes?')).strip() or 'Yes?'
    
    # Start voice listening if not already active
    if not is_listening:
        # Let user know wake-word activation happened.
        socketio.emit('command_result', {
            'status': 'success',
            'message': ack_message,
        })
        try:
            from backend.voice_engine.audio_pipeline import speak
            speak(ack_message)
        except Exception as e:
            logger.warning(f"[WakeWord] Acknowledgement speak failed: {e}")

        is_listening = True
        listening_thread = threading.Thread(
            target=voice_loop,
            kwargs={"one_shot": True, "trigger": "wake_word"},
            daemon=True,
        )
        listening_thread.start()
        
        logger.info("[WakeWord] Voice listening started automatically")
        socketio.emit('listening_status', {'listening': True, 'triggered_by_wake_word': True})
    else:
        logger.debug("[WakeWord] Voice listening already active, ignoring detection")


# ============== VOICE LOOP (Background Thread) ==============

def voice_loop(one_shot: bool = True, trigger: str = "manual"):
    """
    Background voice listening loop
    Runs in a separate thread when listening is enabled
    Uses adaptive/proximity-based listening (stops on silence, not fixed duration)
    """
    global is_listening, pending_confirmation, wake_word_detector
    
    mode = "one-shot" if one_shot else "continuous"
    logger.info(f"[Voice Loop] Started (Adaptive mode - {mode}, trigger={trigger})")

    # Lazy-import voice pipeline so API startup isn't blocked by Whisper/Torch.
    from backend.voice_engine.audio_pipeline import listen_for_gui_adaptive, speak
    
    # Pause wake word detection during active listening
    if wake_word_detector and wake_word_detector.is_active:
        wake_word_detector.pause()
        logger.debug("[Voice Loop] Wake word detection paused during active listening")
    
    ctrl = get_controller()
    no_input_streak = 0

    while is_listening:
        try:
            # Listen for voice input (adaptive mode - stops on silence)
            text = listen_for_gui_adaptive(should_stop=lambda: not is_listening)

            # Stop can be requested while recorder was still collecting chunks.
            # Discard any text captured during shutdown to avoid one extra command execution.
            if not is_listening:
                logger.info("[Voice Loop] Stop requested - exiting before processing transcript")
                break
            
            if not text:
                no_input_streak += 1
                logger.debug(f"[Voice Loop] No speech detected (streak={no_input_streak})")

                # One-shot sessions should stop after silence to avoid infinite restart loops.
                if one_shot:
                    logger.info("[Voice Loop] One-shot session ended (no speech captured)")
                    is_listening = False
                    socketio.emit('command_result', {
                        'status': 'info',
                        'message': 'No speech detected. Please click mic and try again.'
                    })
                    break

                # Continuous mode: back off a bit to avoid tight retry loops and log spam.
                time.sleep(min(0.25 * no_input_streak, 1.0))
                continue

            # Reset silence streak once valid text is captured.
            no_input_streak = 0
            
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
            
            # Process the command via controller's agent loop
            result = ctrl.process(text)

            # Emit steps from the loop's executed plan (single source of truth)
                # Step progress is emitted in real-time by MultiExecutor via runtime_events.

            logger.info(f"[Voice Loop] Result: {result}")
            
            # Handle confirmation requirement
            if result.get('status') == 'confirmation_required':
                pending_confirmation = result
                socketio.emit('confirmation_required', result)
                # Don't speak yet, wait for user confirmation via UI
                if one_shot:
                    logger.info("[Voice Loop] One-shot session complete (confirmation required)")
                    is_listening = False
                    break
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

                if one_shot:
                    logger.info("[Voice Loop] One-shot session complete")
                    is_listening = False
                    break
                
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
    """Initialize wake-word detector at startup only when explicitly enabled."""
    global wake_word_detector

    try:
        config_enabled = bool(assistant_config.get('wake_word.enabled', False))
        config_autostart = bool(assistant_config.get('wake_word.autostart', False))

        env_override = os.environ.get("OMNIASSIST_WAKE_WORD_AUTOSTART")
        if env_override is None:
            autostart_enabled = config_enabled and config_autostart
        else:
            env_val = env_override.strip().lower()
            autostart_enabled = env_val in {"1", "true", "yes", "on"}

        if not autostart_enabled:
            logger.info('[WakeWord] Startup auto-enable is OFF')
            return

        if wake_word_detector is None:
            from backend.voice_engine.wake_word_detector import WakeWordDetector
            wake_word_detector = WakeWordDetector(
                callback=on_wake_word_detected,
                on_state_change=_emit_wake_word_state,
            )

        if not wake_word_detector.is_active:
            wake_word_detector.start()
            logger.info('[WakeWord] Startup auto-enable is ON. Detection started.')
        else:
            logger.info('[WakeWord] Detection already active at startup.')
    except Exception as e:
        logger.error(f"[WakeWord] Startup initialization error: {e}", exc_info=True)


def initialize_controller_warmup():
    """Warm up controller + LLM in background to reduce first-request latency."""
    try:
        if not bool(assistant_config.get('llm.warmup_on_startup', True)):
            logger.info('[Warmup] LLM startup warmup is OFF')
            return

        logger.info('[Warmup] Initializing controller and warming up LLM...')
        ctrl = get_controller()
        if hasattr(ctrl, 'llm_client') and hasattr(ctrl.llm_client, 'warm_up'):
            ctrl.llm_client.warm_up()
        logger.info('[Warmup] Startup warmup complete')
    except Exception as e:
        logger.warning(f"[Warmup] Startup warmup failed: {e}")


def run_api_service(host='0.0.0.0', port=5000, debug=False):
    """
    Run the API service
    
    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to listen on (default: 5000)
        debug: Enable debug mode (default: False)
    """
    # Initialize database and create default admin if needed.
    # Keep this synchronous so auth endpoints work immediately.
    initialize_database()

    # Wake-word startup can touch audio devices and occasionally blocks/hangs
    # on some systems/drivers. Run it in the background so the API can bind
    # and the desktop UI can connect even if wake-word init is slow.
    threading.Thread(target=initialize_wake_word, daemon=True).start()
    threading.Thread(target=initialize_controller_warmup, daemon=True).start()
    
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
    run_kwargs = {
        "host": host,
        "port": port,
        "debug": debug,
        "use_reloader": False,
    }

    # Compatibility: older Flask-SocketIO versions don't accept allow_unsafe_werkzeug.
    try:
        socketio.run(app, **run_kwargs, allow_unsafe_werkzeug=True)
    except TypeError:
        socketio.run(app, **run_kwargs)


if __name__ == '__main__':
    # Keep debug off for stable background voice/wake-word threads.
    run_api_service(debug=False)
