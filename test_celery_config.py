#!/usr/bin/env python
"""
Test script to verify Celery configuration and task routing
"""
import sys
from app.workers.celery_app import celery_app
from app.workers.tasks import (
    run_recon_scan,
    run_subdomain_enumeration,
    run_live_host_check,
    run_screenshot_capture,
    run_waf_check,
    run_sourceleakhacker_check,
    cleanup_old_jobs
)

def test_celery_config():
    """Test Celery configuration"""
    print("=" * 60)
    print("Testing Celery Configuration")
    print("=" * 60)
    print()

    # Test 1: Check broker connection
    print("[1/5] Testing Redis broker connection...")
    try:
        with celery_app.connection() as conn:
            conn.connect()
        print("✓ Redis broker connection successful")
    except Exception as e:
        print(f"✗ Redis broker connection failed: {e}")
        return False
    print()

    # Test 2: Check task registration
    print("[2/5] Checking registered tasks...")
    registered_tasks = celery_app.tasks
    expected_tasks = [
        'app.workers.tasks.run_recon_scan',
        'app.workers.tasks.run_subdomain_enumeration',
        'app.workers.tasks.run_live_host_check',
        'app.workers.tasks.run_screenshot_capture',
        'app.workers.tasks.run_waf_check',
        'app.workers.tasks.run_sourceleakhacker_check',
        'app.workers.tasks.cleanup_old_jobs',
    ]
    
    for task in expected_tasks:
        if task in registered_tasks:
            print(f"✓ {task}")
        else:
            print(f"✗ {task} NOT FOUND")
            return False
    print()

    # Test 3: Check task routing
    print("[3/5] Checking task routing configuration...")
    task_routes = celery_app.conf.task_routes
    
    expected_routes = {
        'app.workers.tasks.run_recon_scan': 'recon_full',
        'app.workers.tasks.run_subdomain_enumeration': 'recon_full',
        'app.workers.tasks.run_live_host_check': 'recon_full',
        'app.workers.tasks.run_screenshot_capture': 'recon_full',
        'app.workers.tasks.run_waf_check': 'waf_check',
        'app.workers.tasks.run_sourceleakhacker_check': 'leak_check',
        'app.workers.tasks.cleanup_old_jobs': 'recon_full',
    }
    
    for task, expected_queue in expected_routes.items():
        if task in task_routes:
            actual_queue = task_routes[task].get('queue')
            if actual_queue == expected_queue:
                print(f"✓ {task} → {actual_queue}")
            else:
                print(f"✗ {task} → {actual_queue} (expected {expected_queue})")
                return False
        else:
            print(f"✗ {task} NOT IN ROUTES")
            return False
    print()

    # Test 4: Check Celery configuration
    print("[4/5] Checking Celery configuration...")
    config_checks = [
        ('task_serializer', 'json'),
        ('result_serializer', 'json'),
        ('accept_content', ['json']),
        ('timezone', 'UTC'),
        ('enable_utc', True),
        ('task_track_started', True),
        ('task_acks_late', True),
    ]
    
    for config_key, expected_value in config_checks:
        actual_value = celery_app.conf.get(config_key)
        if actual_value == expected_value:
            print(f"✓ {config_key} = {actual_value}")
        else:
            print(f"✗ {config_key} = {actual_value} (expected {expected_value})")
            return False
    print()

    # Test 5: Check pool configuration
    print("[5/5] Checking pool configuration...")
    print(f"✓ Task time limit: {celery_app.conf.task_time_limit} seconds")
    print(f"✓ Task soft time limit: {celery_app.conf.task_soft_time_limit} seconds")
    print(f"✓ Worker prefetch multiplier: {celery_app.conf.worker_prefetch_multiplier}")
    print(f"✓ Worker max tasks per child: {celery_app.conf.worker_max_tasks_per_child}")
    print()

    return True

def main():
    """Main test function"""
    print()
    success = test_celery_config()
    print()
    print("=" * 60)
    if success:
        print("✓ All Celery configuration tests PASSED!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Start Redis: redis-server")
        print("2. Start API: python -m uvicorn app.main:app --reload")
        print("3. Start workers: start_workers.bat")
        print("4. Monitor: http://localhost:5555 (Flower)")
        print()
        return 0
    else:
        print("✗ Some Celery configuration tests FAILED!")
        print("=" * 60)
        print()
        print("Please check the errors above and fix the configuration.")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())

