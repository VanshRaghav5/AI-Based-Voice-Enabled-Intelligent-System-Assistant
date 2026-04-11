"""Authentication service with password hashing and JWT token management."""

import bcrypt
import jwt
import hashlib
import secrets
import os
import smtplib
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from email.message import EmailMessage
from backend.models.models import User, Session as SessionModel, PasswordResetToken
from backend.utils.logger import logger


# JWT Configuration
@lru_cache(maxsize=1)
def _get_jwt_secret_key() -> str:
    """Read the JWT secret key from environment.

    Note: this is intentionally *lazy* to avoid import-time crashes.
    """
    secret_key = os.environ.get("OMNIASSIST_JWT_SECRET", "").strip()
    if not secret_key:
        # Dev-friendly fallback: generate an ephemeral secret so the backend can start.
        # Tokens will be invalid after restart; set OMNIASSIST_JWT_SECRET for persistence.
        secret_key = secrets.token_urlsafe(64)
        os.environ["OMNIASSIST_JWT_SECRET"] = secret_key
        logger.warning(
            "[Auth] OMNIASSIST_JWT_SECRET is not set; using an ephemeral generated secret. "
            "Set OMNIASSIST_JWT_SECRET (or create a .env) to keep sessions valid across restarts."
        )
    return secret_key

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
PASSWORD_RESET_EXPIRE_MINUTES = 30


class PasswordHasher:
    """Password hashing utilities using bcrypt."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )


class AuthService:
    """Authentication service for user management and JWT tokens."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user"
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Create a new user.
        
        Returns:
            (success, message, user_object)
        """
        # Check if username exists
        existing_user = self.db.query(User).filter(User.username == username).first()
        if existing_user:
            return False, "Username already exists", None
        
        # Check if email exists
        existing_email = self.db.query(User).filter(User.email == email).first()
        if existing_email:
            return False, "Email already exists", None
        
        # Hash password
        hashed_password = PasswordHasher.hash_password(password)
        
        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return True, "User created successfully", user
        except Exception as e:
            self.db.rollback()
            return False, f"Error creating user: {str(e)}", None
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate a user with username and password.
        
        Returns:
            (success, message, user_object)
        """
        # Find user
        user = self.db.query(User).filter(User.username == username).first()
        
        if not user:
            return False, "Invalid username or password", None
        
        if not user.is_active:
            return False, "Account is disabled", None
        
        # Verify password
        if not PasswordHasher.verify_password(password, user.hashed_password):
            return False, "Invalid username or password", None
        
        # Extract user info before closing session (to avoid detached object errors)
        user_id = user.id
        user_username = user.username
        user_email = user.email
        user_role = user.role
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Return fresh user object with updated data
        user.id = user_id
        user.username = user_username
        user.email = user_email
        user.role = user_role
        
        return True, "Login successful", user
    
    def create_token(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, datetime]:
        """
        Create a JWT token for a user.
        
        Returns:
            (token, expiration_datetime)
        """
        # Set expiration time
        expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Create JWT payload
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "exp": expires_at,
            "iat": datetime.utcnow()
        }
        
        # Generate token
        token = jwt.encode(payload, _get_jwt_secret_key(), algorithm=ALGORITHM)
        
        # Store session in database
        session = SessionModel(
            user_id=user.id,
            token=token,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            is_valid=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(session)
        self.db.commit()
        
        return token, expires_at
    
    def verify_token(self, token: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Verify a JWT token.
        
        Returns:
            (valid, message, payload)
        """
        try:
            # Decode token
            payload = jwt.decode(token, _get_jwt_secret_key(), algorithms=[ALGORITHM])
            
            # Check if session exists and is valid
            session = self.db.query(SessionModel).filter(
                SessionModel.token == token,
                SessionModel.is_valid == True
            ).first()
            
            if not session:
                return False, "Invalid or revoked token", None
            
            # Check if token is expired
            if session.expires_at < datetime.utcnow():
                session.is_valid = False
                self.db.commit()
                return False, "Token expired", None
            
            return True, "Token valid", payload
            
        except jwt.ExpiredSignatureError:
            return False, "Token expired", None
        except jwt.InvalidTokenError:
            return False, "Invalid token", None
        except Exception as e:
            return False, f"Token verification error: {str(e)}", None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token (logout)."""
        session = self.db.query(SessionModel).filter(SessionModel.token == token).first()
        if session:
            session.is_valid = False
            self.db.commit()
            return True
        return False
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def _hash_reset_token(token: str) -> str:
        """Hash a reset token before storing it in the database."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _send_password_reset_email(self, recipient: str, username: str, reset_token: str) -> bool:
        """Send password reset instructions using configured SMTP settings."""
        smtp_host = os.environ.get("SMTP_HOST")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_password = os.environ.get("SMTP_PASSWORD")

        if not smtp_host or not smtp_user or not smtp_password:
            return False

        reset_link = os.environ.get(
            "PASSWORD_RESET_URL",
            f"http://localhost:5000/reset-password?token={reset_token}"
        )

        msg = EmailMessage()
        msg["From"] = smtp_user
        msg["To"] = recipient
        msg["Subject"] = "OmniAssist Password Reset"
        msg.set_content(
            "You requested a password reset for your OmniAssist account.\n\n"
            f"Username: {username}\n"
            f"Reset link: {reset_link}\n"
            f"Reset token: {reset_token}\n\n"
            "This token expires in 30 minutes and can be used only once.\n"
            "If you did not request this, you can ignore this email."
        )

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return True

    def request_password_reset(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Create and email a password reset token.

        Returns a generic success-style response for privacy (no account enumeration).
        """
        generic_message = "If an account with that email exists, reset instructions have been sent."

        user = self.db.query(User).filter(User.email == email).first()
        if not user or not user.is_active:
            return True, generic_message

        try:
            # Mark any older unused reset tokens as used before issuing a new one.
            active_tokens = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.utcnow()
            ).all()

            for token in active_tokens:
                token.used_at = datetime.utcnow()

            raw_token = secrets.token_urlsafe(32)
            token_hash = self._hash_reset_token(raw_token)
            expires_at = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)

            reset_entry = PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                requested_ip=ip_address,
                user_agent=user_agent
            )

            self.db.add(reset_entry)
            self.db.commit()

            try:
                sent = self._send_password_reset_email(user.email, user.username, raw_token)
                if not sent:
                    return False, "Password reset email is not configured on the server."
            except Exception:
                return False, "Failed to send password reset email."

            return True, generic_message
        except Exception as e:
            self.db.rollback()
            return False, f"Error requesting password reset: {str(e)}"

    def reset_password_with_token(self, token: str, new_password: str) -> Tuple[bool, str]:
        """Reset a user's password using a valid one-time token."""
        token_hash = self._hash_reset_token(token)

        reset_entry = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).first()

        if not reset_entry:
            return False, "Invalid or expired reset token"

        if reset_entry.used_at is not None:
            return False, "This reset token has already been used"

        if reset_entry.expires_at < datetime.utcnow():
            return False, "Invalid or expired reset token"

        user = self.db.query(User).filter(User.id == reset_entry.user_id).first()
        if not user or not user.is_active:
            return False, "Account is not available for password reset"

        try:
            user.hashed_password = PasswordHasher.hash_password(new_password)
            reset_entry.used_at = datetime.utcnow()

            # Revoke all active sessions to enforce re-login after password change.
            self.db.query(SessionModel).filter(
                SessionModel.user_id == user.id,
                SessionModel.is_valid == True
            ).update({"is_valid": False}, synchronize_session=False)

            self.db.commit()
            return True, "Password reset successful. Please log in again."
        except Exception as e:
            self.db.rollback()
            return False, f"Error resetting password: {str(e)}"
