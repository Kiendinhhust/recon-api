"""
Celery application configuration
"""
from celery import Celery

from app.deps import settings

# Create Celery instance
celery_app = Celery(
    "recon_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"]
)

# Enhanced Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=45 * 60,  # 45 minutes for full scans
    task_soft_time_limit=40 * 60,  # 40 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,  # Lower to prevent memory issues
    task_acks_late=True,  # Acknowledge tasks only after completion
    worker_disable_rate_limits=False,
    task_reject_on_worker_lost=True,
    # Retry configuration
    task_default_retry_delay=60,
    task_max_retries=3,
    # Broker connection retry on startup (fixes deprecation warning)
    broker_connection_retry_on_startup=True,
)

# Enhanced task routing with specialized queues for different workloads
# This allows for dedicated workers to handle specific types of tasks
celery_app.conf.task_routes = {
    # Full reconnaissance scans (includes all stages)
    "app.workers.tasks.run_recon_scan": {"queue": "recon_full"},

    "app.workers.tasks.run_subdomain_enumeration": {"queue": "recon_enum"},
    "app.workers.tasks.run_live_host_check": {"queue": "recon_check"},
    "app.workers.tasks.run_screenshot_capture": {"queue": "recon_screenshot"},

    # Specialized detection tasks
    "app.workers.tasks.run_waf_check": {"queue": "waf_check"},
    "app.workers.tasks.run_sourceleakhacker_check": {"queue": "leak_check"},

    # Maintenance tasks
     "app.workers.tasks.cleanup_old_jobs": {"queue": "maintenance"},
}

# Queue priorities (higher number = higher priority)
celery_app.conf.task_queue_max_priority = 10
celery_app.conf.task_default_priority = 5
celery_app.conf.worker_direct = True

if __name__ == "__main__":
    celery_app.start()
