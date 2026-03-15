import requests
from typing import Optional, Dict, Any, Tuple
import os
import json

BASE_URL = "http://127.0.0.1:5000"

# Token storage
TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".omniassist", "token.json")
_current_token: Optional[str] = None
_current_user: Optional[Dict[str, Any]] = None


def _ensure_token_dir():
    """Ensure token directory exists."""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)


def save_token(token: str, user: Dict[str, Any]):
    """Save authentication token and user info."""
    global _current_token, _current_user
    _current_token = token
    _current_user = user
    
    _ensure_token_dir()
    with open(TOKEN_FILE, 'w') as f:
        json.dump({
            'token': token,
            'user': user
        }, f)


def load_token() -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Load authentication token and user info."""
    global _current_token, _current_user
    
    if _current_token:
        return _current_token, _current_user
    
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                _current_token = data.get('token')
                _current_user = data.get('user')
                return _current_token, _current_user
        except Exception:
            pass
    
    return None, None


def clear_token():
    """Clear authentication token."""
    global _current_token, _current_user
    _current_token = None
    _current_user = None
    
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)


def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers with JWT token."""
    token, _ = load_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def login(username: str, password: str) -> Tuple[bool, str, Optional[str], Optional[Dict]]:
    """
    Login and receive JWT token.
    
    Returns:
        (success, message, token, user)
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        
        data = response.json()
        
        if response.status_code == 200 and data.get('status') == 'success':
            token = data.get('token')
            user = data.get('user')
            save_token(token, user)
            return True, data.get('message', 'Login successful'), token, user
        else:
            return False, data.get('message', 'Login failed'), None, None
            
    except Exception as e:
        return False, f"Connection error: {str(e)}", None, None


def logout() -> Tuple[bool, str]:
    """
    Logout and revoke token.
    
    Returns:
        (success, message)
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers=get_auth_headers(),
            timeout=5
        )
        
        clear_token()
        
        if response.status_code == 200:
            return True, "Logged out successfully"
        else:
            return True, "Logged out locally"  # Clear token anyway
            
    except Exception:
        clear_token()
        return True, "Logged out locally"


def register(username: str, email: str, password: str) -> Tuple[bool, str]:
    """
    Register a new user.
    
    Returns:
        (success, message)
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password
            },
            timeout=10
        )
        
        data = response.json()
        
        if response.status_code == 201 and data.get('status') == 'success':
            return True, data.get('message', 'Registration successful')
        else:
            message = data.get('message', 'Registration failed')
            if 'errors' in data:
                # Include validation errors
                errors = data['errors']
                if isinstance(errors, dict):
                    error_msgs = []
                    for field, msgs in errors.items():
                        if isinstance(msgs, list):
                            error_msgs.extend(msgs)
                        else:
                            error_msgs.append(str(msgs))
                    message += ": " + ", ".join(error_msgs)
            return False, message
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def verify_token() -> Tuple[bool, Optional[Dict]]:
    """
    Verify if current token is valid.
    
    Returns:
        (valid, user_info)
    """
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/verify",
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data.get('user')
        else:
            clear_token()
            return False, None
            
    except Exception:
        return False, None


def process_command(command: str, language: Optional[str] = None):
    """Process a command with extended timeout for LLM operations."""
    payload = {"command": command}
    if language:
        payload["language"] = language

    return requests.post(
        f"{BASE_URL}/api/process_command",
        json=payload,
        headers=get_auth_headers(),
        timeout=120  # 2 minutes for LLM + confirmation workflows
    )

def start_listening():
    """Start voice listening mode. Returns True on success, False on failure."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/start_listening",
            headers=get_auth_headers(),
            timeout=5
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error starting voice listening: {e}")
        return False

def stop_listening():
    """Stop voice listening mode. Returns True on success, False on failure."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/stop_listening",
            headers=get_auth_headers(),
            timeout=5
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error stopping voice listening: {e}")
        return False

def send_confirmation(approved: bool):
    return requests.post(
        f"{BASE_URL}/api/confirm",
        json={"approved": approved},
        headers=get_auth_headers(),
        timeout=10
    )

def start_wake_word():
    """Start wake word detection. Returns True on success, False on failure."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/wake_word/start",
            headers=get_auth_headers(),
            timeout=5
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error starting wake word detection: {e}")
        return False

def stop_wake_word():
    """Stop wake word detection. Returns True on success, False on failure."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/wake_word/stop",
            headers=get_auth_headers(),
            timeout=5
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error stopping wake word detection: {e}")
        return False

def get_wake_word_status():
    """Get wake word detection status."""
    try:
        response = requests.get(
            f"{BASE_URL}/api/wake_word/status",
            headers=get_auth_headers(),
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting wake word status: {e}")
        return None

def update_settings(settings: dict):
    """Update backend settings (persona, language, memory)."""
    return requests.post(
        f"{BASE_URL}/api/settings",
        json=settings,
        headers=get_auth_headers(),
        timeout=10
    )

def get_settings():
    """Get current backend settings."""
    return requests.get(
        f"{BASE_URL}/api/settings",
        headers=get_auth_headers(),
        timeout=5
    )


def request_password_reset(email: str) -> Tuple[bool, str]:
    """
    Request a password reset email.

    Returns:
        (success, message)
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/password-reset/request",
            json={"email": email},
            timeout=15
        )
        data = response.json()
        if response.status_code == 200:
            return True, data.get("message", "Reset email sent.")
        return False, data.get("message", "Failed to send reset email.")
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def confirm_password_reset(token: str, new_password: str) -> Tuple[bool, str]:
    """
    Confirm a password reset with a one-time token and new password.

    Returns:
        (success, message)
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/password-reset/confirm",
            json={"token": token, "new_password": new_password},
            timeout=15
        )
        data = response.json()
        if response.status_code == 200:
            return True, data.get("message", "Password reset successful.")
        message = data.get("message", "Password reset failed.")
        if "errors" in data:
            errors = data["errors"]
            if isinstance(errors, dict):
                msgs = []
                for field, v in errors.items():
                    msgs.extend(v if isinstance(v, list) else [str(v)])
                message += ": " + ", ".join(msgs)
        return False, message
    except Exception as e:
        return False, f"Connection error: {str(e)}"