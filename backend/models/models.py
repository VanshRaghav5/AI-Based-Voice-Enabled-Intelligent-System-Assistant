"""Database models for authentication, authorization, and scheduled tasks."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.models.database import Base


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # 'admin' or 'user'
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationship to sessions
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    scheduled_tasks = relationship(
        "ScheduledTask",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}', email_verified={self.is_email_verified})>"


class Session(Base):
    """Session model for tracking user sessions and JWT tokens."""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(255), nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<Session(user_id={self.user_id}, valid={self.is_valid})>"


class PasswordResetToken(Base):
    """Password reset token model for email-based account recovery."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    requested_ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)

    # Relationship to user
    user = relationship("User", back_populates="password_reset_tokens")

    def __repr__(self):
        return f"<PasswordResetToken(user_id={self.user_id}, used={self.used_at is not None})>"


class ScheduledTask(Base):
    """Scheduled automation task tied to a user account."""
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    command = Column(String(1000), nullable=False)
    language = Column(String(20), nullable=True)
    trigger_type = Column(String(20), nullable=False)
    run_at = Column(DateTime, nullable=True)
    interval_seconds = Column(Integer, nullable=True)
    cron_expression = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_status = Column(String(20), nullable=True)
    last_message = Column(String(500), nullable=True)

    user = relationship("User", back_populates="scheduled_tasks")

    def __repr__(self):
        return (
            f"<ScheduledTask(id={self.id}, user_id={self.user_id}, trigger_type='{self.trigger_type}', "
            f"active={self.is_active})>"
        )
