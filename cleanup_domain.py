"""
Script to cleanup jobs for a specific domain
Usage: python cleanup_domain.py <domain>
"""
import sys
from app.deps import SessionLocal
from app.storage.models import ScanJob
from app.workers.celery_app import celery_app
import shutil
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python cleanup_domain.py <domain>")
    print("Example: python cleanup_domain.py soict.ai")
    sys.exit(1)

domain = sys.argv[1]

db = SessionLocal()

try:
    # Find all jobs for domain
    jobs = db.query(ScanJob).filter(ScanJob.domain == domain).all()
    
    print(f"Found {len(jobs)} jobs for {domain}:")
    print()
    
    if not jobs:
        print(f"No jobs found for {domain}")
        sys.exit(0)
    
    for job in jobs:
        print(f"Job ID: {job.job_id}")
        print(f"  Status: {job.status}")
        print(f"  Created: {job.created_at}")
        print()
    
    # Delete all jobs
    for job in jobs:
        print(f"Deleting job {job.job_id}...")
        
        # 1. Revoke Celery task
        if job.task_id:
            try:
                celery_app.control.revoke(job.task_id, terminate=True)
                print(f"  ✅ Revoked Celery task")
            except Exception as e:
                print(f"  ⚠️  Failed to revoke task: {e}")
        
        # 2. Delete job directory
        job_dir = Path("jobs") / job.job_id
        if job_dir.exists():
            try:
                shutil.rmtree(job_dir)
                print(f"  ✅ Deleted job directory")
            except Exception as e:
                print(f"  ⚠️  Failed to delete directory: {e}")
        
        # 3. Delete from database
        db.delete(job)
    
    # Commit all deletions
    db.commit()
    print()
    print(f"✅ Successfully deleted {len(jobs)} jobs for {domain}!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()

