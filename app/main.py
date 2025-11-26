"""
Main FastAPI application for Recon API
"""
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from sqlalchemy.orm import Session

from app.deps import settings, setup_cors, create_jobs_directory, get_db
from app.routers import scans, auth
from app.auth.dependencies import get_current_user_optional


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Setup CORS
    setup_cors(app)
    
    # Create necessary directories
    create_jobs_directory()

    # Include routers
    app.include_router(auth.router, tags=["authentication"])
    app.include_router(scans.router, prefix="/api/v1", tags=["scans"])

    # Serve static files (CSS, JavaScript, screenshots, and jobs)
    # Mount web static files (CSS, JS) - must be before routes to avoid conflicts
    from pathlib import Path
    web_dir = Path("web")
    if web_dir.exists():
        app.mount("/static", StaticFiles(directory="web"), name="static")

    # Serve jobs directory (screenshots and scan results)
    app.mount("/jobs", StaticFiles(directory="jobs"), name="jobs")

    # Root route - redirect to login
    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request, db: Session = Depends(get_db)):
        """
        Root route - redirect to dashboard if authenticated, otherwise to login
        """
        user = await get_current_user_optional(request, db)
        if user:
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        else:
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # Protected dashboard route
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_redirect(request: Request, db: Session = Depends(get_db)):
        """
        Dashboard route - require authentication
        """
        user = await get_current_user_optional(request, db)
        if not user:
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

        # Serve the dashboard HTML with user info
        from pathlib import Path
        dashboard_html = (Path("web") / "index.html").read_text(encoding="utf-8")

        # Inject user info and logout button into dashboard
        dashboard_html = dashboard_html.replace(
            '<h1 class="logo">🔍 Recon WEB-KD</h1>',
            f'<h1 class="logo">🔍 Recon WEB-KD</h1><p style="color: white; margin-top: 10px;">Welcome, {user.username}! <a href="/logout" style="color: white; text-decoration: underline;">Logout</a></p>'
        )

        return HTMLResponse(content=dashboard_html)
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
