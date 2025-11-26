"""
Authentication routes for login, registration, and user management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from pathlib import Path

from app.deps import get_db
from app.auth.models import User
from app.auth.utils import (
    authenticate_user,
    create_user,
    create_access_token,
    update_last_login,
    get_current_user
)
from app.auth.dependencies import require_auth, get_current_user_optional

router = APIRouter()

# Load HTML templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
LOGIN_HTML = (TEMPLATES_DIR / "login.html").read_text(encoding="utf-8")
REGISTER_HTML = (TEMPLATES_DIR / "register.html").read_text(encoding="utf-8")


# Pydantic models for request/response
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool


# ============================================================================
# API ENDPOINTS (JSON)
# ============================================================================

@router.post("/api/v1/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_api(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user (API endpoint)
    
    Returns user data on success
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin
    )


@router.post("/api/v1/auth/login", response_model=Token)
async def login_api(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login and get access token (API endpoint)
    
    Returns JWT access token on success
    """
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    update_last_login(db, user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_api(current_user: User = Depends(require_auth)):
    """
    Get current authenticated user info (API endpoint)
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin
    )


@router.post("/api/v1/auth/logout")
async def logout_api():
    """
    Logout (API endpoint)

    Note: For JWT tokens, logout is handled client-side by deleting the token
    """
    return {"message": "Logged out successfully"}


# ============================================================================
# HTML ENDPOINTS (Form-based authentication)
# ============================================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    """
    Serve login page

    If user is already authenticated, redirect to dashboard
    """
    user = await get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    return HTMLResponse(content=LOGIN_HTML)


@router.post("/login")
async def login_form(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle login form submission

    Sets access token in cookie and redirects to dashboard
    """
    user = authenticate_user(db, username, password)
    if not user:
        # Return to login page with error
        return HTMLResponse(
            content=LOGIN_HTML.replace(
                '<div id="error-message" class="error-message"></div>',
                '<div id="error-message" class="error-message">Invalid username or password</div>'
            ),
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Update last login
    update_last_login(db, user)

    # Create access token
    access_token = create_access_token(data={"sub": user.username})

    # Redirect to dashboard with cookie
    redirect_response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    redirect_response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24,  # 24 hours
        samesite="lax"
    )

    return redirect_response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    """
    Serve registration page

    If user is already authenticated, redirect to dashboard
    """
    user = await get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    return HTMLResponse(content=REGISTER_HTML)


@router.post("/register")
async def register_form(
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle registration form submission

    Creates user and redirects to login page
    """
    # Validate input
    if len(username) < 3:
        return HTMLResponse(
            content=REGISTER_HTML.replace(
                '<div id="error-message" class="error-message"></div>',
                '<div id="error-message" class="error-message">Username must be at least 3 characters</div>'
            ),
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 6:
        return HTMLResponse(
            content=REGISTER_HTML.replace(
                '<div id="error-message" class="error-message"></div>',
                '<div id="error-message" class="error-message">Password must be at least 6 characters</div>'
            ),
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return HTMLResponse(
            content=REGISTER_HTML.replace(
                '<div id="error-message" class="error-message"></div>',
                '<div id="error-message" class="error-message">Username already registered</div>'
            ),
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        return HTMLResponse(
            content=REGISTER_HTML.replace(
                '<div id="error-message" class="error-message"></div>',
                '<div id="error-message" class="error-message">Email already registered</div>'
            ),
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Create user
    try:
        user = create_user(
            db=db,
            username=username,
            email=email,
            password=password,
            full_name=full_name
        )
    except Exception as e:
        return HTMLResponse(
            content=REGISTER_HTML.replace(
                '<div id="error-message" class="error-message"></div>',
                f'<div id="error-message" class="error-message">Registration failed: {str(e)}</div>'
            ),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Redirect to login page with success message
    return RedirectResponse(url="/login?registered=true", status_code=status.HTTP_302_FOUND)


@router.get("/logout")
async def logout_html():
    """
    Logout (HTML endpoint)

    Clears cookie and redirects to login page
    """
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

