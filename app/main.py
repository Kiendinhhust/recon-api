"""
Main FastAPI application for Recon API
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.deps import settings, setup_cors, create_jobs_directory
from app.routers import scans


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
    app.include_router(scans.router, prefix="/api/v1", tags=["scans"])
    
    # Serve static files (screenshots and jobs)
    app.mount("/jobs", StaticFiles(directory="jobs"), name="jobs")

    # Serve web UI
    app.mount("/dashboard", StaticFiles(directory="web", html=True), name="web")

    # Simple frontend (redirect to dashboard)
    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Recon API</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .card { border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px; }
                .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                .btn:hover { background: #0056b3; }
                input[type="text"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
                .results { margin-top: 20px; }
                .subdomain { padding: 5px; margin: 2px 0; background: #f8f9fa; border-radius: 4px; }
                .screenshot { max-width: 200px; margin: 10px; border: 1px solid #ddd; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Recon API - Subdomain Scanner</h1>
                
                <div class="card">
                    <h2>Start New Scan</h2>
                    <input type="text" id="domain" placeholder="Enter domain (e.g., example.com)">
                    <button class="btn" onclick="startScan()">Start Scan</button>
                </div>
                
                <div class="card">
                    <h2>Check Scan Status</h2>
                    <input type="text" id="jobId" placeholder="Enter job ID">
                    <button class="btn" onclick="checkStatus()">Check Status</button>
                </div>
                
                <div id="results" class="results"></div>
            </div>
            
            <script>
                async function startScan() {
                    const domain = document.getElementById('domain').value;
                    if (!domain) {
                        alert('Please enter a domain');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/v1/scans', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ domain: domain })
                        });
                        const data = await response.json();
                        document.getElementById('results').innerHTML = 
                            `<div class="card"><h3>Scan Started</h3><p>Job ID: ${data.job_id}</p><p>Status: ${data.status}</p></div>`;
                    } catch (error) {
                        document.getElementById('results').innerHTML = 
                            `<div class="card"><h3>Error</h3><p>${error.message}</p></div>`;
                    }
                }
                
                async function checkStatus() {
                    const jobId = document.getElementById('jobId').value;
                    if (!jobId) {
                        alert('Please enter a job ID');
                        return;
                    }
                    
                    try {
                        const response = await fetch(`/api/v1/scans/${jobId}`);
                        const data = await response.json();
                        
                        let html = `<div class="card"><h3>Scan Results</h3>`;
                        html += `<p><strong>Status:</strong> ${data.status}</p>`;
                        html += `<p><strong>Domain:</strong> ${data.domain}</p>`;
                        
                        if (data.subdomains && data.subdomains.length > 0) {
                            html += `<h4>Found Subdomains (${data.subdomains.length}):</h4>`;
                            data.subdomains.forEach(sub => {
                                html += `<div class="subdomain">${sub.subdomain} - ${sub.status}</div>`;
                            });
                        }
                        
                        if (data.screenshots && data.screenshots.length > 0) {
                            html += `<h4>Screenshots:</h4>`;
                            data.screenshots.forEach(shot => {
                                html += `<img src="/static/${data.job_id}/shots/${shot.filename}" class="screenshot" alt="${shot.url}">`;
                            });
                        }
                        
                        html += `</div>`;
                        document.getElementById('results').innerHTML = html;
                    } catch (error) {
                        document.getElementById('results').innerHTML = 
                            `<div class="card"><h3>Error</h3><p>${error.message}</p></div>`;
                    }
                }
            </script>
        </body>
        </html>
        """
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
