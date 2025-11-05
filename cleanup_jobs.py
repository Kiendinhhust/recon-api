"""
Script to cleanup running jobs for example.com
"""
from app.deps import SessionLocal
from app.storage.models import ScanJob, ScanStatus
from app.workers.celery_app import celery_app
import shutil
from pathlib import Path

db = SessionLocal()

try:
    # Find all jobs for example.com
    jobs = db.query(ScanJob).filter(ScanJob.domain == 'example.com').all()
    
    print(f"Found {len(jobs)} jobs for example.com:")
    print()
    
    for job in jobs:
        print(f"Job ID: {job.job_id}")
        print(f"  Status: {job.status}")
        print(f"  Created: {job.created_at}")
        print(f"  Task ID: {job.task_id}")
        print()
    
    if not jobs:
        print("No jobs found for example.com")
        exit(0)
    
    # Ask for confirmation
    response = input(f"\nDo you want to delete all {len(jobs)} jobs? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        exit(0)
    
    print()
    print("Deleting jobs...")
    print()
    
    for job in jobs:
        print(f"Deleting job {job.job_id}...")
        
        # 1. Revoke Celery task if running
        if job.task_id:
            try:
                celery_app.control.revoke(job.task_id, terminate=True)
                print(f"  ✅ Revoked Celery task {job.task_id}")
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
        try:
            db.delete(job)
            print(f"  ✅ Deleted from database")
        except Exception as e:
            print(f"  ⚠️  Failed to delete from database: {e}")
        
        print()
    
    # Commit all deletions
    db.commit()
    print(f"✅ Successfully deleted {len(jobs)} jobs!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()

