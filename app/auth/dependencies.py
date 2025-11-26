"""
Authentication dependencies for route protection
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.deps import get_db
from app.auth.models import User
from app.auth.utils import get_current_user, decode_access_token

# HTTP Bearer token scheme (optional - allows None)
security = HTTPBearer(auto_error=False)


async def get_current_user_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from either Authorization header or cookie

    This dependency checks both:
    1. Authorization: Bearer <token> header (for API clients)
    2. access_token cookie (for browser-based requests)
    """
    token = None

    # Try to get token from Authorization header first
    if credentials:
        token = credentials.credentials

    # If no Authorization header, try to get token from cookie
    if not token:
        token = request.cookies.get("access_token")

    # If still no token, raise authentication error
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode and validate token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get username from token
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


def require_auth(current_user: User = Depends(get_current_user_from_request)) -> User:
    """
    Dependency to require authentication for API routes

    Accepts JWT token from either:
    - Authorization: Bearer <token> header
    - access_token cookie

    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(require_auth)):
            return {"message": f"Hello {user.username}"}
    """
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require admin privileges
    
    Usage:
        @router.get("/admin-only")
        async def admin_route(user: User = Depends(require_admin)):
            return {"message": "Admin access granted"}
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """
    Get current user from session cookie (optional - doesn't raise exception if not authenticated)
    
    This is used for HTML pages that should work for both authenticated and unauthenticated users
    """
    from app.auth.utils import decode_access_token
    
    # Try to get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    username = payload.get("sub")
    if username is None:
        return None
    
    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        return None
    
    return user


async def require_auth_html(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Require authentication for HTML pages (redirects to login if not authenticated)
    
    Usage:
        @app.get("/dashboard")
        async def dashboard(user: User = Depends(require_auth_html)):
            return HTMLResponse(...)
    """
    user = await get_current_user_optional(request, db)
    if user is None:
        # Redirect to login page
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return user

