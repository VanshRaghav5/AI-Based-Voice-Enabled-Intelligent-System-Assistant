"""Authentication service with password hashing and JWT token management."""

import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from backend.database.models import User, Session as SessionModel


# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour


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
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
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
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
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
