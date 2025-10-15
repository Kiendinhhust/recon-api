"""
REST API endpoints for scan operations
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.deps import get_db
from app.storage.repo import ScanJobRepository, SubdomainRepository, ScreenshotRepository
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


class ScanResultResponse(BaseModel):
    job_id: str
    domain: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    subdomains: List[SubdomainInfo] = []
    screenshots: List[ScreenshotInfo] = []


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
        ]
    )


@router.get("/scans", response_model=List[ScanListResponse])
async def list_scans(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List recent scan jobs
    """
    scan_repo = ScanJobRepository(db)
    scan_jobs = scan_repo.get_recent_scans(limit)
    
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
