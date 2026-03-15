"""Tests for password reset flow in AuthService."""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.auth.auth_service import AuthService, PasswordHasher
from backend.database import Base
from backend.database.models import PasswordResetToken, Session as SessionModel


@pytest.fixture
def db_session():
    """Create an isolated in-memory database session for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _create_user(auth_service: AuthService, username: str = "alice", email: str = "alice@example.com"):
    success, message, user = auth_service.create_user(
        username=username,
        email=email,
        password="StrongPass123",
    )
    assert success, message
    return user


def test_password_reset_request_is_generic_for_unknown_email(db_session):
    """Unknown emails should return a generic success message for privacy."""
    auth_service = AuthService(db_session)

    success, message = auth_service.request_password_reset("nobody@example.com")

    assert success is True
    assert "If an account with that email exists" in message
    assert db_session.query(PasswordResetToken).count() == 0


def test_password_reset_request_creates_token_and_invalidates_old_ones(db_session):
    """A new request should mark previous active reset tokens as used."""
    auth_service = AuthService(db_session)
    _create_user(auth_service)

    with patch.object(AuthService, "_send_password_reset_email", return_value=True):
        success1, _ = auth_service.request_password_reset("alice@example.com")
        success2, _ = auth_service.request_password_reset("alice@example.com")

    assert success1 is True
    assert success2 is True

    tokens = db_session.query(PasswordResetToken).order_by(PasswordResetToken.id.asc()).all()
    assert len(tokens) == 2
    assert tokens[0].used_at is not None
    assert tokens[1].used_at is None


def test_reset_password_with_token_updates_password_and_revokes_sessions(db_session):
    """Reset confirmation should update password, consume token, and revoke sessions."""
    auth_service = AuthService(db_session)
    user = _create_user(auth_service)

    token, _ = auth_service.create_token(user)
    valid_session = (
        db_session.query(SessionModel)
        .filter(SessionModel.token == token)
        .first()
    )
    assert valid_session is not None
    assert valid_session.is_valid is True

    captured = {"token": None}

    def _fake_email(_recipient, _username, raw_token):
        captured["token"] = raw_token
        return True

    with patch.object(AuthService, "_send_password_reset_email", side_effect=_fake_email):
        success_req, message_req = auth_service.request_password_reset("alice@example.com")

    assert success_req is True, message_req
    assert captured["token"]

    success_reset, message_reset = auth_service.reset_password_with_token(
        captured["token"],
        "NewStrongPass456",
    )

    assert success_reset is True, message_reset
    assert "successful" in message_reset.lower()

    db_session.refresh(user)
    assert PasswordHasher.verify_password("NewStrongPass456", user.hashed_password)

    db_session.refresh(valid_session)
    assert valid_session.is_valid is False

    reset_entry = db_session.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id
    ).first()
    assert reset_entry.used_at is not None


def test_reset_password_with_expired_or_invalid_token_fails(db_session):
    """Reset should fail when token does not exist or is expired."""
    auth_service = AuthService(db_session)
    _create_user(auth_service)

    success, message = auth_service.reset_password_with_token("invalid-token", "AnotherPass789")
    assert success is False
    assert "invalid" in message.lower() or "expired" in message.lower()

    raw_token = "expired-token-value"
    token_hash = AuthService._hash_reset_token(raw_token)
    expired_entry = PasswordResetToken(
        user_id=1,
        token_hash=token_hash,
        expires_at=datetime.utcnow() - timedelta(minutes=1),
    )
    db_session.add(expired_entry)
    db_session.commit()

    success_expired, message_expired = auth_service.reset_password_with_token(
        raw_token,
        "AnotherPass789",
    )
    assert success_expired is False
    assert "invalid" in message_expired.lower() or "expired" in message_expired.lower()
