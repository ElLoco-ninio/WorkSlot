"""Security utilities: password hashing, JWT tokens, API keys."""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============== Password Utilities ==============

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============== JWT Token Utilities ==============

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow(),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow(),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def create_token_pair(user_id: str) -> Tuple[str, str, int]:
    """Create access and refresh token pair."""
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return access_token, refresh_token, expires_in


# ============== API Key Utilities ==============

def generate_api_key() -> Tuple[str, str, str]:
    """
    Generate a new API key.
    
    Returns:
        Tuple of (full_key, key_prefix, key_hash)
        - full_key: The complete API key to give to the user (shown once)
        - key_prefix: Prefix for display (e.g., "wsk_abc123...")
        - key_hash: SHA-256 hash for secure storage
    """
    # Generate random bytes
    random_bytes = secrets.token_bytes(settings.API_KEY_LENGTH)
    
    # Create the key with prefix
    key_suffix = secrets.token_urlsafe(settings.API_KEY_LENGTH)
    full_key = f"{settings.API_KEY_PREFIX}_{key_suffix}"
    
    # Create prefix for display (first 12 chars including prefix)
    key_prefix = full_key[:12]
    
    # Hash the key for storage
    key_hash = hash_api_key(full_key)
    
    return full_key, key_prefix, key_hash


def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def validate_api_key_format(api_key: str) -> bool:
    """Validate API key format."""
    if not api_key:
        return False
    
    # Check prefix
    if not api_key.startswith(f"{settings.API_KEY_PREFIX}_"):
        return False
    
    # Check minimum length
    if len(api_key) < 20:
        return False
    
    return True


# ============== Email Verification Token ==============

def generate_verification_token() -> Tuple[str, str]:
    """
    Generate a verification token for email confirmation.
    
    Returns:
        Tuple of (token, token_hash)
    """
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


def hash_verification_token(token: str) -> str:
    """Hash a verification token."""
    return hashlib.sha256(token.encode()).hexdigest()

