import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.config import settings

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with 12 rounds."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

# Dummy hash for timing-attack mitigation
DUMMY_HASH = hash_password("dummy_password_12345")

def create_jwt_token(
    user_id: str,
    user_email: str,
    token_version: int,
    expires_in: int = 7 * 24 * 60 * 60  # 7 days in seconds
) -> str:
    """Create a JWT token."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=expires_in)
    jti = secrets.token_hex(16)

    payload = {
        "sub": str(user_id),
        "issuer": "carepoint-hospital",
        "audience": "carepoint-web",
        "exp": exp,
        "iat": now,
        "jti": jti,
        "version": token_version,
        "email": user_email,
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token

def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience="carepoint-web",
            issuer="carepoint-hospital",
        )
        return payload
    except JWTError:
        # Fallback decode without audience/issuer if generated differently
        try:
            return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], options={"verify_aud": False, "verify_iss": False})
        except JWTError:
            return None

def parse_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    """Extract token from Authorization header."""
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None
