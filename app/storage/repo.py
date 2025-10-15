"""
Repository layer for database operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.storage.models import ScanJob, Subdomain, Screenshot, ScanStatus, SubdomainStatus


class ScanJobRepository:
    """Repository for scan job operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_scan_job(self, job_id: str, domain: str) -> ScanJob:
        """Create a new scan job"""
        scan_job = ScanJob(job_id=job_id, domain=domain)
        self.db.add(scan_job)
        self.db.commit()
        self.db.refresh(scan_job)
        return scan_job
    
    def get_scan_job(self, job_id: str) -> Optional[ScanJob]:
        """Get scan job by job_id"""
        return self.db.query(ScanJob).filter(ScanJob.job_id == job_id).first()
    
    def update_scan_status(self, job_id: str, status: ScanStatus, error_message: str = None) -> Optional[ScanJob]:
        """Update scan job status"""
        scan_job = self.get_scan_job(job_id)
        if scan_job:
            scan_job.status = status
            if error_message:
                scan_job.error_message = error_message
            if status == ScanStatus.COMPLETED:
                from datetime import datetime
                scan_job.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(scan_job)
        return scan_job

    def update_task_id(self, job_id: str, task_id: str) -> Optional[ScanJob]:
        """Update Celery task ID for progress tracking"""
        scan_job = self.get_scan_job(job_id)
        if scan_job:
            scan_job.task_id = task_id
            self.db.commit()
            self.db.refresh(scan_job)
        return scan_job
    
    def get_recent_scans(self, limit: int = 10) -> List[ScanJob]:
        """Get recent scan jobs"""
        return self.db.query(ScanJob).order_by(desc(ScanJob.created_at)).limit(limit).all()


class SubdomainRepository:
    """Repository for subdomain operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_subdomain(self, scan_job_id: int, subdomain: str, discovered_by: str = None) -> Subdomain:
        """Create a new subdomain"""
        subdomain_obj = Subdomain(
            scan_job_id=scan_job_id,
            subdomain=subdomain,
            discovered_by=discovered_by
        )
        self.db.add(subdomain_obj)
        self.db.commit()
        self.db.refresh(subdomain_obj)
        return subdomain_obj
    
    def bulk_create_subdomains(self, scan_job_id: int, subdomains: List[str], discovered_by: str = None) -> List[Subdomain]:
        """Bulk create subdomains"""
        subdomain_objs = []
        for subdomain in subdomains:
            subdomain_obj = Subdomain(
                scan_job_id=scan_job_id,
                subdomain=subdomain,
                discovered_by=discovered_by
            )
            subdomain_objs.append(subdomain_obj)
        
        self.db.add_all(subdomain_objs)
        self.db.commit()
        return subdomain_objs
    
    def update_subdomain_status(self, subdomain_id: int, status: SubdomainStatus, 
                              is_live: bool = False, http_status: int = None, 
                              response_time: int = None) -> Optional[Subdomain]:
        """Update subdomain status and live check results"""
        subdomain = self.db.query(Subdomain).filter(Subdomain.id == subdomain_id).first()
        if subdomain:
            subdomain.status = status
            subdomain.is_live = is_live
            if http_status:
                subdomain.http_status = http_status
            if response_time:
                subdomain.response_time = response_time
            self.db.commit()
            self.db.refresh(subdomain)
        return subdomain
    
    def get_subdomains_by_job(self, job_id: str) -> List[Subdomain]:
        """Get all subdomains for a scan job"""
        return self.db.query(Subdomain).join(ScanJob).filter(ScanJob.job_id == job_id).all()
    
    def get_live_subdomains_by_job(self, job_id: str) -> List[Subdomain]:
        """Get live subdomains for a scan job"""
        return self.db.query(Subdomain).join(ScanJob).filter(
            ScanJob.job_id == job_id,
            Subdomain.is_live == True
        ).all()


class ScreenshotRepository:
    """Repository for screenshot operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_screenshot(self, scan_job_id: int, url: str, filename: str, 
                         file_path: str, subdomain_id: int = None, 
                         file_size: int = None) -> Screenshot:
        """Create a new screenshot record"""
        screenshot = Screenshot(
            scan_job_id=scan_job_id,
            subdomain_id=subdomain_id,
            url=url,
            filename=filename,
            file_path=file_path,
            file_size=file_size
        )
        self.db.add(screenshot)
        self.db.commit()
        self.db.refresh(screenshot)
        return screenshot
    
    def get_screenshots_by_job(self, job_id: str) -> List[Screenshot]:
        """Get all screenshots for a scan job"""
        return self.db.query(Screenshot).join(ScanJob).filter(ScanJob.job_id == job_id).all()
    
    def get_screenshots_by_subdomain(self, subdomain_id: int) -> List[Screenshot]:
        """Get screenshots for a specific subdomain"""
        return self.db.query(Screenshot).filter(Screenshot.subdomain_id == subdomain_id).all()
