import time
from fastapi import Depends, HTTPException, Request
from app.auth_utils import verify_jwt_token, parse_bearer_token
from app.database import get_database
from app.models import User

async def verify_auth_cookie(request: Request) -> dict:
    """
    Middleware dependency to verify JWT auth cookie or Bearer token.
    Returns the decoded JWT payload with user details.
    Raises HTTPException(401) if token is missing, invalid, or user session is invalidated.
    """
    token = request.cookies.get("Authorization")
    if not token:
        token = parse_bearer_token(request.headers.get("Authorization"))

    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Check token expiration
    if payload.get("exp", 0) < time.time():
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Verify user exists in database and token version is valid
    db = get_database()
    user_model = User(db)
    user = await user_model.find_by_id(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if user.get("tokenVersion", 0) != payload.get("version", 0):
        raise HTTPException(status_code=401, detail="Unauthorized")

    payload["user"] = {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
    }
    return payload

async def require_admin(auth_payload: dict = Depends(verify_auth_cookie)) -> dict:
    """
    Middleware dependency to verify the user has the admin role.
    Raises HTTPException(403) if user is not admin.
    """
    user_info = auth_payload.get("user", {})
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return auth_payload
