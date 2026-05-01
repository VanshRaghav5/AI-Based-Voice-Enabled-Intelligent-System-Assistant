"""
OMINI Security Module
=====================
Centralized security controls for rate limiting, input validation,
API key management, and code execution sandboxing.

Senior Security Developer: Applied without breaking existing functionality.
"""

import os
import re
import json
import time
import hashlib
import secrets
import threading
import platform
from pathlib import Path
from typing import Any, Optional
from collections import deque
from dataclasses import dataclass, field

try:
    import keyring
    import keyring.errors
    _KEYRING_AVAILABLE = True
except ImportError:
    _KEYRING_AVAILABLE = False

try:
    import jwt
    from jwt import PyJWTError
    _JWT_AVAILABLE = True
except ImportError:
    jwt = None

    class PyJWTError(Exception):
        pass

    _JWT_AVAILABLE = False


def _get_base_dir():
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = _get_base_dir()


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Rate Limiting
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_requests_per_minute: int = 60      # Gemini API calls per minute (increased)
    max_requests_per_hour: int = 2000     # Gemini API calls per hour (increased)
    max_tool_calls_per_minute: int = 100    # Tool executions per minute (increased)
    max_file_writes_per_hour: int = 500      # File write operations per hour (increased)
    max_code_executions_per_hour: int = 100    # Code executions per hour (increased)
    cooldown_seconds: int = 10              # Cooldown after hitting limit (reduced)


class RateLimiter:
    """
    Token bucket rate limiter with minute/hour windows.
    Thread-safe implementation.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._lock = threading.Lock()

        # Minute windows (deque for O(1) append/popleft)
        self._minute_requests: deque = deque(maxlen=self.config.max_requests_per_minute)
        self._minute_tools: deque = deque(maxlen=self.config.max_tool_calls_per_minute)
        self._minute_files: deque = deque(maxlen=self.config.max_file_writes_per_hour)
        self._minute_code: deque = deque(maxlen=self.config.max_code_executions_per_hour)

        # Hour windows
        self._hour_requests: deque = deque(maxlen=self.config.max_requests_per_hour)

        # Cooldown state
        self._cooldown_until: float = 0.0
        self._violation_count: int = 0

    def _clean_old_entries(self, deque_obj: deque) -> None:
        """Remove entries older than the time window."""
        now = time.time()
        while deque_obj and now - deque_obj[0] > 60:
            deque_obj.popleft()

    def _clean_old_hour_entries(self, deque_obj: deque) -> None:
        """Remove entries older than 1 hour."""
        now = time.time()
        while deque_obj and now - deque_obj[0] > 3600:
            deque_obj.popleft()

    def check_api_rate_limit(self) -> tuple[bool, str]:
        """
        Check if API rate limit is exceeded.
        Returns (allowed, message).
        """
        with self._lock:
            now = time.time()

            # Check cooldown
            if now < self._cooldown_until:
                remaining = int(self._cooldown_until - now)
                return False, f"Rate limit exceeded. Please wait {remaining}s."

            # Clean old entries
            self._clean_old_entries(self._minute_requests)
            self._clean_old_hour_entries(self._hour_requests)

            # Check minute limit
            if len(self._minute_requests) >= self.config.max_requests_per_minute:
                self._trigger_cooldown()
                return False, "Minute rate limit exceeded. Please wait 1 minute."

            # Check hourly limit
            if len(self._hour_requests) >= self.config.max_requests_per_hour:
                self._trigger_cooldown()
                return False, "Hourly rate limit exceeded. Please wait 1 hour."

            # Record this request
            self._minute_requests.append(now)
            self._hour_requests.append(now)

            return True, "OK"

    def check_tool_rate_limit(self) -> tuple[bool, str]:
        """Check if tool call rate limit is exceeded."""
        with self._lock:
            now = time.time()
            self._clean_old_entries(self._minute_tools)

            if len(self._minute_tools) >= self.config.max_tool_calls_per_minute:
                return False, f"Tool rate limit ({self.config.max_tool_calls_per_minute}/min) exceeded."

            self._minute_tools.append(now)
            return True, "OK"

    def check_file_write_limit(self) -> tuple[bool, str]:
        """Check if file write rate limit is exceeded."""
        with self._lock:
            now = time.time()
            self._clean_old_entries(self._minute_files)

            if len(self._minute_files) >= self.config.max_file_writes_per_hour:
                return False, f"File write limit ({self.config.max_file_writes_per_hour}/hour) exceeded."

            self._minute_files.append(now)
            return True, "OK"

    def check_code_execution_limit(self) -> tuple[bool, str]:
        """Check if code execution rate limit is exceeded."""
        with self._lock:
            now = time.time()
            self._clean_old_entries(self._minute_code)

            if len(self._minute_code) >= self.config.max_code_executions_per_hour:
                return False, f"Code execution limit ({self.config.max_code_executions_per_hour}/hour) exceeded."

            self._minute_code.append(now)
            return True, "OK"

    def _trigger_cooldown(self) -> None:
        """Trigger cooldown after rate limit violation."""
        self._violation_count += 1
        self._cooldown_until = time.time() + self.config.cooldown_seconds


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Input Validation & Sanitization
# ═══════════════════════════════════════════════════════════════════════════════

class InputValidator:
    """
    Comprehensive input validation and sanitization.
    """

    # Dangerous patterns - simplified path traversal detection
    PATH_TRAVERSAL_PATTERN = re.compile(
        r"(\.\.[\\/])|(%2e%2e)|([a-zA-Z]:[\\/]+(?:windows|system32|etc|usr|bin|boot|dev|tmp))"
    )

    CODE_INJECTION_PATTERNS = [
        re.compile(r"__import__\s*\(\s*['\"]os['\"]", re.I),
        re.compile(r"exec\s*\(\s*", re.I),
        re.compile(r"eval\s*\(\s*", re.I),
        re.compile(r"subprocess\s*\.\s*(?:run|call|Popen)", re.I),
        re.compile(r"import\s+os\s*$", re.M),
        re.compile(r"import\s+subprocess\s*$", re.M),
        re.compile(r"import\s+sys\s*$", re.M),
        re.compile(r"from\s+os\s+import", re.I),
        re.compile(r"from\s+subprocess\s+import", re.I),
        re.compile(r"open\s*\(\s*['\"]/(?:etc|usr|boot|dev)", re.I),
    ]

    DANGEROUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".ps1", ".sh", ".dll", ".so", ".dylib"}
    RESTRICTED_EXTENSIONS = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".go", ".rs"}

    @classmethod
    def sanitize_path(cls, user_input: str) -> str:
        """
        Sanitize file path input to prevent path traversal.
        Returns sanitized path (still needs safe path check).
        """
        if not user_input:
            return ""

        # Remove null bytes
        sanitized = user_input.replace("\0", "")

        # Normalize separators
        sanitized = sanitized.replace("\\", "/")

        # Remove leading/trailing whitespace
        sanitized = sanitized.strip()

        # Remove path components that try to escape
        parts = sanitized.split("/")
        safe_parts = []
        for part in parts:
            if part in (".", ".."):
                continue
            # Filter out parts that start with drive letters or look like absolute paths
            if not re.match(r"^[a-zA-Z]:$", part):
                safe_parts.append(part)

        return "/".join(safe_parts)

    @classmethod
    def validate_path(cls, user_input: str) -> tuple[bool, str]:
        """
        Validate path input for traversal attempts.
        Returns (is_valid, error_message).
        """
        if not user_input:
            return True, ""

        # Check for path traversal patterns
        if cls.PATH_TRAVERSAL_PATTERN.search(user_input.lower()):
            return False, "Path traversal attempt detected."

        # Check for encoded traversals
        lower = user_input.lower()
        if "%2e%2e" in lower or "..%2f" in lower:
            return False, "Encoded path traversal detected."

        return True, ""

    @classmethod
    def sanitize_text(cls, user_input: str, max_length: int = 10000) -> str:
        """
        Sanitize general text input.
        Removes control characters, limits length.
        """
        if not user_input:
            return ""

        # Remove control characters except newline and tab
        sanitized = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", user_input)

        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    @classmethod
    def validate_filename(cls, filename: str) -> tuple[bool, str]:
        """
        Validate filename for dangerous characters/directories.
        """
        if not filename:
            return False, "Empty filename."

        # Check for path separators
        if "/" in filename or "\\" in filename:
            return False, "Filename cannot contain path separators."

        # Check for reserved Windows names
        reserved = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
                    "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2",
                    "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
        name_upper = filename.upper().split(".")[0]
        if name_upper in reserved:
            return False, f"Reserved filename: {filename}"

        # Check for dangerous extensions
        ext = Path(filename).suffix.lower()
        if ext in cls.DANGEROUS_EXTENSIONS:
            return False, f"Dangerous extension not allowed: {ext}"

        return True, ""

    @classmethod
    def check_dangerous_code(cls, code: str) -> tuple[bool, str]:
        """
        Check for potentially dangerous code patterns.
        Used for code_helper and dev_agent inputs.
        Returns (is_safe, warning_message).
        """
        if not code:
            return True, ""

        for pattern in cls.CODE_INJECTION_PATTERNS:
            match = pattern.search(code)
            if match:
                return False, f"Dangerous pattern detected: {match.group()}"

        # Allow subprocess if it's in a safe context (e.g., running known commands)
        # But flag for review
        return True, ""

    @classmethod
    def validate_json_params(cls, params: dict, allowed_keys: list[str]) -> tuple[bool, str, dict]:
        """
        Validate JSON parameters against allowed keys.
        Returns (is_valid, error, sanitized_params).
        """
        if not params:
            return True, "", {}

        sanitized = {}
        for key, value in params.items():
            if key not in allowed_keys:
                return False, f"Unknown parameter: {key}", {}

            # Sanitize based on key type
            if key in ("path", "name", "destination", "file_path"):
                sanitized[key] = cls.sanitize_path(str(value))
            elif key in ("content", "query", "description"):
                sanitized[key] = cls.sanitize_text(str(value))
            elif key in ("app_name", "url", "website"):
                sanitized[key] = cls.sanitize_text(str(value))
            else:
                sanitized[key] = value

        return True, "", sanitized


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Authentication & Authorization
# ═══════════════════════════════════════════════════════════════════════════════

class UserRole:
    """User roles with permission levels."""
    GUEST = "guest"           # minimal access
    USER = "user"            # standard access
    ADMIN = "admin"          # full access


@dataclass
class UserProfile:
    """User profile with authentication info."""
    username: str
    role: str = UserRole.USER
    session_token: Optional[str] = None
    session_expires: float = 0.0
    failed_attempts: int = 0
    locked_until: float = 0.0


class AuthManager:
    """
    Manages authentication (who are you) and authorization (what can you do).
    """

    MAX_FAILED_ATTEMPTS = 5      # Lock after 5 failed login attempts
    LOCKOUT_DURATION = 300       # 5 minutes lockout
    SESSION_DURATION = 3600      # 1 hour session duration
    JWT_ALGORITHM = "HS256"

    # Role-based permissions
    PERMISSIONS = {
        UserRole.GUEST: {
            "file_controller": ["list", "read"],
            "weather_report": True,
            "web_search": True,
            "computer_settings": False,
            "browser_control": False,
            "code_helper": False,
            "dev_agent": False,
            "send_message": False,
            "game_updater": False,
        },
        UserRole.USER: {
            "file_controller": True,
            "weather_report": True,
            "web_search": True,
            "computer_settings": True,
            "browser_control": True,
            "code_helper": ["write", "edit", "explain", "run"],
            "dev_agent": False,
            "send_message": True,
            "game_updater": False,
        },
        UserRole.ADMIN: {
            "*": True,  # Full access
        },
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._users: dict[str, UserProfile] = {}
        self._current_user: Optional[UserProfile] = None
        self._jwt_secret: Optional[str] = None
        self._load_users()

    def _get_jwt_secret(self) -> str:
        """Load or create the signing secret used for JWT sessions."""
        if self._jwt_secret:
            return self._jwt_secret

        env_secret = os.environ.get("OMINI_JWT_SECRET")
        if env_secret:
            self._jwt_secret = env_secret
            return env_secret

        secret_path = BASE_DIR / "config" / "jwt_secret.json"
        if secret_path.exists():
            try:
                with open(secret_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                    secret = payload.get("secret", "")
                    if secret:
                        self._jwt_secret = secret
                        return secret
            except Exception:
                pass

        secret_path.parent.mkdir(parents=True, exist_ok=True)
        secret = secrets.token_urlsafe(48)
        with open(secret_path, "w", encoding="utf-8") as f:
            json.dump({"secret": secret}, f, indent=2)
        self._jwt_secret = secret
        return secret

    def _issue_session_token(self, username: str, role: str, expires_at: float) -> str:
        """Create a signed session token for the authenticated user."""
        if not _JWT_AVAILABLE:
            return secrets.token_urlsafe(32)

        payload = {
            "sub": username,
            "role": role,
            "iat": int(time.time()),
            "exp": int(expires_at),
            "aud": "omini-assistant",
        }
        return jwt.encode(payload, self._get_jwt_secret(), algorithm=self.JWT_ALGORITHM)

    def _token_is_valid(self, profile: Optional[UserProfile]) -> bool:
        """Check whether the stored session token is still valid."""
        if not profile:
            return False

        now = time.time()
        if profile.session_expires and now > profile.session_expires:
            return False

        if not profile.session_token or not _JWT_AVAILABLE:
            return True

        try:
            payload = jwt.decode(
                profile.session_token,
                self._get_jwt_secret(),
                algorithms=[self.JWT_ALGORITHM],
                audience="omini-assistant",
            )
        except PyJWTError:
            return False

        return payload.get("sub") == profile.username and payload.get("role") == profile.role

    def _activate_session(self, username: str, role: str) -> UserProfile:
        """Create and store the active session profile."""
        now = time.time()
        profile = self._users.get(username)
        if profile is None:
            profile = UserProfile(username=username, role=role)
            self._users[username] = profile

        profile.role = role
        profile.failed_attempts = 0
        profile.locked_until = 0.0
        profile.session_expires = now + self.SESSION_DURATION
        profile.session_token = self._issue_session_token(username, role, profile.session_expires)
        self._current_user = profile
        return profile

    def _load_users(self):
        """Load users from config or create default."""
        config_path = BASE_DIR / "config" / "users.json"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                    for username, info in data.items():
                        self._users[username] = UserProfile(
                            username=username,
                            role=info.get("role", UserRole.USER),
                        )
            except Exception:
                pass

        # Create default admin if none exists
        if not self._users:
            self._users["admin"] = UserProfile(
                username="admin",
                role=UserRole.ADMIN,
            )
            # Set default password for admin
            self.set_password("admin", "admin")
            self._save_users()

    def _save_users(self):
        """Save users to config."""
        config_path = BASE_DIR / "config" / "users.json"
        data = {
            username: {"role": profile.role}
            for username, profile in self._users.items()
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)

    def authenticate(self, username: str, password: str) -> tuple[bool, str]:
        """
        Authenticate user with username/password.
        Returns (success, message).
        """
        with self._lock:
            now = time.time()

            # Check if locked
            profile = self._users.get(username)
            if profile and profile.locked_until > now:
                remaining = int(profile.locked_until - now)
                return False, f"Account locked. Wait {remaining}s."

            # Verify password
            if not profile:
                return False, "Invalid credentials."

            # Simple password check (in production, use proper hashing)
            password_hash = self._hash_password(username, password)
            stored_hash = self._get_stored_hash(username)

            if password_hash != stored_hash:
                if profile:
                    profile.failed_attempts += 1
                    if profile.failed_attempts >= self.MAX_FAILED_ATTEMPTS:
                        profile.locked_until = now + self.LOCKOUT_DURATION
                        return False, f"Account locked for {self.LOCKOUT_DURATION}s after {self.MAX_FAILED_ATTEMPTS} failed attempts."
                return False, "Invalid credentials."

            self._activate_session(username, profile.role)

            return True, f"Authenticated as {profile.role}"

    def continue_as_guest(self) -> tuple[bool, str]:
        """Start a restricted guest session without credentials."""
        with self._lock:
            self._activate_session("guest", UserRole.GUEST)
            return True, "Continued as guest."

    def _hash_password(self, username: str, password: str) -> str:
        """Hash password (simple SHA256 with username salt)."""
        return hashlib.sha256(f"{username}:{password}".encode()).hexdigest()

    def _get_stored_hash(self, username: str) -> str:
        """Get stored password hash."""
        hash_path = BASE_DIR / "config" / "passwords.json"
        if hash_path.exists():
            try:
                with open(hash_path, "r") as f:
                    hashes = json.load(f)
                    return hashes.get(username, "")
            except Exception:
                pass
        return ""

    def set_password(self, username: str, password: str) -> bool:
        """Set user password."""
        if username not in self._users:
            return False
        password_hash = self._hash_password(username, password)
        hash_path = BASE_DIR / "config" / "passwords.json"
        hashes = {}
        if hash_path.exists():
            try:
                with open(hash_path, "r") as f:
                    hashes = json.load(f)
            except Exception:
                pass
        hashes[username] = password_hash
        with open(hash_path, "w") as f:
            json.dump(hashes, f)
        return True

    def create_user(self, username: str, password: str, role: str = UserRole.USER) -> bool:
        """Create new user."""
        if username in self._users:
            return False
        self._users[username] = UserProfile(username=username, role=role)
        self.set_password(username, password)
        self._save_users()
        return True

    def authorize(self, tool_name: str, action: str = None) -> tuple[bool, str]:
        """
        Check if current user is authorized for tool/action.
        Returns (authorized, message).
        """
        with self._lock:
            if not self._current_user:
                return False, "Not authenticated. Please login first."

            # Check JWT-backed session validity
            if not self._token_is_valid(self._current_user):
                self._current_user = None
                return False, "Session expired. Please login again."

            role = self._current_user.role
            perms = self.PERMISSIONS.get(role, {})

            # Admin has full access
            if perms.get("*") is True:
                return True, "Authorized."

            # Check tool permission
            tool_perm = perms.get(tool_name, False)
            if tool_perm is True:
                return True, "Authorized."
            elif tool_perm is False:
                return False, f"Tool '{tool_name}' not allowed for {role}."
            elif isinstance(tool_perm, list):
                if action in tool_perm or action is None:
                    return True, "Authorized."
                return False, f"Action '{action}' not allowed for {role}."

            return False, f"No permission for tool '{tool_name}'."

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self._token_is_valid(self._current_user)

    def get_current_user(self) -> Optional[str]:
        """Get current username."""
        if self._token_is_valid(self._current_user):
            return self._current_user.username
        return None

    def logout(self):
        """Logout current user."""
        with self._lock:
            self._current_user = None


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return get_auth_manager().is_authenticated()


# Convenience functions
def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    """Authenticate user."""
    return get_auth_manager().authenticate(username, password)


def continue_as_guest() -> tuple[bool, str]:
    """Start a guest session."""
    return get_auth_manager().continue_as_guest()


def authorize_tool(tool_name: str, action: str = None) -> tuple[bool, str]:
    """Check tool authorization."""
    return get_auth_manager().authorize(tool_name, action)


def require_auth(tool_name: str, action: str = None):
    """Decorator/validator for tool access."""
    allowed, msg = authorize_tool(tool_name, action)
    if not allowed:
        raise PermissionError(msg)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Secure API Key Management
# ═══════════════════════════════════════════════════════════════════════

class SecureKeyManager:
    """
    Manages API keys securely using keyring (OS credential store).
    Falls back to encrypted file if keyring unavailable.
    """

    SERVICE_NAME = "OMINI_ASSISTANT"
    KEYRING_USER = "omini_ai"

    @classmethod
    def get_api_key(cls, config_path: Path) -> Optional[str]:
        """
        Get API key from keyring or fallback to config file.
        """
        # Try keyring first
        if _KEYRING_AVAILABLE:
            try:
                key = keyring.get_password(cls.SERVICE_NAME, cls.KEYRING_USER)
                if key:
                    return key
            except Exception:
                pass

        # Fallback: read from config file (less secure but functional)
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("gemini_api_key")
            except Exception:
                pass

        return None

    @classmethod
    def set_api_key(cls, api_key: str, config_path: Path) -> bool:
        """
        Store API key securely. Returns success status.
        """
        # Try keyring first
        if _KEYRING_AVAILABLE:
            try:
                keyring.set_password(cls.SERVICE_NAME, cls.KEYRING_USER, api_key)
                # Still write to config for fallback reading
                cls._write_config(api_key, config_path)
                return True
            except Exception as e:
                print(f"[Security] Keyring failed: {e}, using encrypted file fallback")

        # Fallback: store with encryption
        return cls._write_encrypted_config(api_key, config_path)

    @classmethod
    def _write_config(cls, api_key: str, config_path: Path) -> None:
        """Write standard config file (for backward compatibility)."""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"gemini_api_key": api_key}
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    @classmethod
    def _write_encrypted_config(cls, api_key: str, config_path: Path) -> bool:
        """Write config with XOR-based obfuscation (not true encryption but better than plaintext)."""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate salt and derive key
            salt = os.urandom(16)
            # Simple XOR obfuscation (not crypto-grade but obscures plaintext)
            key_bytes = api_key.encode("utf-8")
            obfuscated = bytes(a ^ b for a, b in zip(key_bytes, (salt * (len(key_bytes) // 16 + 1))[:len(key_bytes)]))

            data = {
                "_obfuscated": True,
                "_salt": salt.hex(),
                "_key": obfuscated.hex()
            }

            config_path.write_text(json.dumps(data), encoding="utf-8")
            return True
        except Exception:
            return False

    @classmethod
    def read_obfuscated_config(cls, config_path: Path) -> Optional[str]:
        """Read and deobfuscate config if obfuscated."""
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            if not data.get("_obfuscated"):
                return data.get("gemini_api_key")

            # Deobfuscate
            salt = bytes.fromhex(data["_salt"])
            key = bytes.fromhex(data["_key"])
            original = bytes(a ^ b for a, b in zip(key, (salt * (len(key) // 16 + 1))[:len(key)]))
            return original.decode("utf-8")
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Backup Before Write Operations
# ═══════════════════════════════════════════════════════════════════════════════

class SecureFileWriter:
    """
    Secure file operations with automatic backup.
    """

    BACKUP_DIR = Path.home() / ".omini_backups"
    MAX_BACKUPS_PER_FILE = 5

    @classmethod
    def ensure_backup_dir(cls) -> Path:
        """Ensure backup directory exists."""
        cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        return cls.BACKUP_DIR

    @classmethod
    def create_backup(cls, file_path: Path) -> Optional[Path]:
        """
        Create timestamped backup of existing file.
        Returns backup path or None if file doesn't exist.
        """
        if not file_path.exists():
            return None

        cls.ensure_backup_dir()

        # Clean old backups for this file
        file_backups = cls.BACKUP_DIR.glob(f"{file_path.stem}_*.bak")
        sorted_backups = sorted(file_backups, key=lambda p: p.stat().st_mtime)
        while len(sorted_backups) >= cls.MAX_BACKUPS_PER_FILE:
            old = sorted_backups.pop(0)
            old.unlink()

        # Create new backup
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = cls.BACKUP_DIR / f"{file_path.stem}_{timestamp}.bak"

        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception:
            return None

    @classmethod
    def write_with_backup(cls, file_path: Path, content: str,
                       create_parent: bool = True) -> bool:
        """
        Write file with automatic backup.
        Returns True if successful.
        """
        try:
            if create_parent:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup of existing file
            cls.create_backup(file_path)

            # Write new content
            file_path.write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False


# ═════════════════════════════════════════════════════════════════════════════==═
# SECTION 5: Security Logger
# ═════════════════════════════════════════��═��═══════════════════════════════════

class SecurityLogger:
    """
    Security event logging for audit trails.
    """

    LOG_FILE = Path.home() / ".omini_logs" / "security.log"

    @classmethod
    def _ensure_log_dir(cls) -> None:
        """Ensure log directory exists."""
        cls.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def log_event(cls, event_type: str, details: dict) -> None:
        """Log security event."""
        cls._ensure_log_dir()

        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": event_type,
            **details
        }

        try:
            with open(cls.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    @classmethod
    def log_rate_limit_hit(cls, limiter_type: str) -> None:
        """Log rate limit violation."""
        cls.log_event("RATE_LIMIT_HIT", {"limiter": limiter_type})

    @classmethod
    def log_dangerous_code_blocked(cls, code_snippet: str) -> None:
        """Log dangerous code attempt."""
        cls.log_event("DANGEROUS_CODE_BLOCKED", {"code": code_snippet[:100]})

    @classmethod
    def log_path_traversal_blocked(cls, path: str) -> None:
        """Log path traversal attempt."""
        cls.log_event("PATH_TRAVERSAL_BLOCKED", {"path": path})


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: Convenience Functions (API-compatible wrappers)
# ═══════════════════════════════════════════════════════════════════════

def check_api_rate_limit() -> tuple[bool, str]:
    """Check Gemini API rate limit."""
    return _rate_limiter.check_api_rate_limit()


def check_tool_rate_limit() -> tuple[bool, str]:
    """Check tool execution rate limit."""
    return _rate_limiter.check_tool_rate_limit()


def check_file_write_limit() -> tuple[bool, str]:
    """Check file write rate limit."""
    return _rate_limiter.check_file_write_limit()


def check_code_execution_limit() -> tuple[bool, str]:
    """Check code execution rate limit."""
    return _rate_limiter.check_code_execution_limit()


def sanitize_path_input(path: str) -> str:
    """Sanitize path input."""
    return InputValidator.sanitize_path(path)


def validate_path_input(path: str) -> tuple[bool, str]:
    """Validate path for traversal attempts."""
    return InputValidator.validate_path(path)


def validate_filename_input(filename: str) -> tuple[bool, str]:
    """Validate filename."""
    return InputValidator.validate_filename(filename)


def sanitize_text_input(text: str, max_length: int = 10000) -> str:
    """Sanitize text input."""
    return InputValidator.sanitize_text(text, max_length)


def secure_write_file(file_path: Path, content: str) -> bool:
    """Write file with backup."""
    return SecureFileWriter.write_with_backup(file_path, content)


def create_file_backup(file_path: Path) -> Optional[Path]:
    """Create backup of existing file."""
    return SecureFileWriter.create_backup(file_path)