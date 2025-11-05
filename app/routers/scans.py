"""
REST API endpoints for scan operations
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.deps import get_db
from app.storage.repo import ScanJobRepository, SubdomainRepository, ScreenshotRepository, WafDetectionRepository, LeakDetectionRepository
from app.storage.models import ScanStatus
from app.workers.tasks import run_recon_scan

router = APIRouter()


# Pydantic models for request/response
class ScanRequest(BaseModel):
    domain: str = Field(..., description="Target domain to scan", example="example.com")


class ScanResponse(BaseModel):
    job_id: str
    domain: str
    status: str
    message: str


class BulkScanRequest(BaseModel):
    domains: List[str] = Field(..., description="List of domains to scan", example=["example1.com", "example2.com", "example3.com"])


class BulkScanResponse(BaseModel):
    total_submitted: int
    jobs: List[ScanResponse]
    message: str


class SubdomainInfo(BaseModel):
    id: int
    subdomain: str
    status: str
    is_live: bool
    http_status: Optional[int] = None
    response_time: Optional[int] = None
    discovered_by: Optional[str] = None


class ScreenshotInfo(BaseModel):
    id: int
    url: str
    filename: str
    file_path: str
    file_size: Optional[int] = None


class WafDetectionInfo(BaseModel):
    id: int
    url: str
    has_waf: bool
    waf_name: Optional[str] = None
    waf_manufacturer: Optional[str] = None


class LeakDetectionInfo(BaseModel):
    id: int
    base_url: str
    leaked_file_url: str
    file_type: Optional[str] = None
    severity: Optional[str] = None
    file_size: Optional[int] = None
    http_status: Optional[int] = None  # HTTP status code (200, 403, etc.)


class ScanResultResponse(BaseModel):
    job_id: str
    domain: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    subdomains: List[SubdomainInfo] = []
    screenshots: List[ScreenshotInfo] = []
    waf_detections: List[WafDetectionInfo] = []
    leak_detections: List[LeakDetectionInfo] = []


class ScanListResponse(BaseModel):
    job_id: str
    domain: str
    status: str
    created_at: str
    subdomains_count: int
    screenshots_count: int


@router.post("/scans", response_model=ScanResponse)
async def create_scan(
    scan_request: ScanRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new reconnaissance scan job
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Validate domain
    domain = scan_request.domain.strip().lower()
    if not domain or '.' not in domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid domain format"
        )

    # Create scan job in database
    scan_repo = ScanJobRepository(db)
    scan_job = scan_repo.create_scan_job(job_id, domain)

    # Start background task
    task = run_recon_scan.delay(job_id, domain)

    # Store task_id in database for progress tracking
    scan_repo.update_task_id(job_id, task.id)

    return ScanResponse(
        job_id=job_id,
        domain=domain,
        status="pending",
        message=f"Scan job created successfully. Task ID: {task.id}"
    )


@router.post("/scans/bulk", response_model=BulkScanResponse)
async def create_bulk_scans(
    bulk_request: BulkScanRequest,
    db: Session = Depends(get_db)
):
    """
    Create multiple reconnaissance scan jobs at once

    Each domain will be processed as a separate Celery task,
    automatically distributed across available workers.
    """
    scan_repo = ScanJobRepository(db)
    jobs = []

    for domain in bulk_request.domains:
        # Validate domain
        domain = domain.strip().lower()
        if not domain or '.' not in domain:
            # Skip invalid domains
            continue

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Create scan job in database
        scan_job = scan_repo.create_scan_job(job_id, domain)

        # Start background task
        task = run_recon_scan.delay(job_id, domain)

        # Store task_id in database
        scan_repo.update_task_id(job_id, task.id)

        jobs.append(ScanResponse(
            job_id=job_id,
            domain=domain,
            status="pending",
            message=f"Task ID: {task.id}"
        ))

    return BulkScanResponse(
        total_submitted=len(jobs),
        jobs=jobs,
        message=f"Successfully submitted {len(jobs)} scan jobs. Workers will process them in parallel."
    )


@router.get("/scans/{job_id}", response_model=ScanResultResponse)
async def get_scan_result(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get scan results by job ID
    """
    scan_repo = ScanJobRepository(db)
    scan_job = scan_repo.get_scan_job(job_id)
    
    if not scan_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan job not found"
        )
    
    # Get subdomains
    subdomain_repo = SubdomainRepository(db)
    subdomains = subdomain_repo.get_subdomains_by_job(job_id)

    # Get screenshots
    screenshot_repo = ScreenshotRepository(db)
    screenshots = screenshot_repo.get_screenshots_by_job(job_id)

    # Get WAF detections
    waf_repo = WafDetectionRepository(db)
    waf_detections = waf_repo.get_by_job(job_id)

    # Get leak detections
    leak_repo = LeakDetectionRepository(db)
    leak_detections = leak_repo.get_by_job(job_id)

    return ScanResultResponse(
        job_id=scan_job.job_id,
        domain=scan_job.domain,
        status=scan_job.status,
        created_at=scan_job.created_at.isoformat(),
        completed_at=scan_job.completed_at.isoformat() if scan_job.completed_at else None,
        error_message=scan_job.error_message,
        subdomains=[
            SubdomainInfo(
                id=sub.id,
                subdomain=sub.subdomain,
                status=sub.status,
                is_live=sub.is_live,
                http_status=sub.http_status,
                response_time=sub.response_time,
                discovered_by=sub.discovered_by
            )
            for sub in subdomains
        ],
        screenshots=[
            ScreenshotInfo(
                id=shot.id,
                url=shot.url,
                filename=shot.filename,
                file_path=shot.file_path,
                file_size=shot.file_size
            )
            for shot in screenshots
        ],
        waf_detections=[
            WafDetectionInfo(
                id=waf.id,
                url=waf.url,
                has_waf=waf.has_waf,
                waf_name=waf.waf_name,
                waf_manufacturer=waf.waf_manufacturer
            )
            for waf in waf_detections
        ],
        leak_detections=[
            LeakDetectionInfo(
                id=leak.id,
                base_url=leak.base_url,
                leaked_file_url=leak.leaked_file_url,
                file_type=leak.file_type,
                severity=leak.severity,
                file_size=leak.file_size
            )
            for leak in leak_detections
        ]
    )


@router.get("/scans", response_model=List[ScanListResponse])
async def list_scans(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List recent scan jobs with pagination support
    """
    scan_repo = ScanJobRepository(db)
    scan_jobs = scan_repo.get_recent_scans(limit, offset)
    
    result = []
    for scan_job in scan_jobs:
        # Count subdomains and screenshots
        subdomain_repo = SubdomainRepository(db)
        screenshot_repo = ScreenshotRepository(db)
        
        subdomains_count = len(subdomain_repo.get_subdomains_by_job(scan_job.job_id))
        screenshots_count = len(screenshot_repo.get_screenshots_by_job(scan_job.job_id))
        
        result.append(ScanListResponse(
            job_id=scan_job.job_id,
            domain=scan_job.domain,
            status=scan_job.status,
            created_at=scan_job.created_at.isoformat(),
            subdomains_count=subdomains_count,
            screenshots_count=screenshots_count
        ))
    
    return result


@router.delete("/scans/{job_id}")
async def delete_scan(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a scan job and its associated data
    """
    import shutil
    from pathlib import Path
    from app.deps import settings
    
    scan_repo = ScanJobRepository(db)
    scan_job = scan_repo.get_scan_job(job_id)
    
    if not scan_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan job not found"
        )
    
    # Delete job directory
    job_dir = Path(settings.jobs_directory) / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)
    
    # Delete from database (cascade will handle related records)
    db.delete(scan_job)
    db.commit()
    
    return {"message": f"Scan job {job_id} deleted successfully"}


@router.get("/scans/{job_id}/progress")
async def get_scan_progress(job_id: str, db: Session = Depends(get_db)):
    """
    Get scan progress from Celery task and database
    """
    from app.workers.celery_app import celery_app

    # Get scan job from database
    scan_repo = ScanJobRepository(db)
    scan_job = scan_repo.get_scan_job(job_id)

    if not scan_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan job not found"
        )

    # If we have task_id, check Celery task state
    if scan_job.task_id:
        result = celery_app.AsyncResult(scan_job.task_id)

        if result.state == 'PENDING':
            return {
                'job_id': job_id,
                'status': 'pending',
                'message': 'Task is waiting to be executed',
                'db_status': scan_job.status
            }
        elif result.state == 'PROGRESS':
            return {
                'job_id': job_id,
                'status': 'running',
                'progress': result.info,
                'db_status': scan_job.status
            }
        elif result.state == 'SUCCESS':
            return {
                'job_id': job_id,
                'status': 'completed',
                'result': result.info,
                'db_status': scan_job.status
            }
        elif result.state == 'FAILURE':
            return {
                'job_id': job_id,
                'status': 'failed',
                'error': str(result.info),
                'db_status': scan_job.status
            }
        elif result.state == 'RETRY':
            return {
                'job_id': job_id,
                'status': 'retrying',
                'message': 'Task is being retried',
                'db_status': scan_job.status
            }

    # Fallback to database status
    status_map = {
        ScanStatus.PENDING: 'pending',
        ScanStatus.RUNNING: 'running',
        ScanStatus.COMPLETED: 'completed',
        ScanStatus.FAILED: 'failed'
    }

    return {
        'job_id': job_id,
        'status': status_map.get(scan_job.status, 'unknown'),
        'db_status': scan_job.status,
        'created_at': scan_job.created_at.isoformat(),
        'completed_at': scan_job.completed_at.isoformat() if scan_job.completed_at else None,
        'error_message': scan_job.error_message
    }


# Selective Leak Scanning
class SelectiveScanRequest(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to scan for leaks", example=["https://example.com", "https://api.example.com"])
    mode: str = Field(default="tiny", description="Scan mode: 'tiny' (fast) or 'full' (thorough)", example="tiny")


class SelectiveScanResponse(BaseModel):
    task_id: str
    job_id: str
    urls_to_scan: int
    mode: str
    message: str
    status: str = "started"


class AddSubdomainRequest(BaseModel):
    subdomain: str = Field(..., description="Subdomain to add (e.g., 'admin.example.com' or 'https://admin.example.com')", example="admin.example.com")
    is_live: Optional[bool] = Field(None, description="Whether the subdomain is live (optional)")
    http_status: Optional[int] = Field(None, description="HTTP status code (optional)", example=200)


class AddSubdomainResponse(BaseModel):
    id: int
    subdomain: str
    status: str
    is_live: bool
    http_status: Optional[int] = None
    discovered_by: str
    message: str


@router.post("/scans/{job_id}/leak-scan", response_model=SelectiveScanResponse)
async def run_selective_leak_scan(
    job_id: str,
    request: SelectiveScanRequest,
    db: Session = Depends(get_db)
):
    """
    **ASYNC VERSION:** Dispatch SourceLeakHacker scan on selected URLs as a background task.

    This endpoint allows you to selectively scan specific URLs for source code leaks
    after the initial reconnaissance scan has completed. The scan runs asynchronously
    in the background, and you can check progress via the `/scans/{job_id}/progress` endpoint.

    **Parameters:**
    - `job_id`: The ID of the completed scan job
    - `urls`: List of URLs to scan (must be from the job's live hosts)
    - `mode`: Scan mode - 'tiny' (faster, ~100 paths) or 'full' (thorough, ~1000 paths)

    **Returns:**
    - `task_id`: Celery task ID for tracking progress
    - `job_id`: The scan job ID
    - `urls_to_scan`: Number of URLs that will be scanned
    - `mode`: Scan mode used
    - `message`: Status message

    **Check Progress:**
    Use `GET /api/v1/scans/{job_id}/progress` to check the task status and progress.
    """
    from pathlib import Path
    from app.deps import settings
    from app.workers.tasks import run_sourceleakhacker_check

    # Validate mode
    if request.mode not in ['tiny', 'full']:
        raise HTTPException(
            status_code=400,
            detail="Invalid mode. Must be 'tiny' or 'full'"
        )

    # Get scan job from database
    scan_repo = ScanJobRepository(db)
    scan_job = scan_repo.get_scan_job(job_id)

    if not scan_job:
        raise HTTPException(
            status_code=404,
            detail=f"Scan job {job_id} not found"
        )

    # Check if job has completed
    if scan_job.status != ScanStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Scan job must be completed. Current status: {scan_job.status}"
        )

    # Validate URLs belong to this job
    job_dir = Path(settings.jobs_directory) / job_id
    live_file = job_dir / "live.txt"

    if not live_file.exists():
        raise HTTPException(
            status_code=400,
            detail="No live hosts found for this job. Run a full scan first."
        )

    # Read valid URLs from live.txt (JSON Lines format from httpx)
    import json
    valid_urls = set()
    with open(live_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)
                    if 'url' in data:
                        valid_urls.add(data['url'])
                except json.JSONDecodeError:
                    continue

    # Filter requested URLs to only valid ones
    urls_to_scan = [url for url in request.urls if url in valid_urls]

    if not urls_to_scan:
        raise HTTPException(
            status_code=400,
            detail="None of the provided URLs are valid live hosts from this job"
        )

    # Dispatch Celery task (ASYNC - returns immediately)
    task = run_sourceleakhacker_check.delay(job_id, urls_to_scan, request.mode)

    return SelectiveScanResponse(
        task_id=task.id,
        job_id=job_id,
        urls_to_scan=len(urls_to_scan),
        mode=request.mode,
        message=f"Leak scan started on {len(urls_to_scan)} URLs in '{request.mode}' mode. Use task_id to check progress.",
        status="started"
    )


@router.post("/scans/{job_id}/subdomains", response_model=AddSubdomainResponse)
async def add_subdomain_manually(
    job_id: str,
    request: AddSubdomainRequest,
    db: Session = Depends(get_db)
):
    """
    Manually add a subdomain to an existing scan job.

    This endpoint allows you to add subdomains that were not discovered by automated tools.

    **Parameters:**
    - `job_id`: The ID of the scan job
    - `subdomain`: The subdomain to add (e.g., "admin.example.com" or "https://admin.example.com")
    - `is_live`: (Optional) Whether the subdomain is live
    - `http_status`: (Optional) HTTP status code

    **Returns:**
    - The created subdomain record

    **Example:**
    ```json
    {
        "subdomain": "admin.fpt.ai",
        "is_live": true,
        "http_status": 200
    }
    ```
    """
    import re
    from urllib.parse import urlparse
    from app.storage.models import SubdomainStatus

    # Get scan job from database
    scan_repo = ScanJobRepository(db)
    scan_job = scan_repo.get_scan_job(job_id)

    if not scan_job:
        raise HTTPException(
            status_code=404,
            detail=f"Scan job {job_id} not found"
        )

    # Parse and validate subdomain
    subdomain_str = request.subdomain.strip()

    # Remove protocol if present
    if subdomain_str.startswith('http://') or subdomain_str.startswith('https://'):
        parsed = urlparse(subdomain_str)
        subdomain_str = parsed.netloc

    # Remove trailing slash and path
    subdomain_str = subdomain_str.split('/')[0]

    # Validate subdomain format (basic validation)
    if not subdomain_str or '.' not in subdomain_str:
        raise HTTPException(
            status_code=400,
            detail="Invalid subdomain format. Must be a valid domain name (e.g., 'admin.example.com')"
        )

    # Validate subdomain belongs to the scan's domain
    if not subdomain_str.endswith(scan_job.domain):
        raise HTTPException(
            status_code=400,
            detail=f"Subdomain must belong to the scan's domain ({scan_job.domain})"
        )

    # Check if subdomain already exists
    subdomain_repo = SubdomainRepository(db)
    existing_subdomains = subdomain_repo.get_subdomains_by_job(job_id)

    for existing in existing_subdomains:
        if existing.subdomain.lower() == subdomain_str.lower():
            raise HTTPException(
                status_code=409,
                detail=f"Subdomain '{subdomain_str}' already exists in this scan"
            )

    # Determine status
    if request.is_live is True:
        status = SubdomainStatus.LIVE
    elif request.is_live is False:
        status = SubdomainStatus.DEAD
    else:
        status = SubdomainStatus.FOUND

    # Create subdomain
    subdomain = subdomain_repo.create_subdomain(
        scan_job_id=scan_job.id,
        subdomain=subdomain_str,
        discovered_by="manual"
    )

    # Update status if provided
    if request.is_live is not None or request.http_status is not None:
        subdomain = subdomain_repo.update_subdomain_status(
            subdomain_id=subdomain.id,
            status=status,
            is_live=request.is_live if request.is_live is not None else False,
            http_status=request.http_status,
            response_time=None
        )

    return AddSubdomainResponse(
        id=subdomain.id,
        subdomain=subdomain.subdomain,
        status=subdomain.status,
        is_live=subdomain.is_live,
        http_status=subdomain.http_status,
        discovered_by=subdomain.discovered_by,
        message=f"Subdomain '{subdomain.subdomain}' added successfully"
    )
