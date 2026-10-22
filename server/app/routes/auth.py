import os
import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.database import get_database
from app.models import User
from app.schemas import (
    LoginRequest, CreateStaffRequest, ChangePasswordRequest, UserResponse,
)
from app.auth_utils import (
    hash_password, verify_password, create_jwt_token, DUMMY_HASH,
)
from app.middleware.auth import verify_auth_cookie, require_admin
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Rate limiting state (in-memory for single instance)
LOGIN_ATTEMPTS = {}  # {email: [(timestamp, success), ...]}
LOGIN_WINDOW = 15 * 60  # 15 minutes
LOGIN_MAX_ATTEMPTS = 10

def check_login_limit(email: str) -> bool:
    """Check if login is rate limited."""
    now = time.time()
    if email not in LOGIN_ATTEMPTS:
        return True

    attempts = LOGIN_ATTEMPTS[email]
    attempts = [(ts, success) for ts, success in attempts if now - ts < LOGIN_WINDOW]
    LOGIN_ATTEMPTS[email] = attempts
    failed = sum(1 for ts, success in attempts if not success)
    return failed < LOGIN_MAX_ATTEMPTS

def record_login_attempt(email: str, success: bool):
    """Record a login attempt."""
    now = time.time()
    if email not in LOGIN_ATTEMPTS:
        LOGIN_ATTEMPTS[email] = []
    LOGIN_ATTEMPTS[email].append((now, success))

@router.post("/login")
async def login(request: Request, response: Response, payload: LoginRequest):
    """Login endpoint. Returns JWT token in HTTP-only cookie and user object."""
    email = payload.email.lower().strip()

    if not check_login_limit(email):
        await asyncio.sleep(0.1)
        raise HTTPException(status_code=429, detail="Too many failed login attempts. Please try again later.")

    db = get_database()
    user_model = User(db)
    user = await user_model.find_by_email(email)

    if not user:
        verify_password(payload.password, DUMMY_HASH)
        record_login_attempt(email, False)
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(payload.password, user.get("passwordHash", "")):
        record_login_attempt(email, False)
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    record_login_attempt(email, True)

    token_version = user.get("tokenVersion", 0)
    token = create_jwt_token(str(user["_id"]), user["email"], token_version)

    # Set HTTP-only cookie
    response.set_cookie(
        key="Authorization",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.node_env == "production" or os.getenv("VERCEL") == "1",
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/",
    )

    user_info = {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
    }

    return {"user": user_info, "token": token, **user_info}

@router.post("/logout")
async def logout(response: Response, auth_payload: dict = Depends(verify_auth_cookie)):
    """Logout endpoint. Clears auth cookie."""
    response.delete_cookie("Authorization", path="/")
    return {"message": "Logged out successfully."}

@router.get("/me")
async def get_current_user(auth_payload: dict = Depends(verify_auth_cookie)):
    """Get current authenticated user."""
    user_info = auth_payload.get("user")
    if not user_info:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"user": user_info, **user_info}

@router.post("/password")
async def change_password(
    response: Response,
    payload: ChangePasswordRequest,
    auth_payload: dict = Depends(verify_auth_cookie)
):
    """Change password for authenticated user."""
    db = get_database()
    user_model = User(db)
    user = await user_model.find_by_id(auth_payload.get("sub"))

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not verify_password(payload.currentPassword, user.get("passwordHash", "")):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    new_password_hash = hash_password(payload.newPassword)
    new_token_version = user.get("tokenVersion", 0) + 1
    await user_model.update_password(str(user["_id"]), new_password_hash, new_token_version)

    response.delete_cookie("Authorization", path="/")
    return {"message": "Password changed successfully."}

@router.get("/users")
async def list_staff(auth_payload: dict = Depends(require_admin)):
    """List all staff accounts (admin-only)."""
    db = get_database()
    user_model = User(db)
    users = await user_model.find_all()

    user_list = [
        {
            "id": str(u["_id"]),
            "name": u["name"],
            "email": u["email"],
            "role": u["role"],
            "createdAt": str(u.get("createdAt", "")),
        }
        for u in users
    ]
    return {"users": user_list}

@router.post("/users")
async def create_staff(
    payload: CreateStaffRequest,
    auth_payload: dict = Depends(require_admin)
):
    """Create a new staff member (admin-only)."""
    db = get_database()
    user_model = User(db)

    email = payload.email.lower().strip()
    existing = await user_model.find_by_email(email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already in use.")

    password_hash = hash_password(payload.password)
    user = await user_model.create(payload.name, email, password_hash, "staff")

    user_info = {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "createdAt": str(user.get("createdAt", "")),
    }
    return {"user": user_info, **user_info}
