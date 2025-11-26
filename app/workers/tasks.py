"""
Celery tasks for background processing
"""
import asyncio
from typing import Dict, Any, List, Optional

from celery import current_task
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.deps import SessionLocal, settings
from app.services.pipeline import ReconPipeline
from app.storage.repo import ScanJobRepository, SubdomainRepository, ScreenshotRepository, WafDetectionRepository, LeakDetectionRepository, TechnologyRepository
from app.storage.models import ScanJob, ScanStatus, SubdomainStatus


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_recon_scan(self, job_id: str, domain: str) -> Dict[str, Any]:
    """
    Enhanced main task to run reconnaissance scan with retry logic
    """
    db = SessionLocal()
    try:
        # Update job status to running
        scan_repo = ScanJobRepository(db)
        scan_repo.update_scan_status(job_id, ScanStatus.RUNNING)

        # Progress callback function
        def progress_callback(percentage: int, message: str):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': percentage,
                    'total': 100,
                    'status': message,
                    'job_id': job_id,
                    'domain': domain
                }
            )

        # Update initial progress
        progress_callback(0, 'Initializing reconnaissance pipeline...')

        # Run the enhanced pipeline
        pipeline = ReconPipeline(job_id, domain, progress_callback)

        # Use asyncio to run the async pipeline
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            results = loop.run_until_complete(pipeline.run_full_pipeline())
        finally:
            loop.close()

        # Save results to database
        scan_job = scan_repo.get_scan_job(job_id)
        if scan_job:
            # Save subdomains
            subdomain_repo = SubdomainRepository(db)
            screenshot_repo = ScreenshotRepository(db)

            # Update progress
            progress_callback(95, 'Saving results to database...')

            # Save discovered subdomains
            if results.get('subdomains'):
                subdomain_repo.bulk_create_subdomains(
                    scan_job.id,
                    results['subdomains'],
                    discovered_by="enhanced_pipeline"
                )

            # Update all hosts (both live and dead) with their status codes and httpx data
            if results.get('live_hosts'):
                tech_repo = TechnologyRepository(db)

                for live_host in results['live_hosts']:
                    # Extract domain from URL
                    url = live_host['url']
                    domain_part = url.replace('http://', '').replace('https://', '').split('/')[0]

                    # Find corresponding subdomain and update it
                    subdomains = subdomain_repo.get_subdomains_by_job(job_id)
                    for subdomain in subdomains:
                        if subdomain.subdomain == domain_part:
                            # Determine status based on is_live flag
                            status = SubdomainStatus.LIVE if live_host.get('is_live') else SubdomainStatus.DEAD

                            # Update subdomain with all httpx fields
                            subdomain_repo.update_subdomain_status(
                                subdomain.id,
                                status,
                                is_live=live_host.get('is_live', False),
                                http_status=live_host.get('status_code'),
                                response_time=live_host.get('response_time'),
                                url=live_host.get('url'),
                                title=live_host.get('title'),
                                content_length=live_host.get('content_length'),
                                webserver=live_host.get('webserver'),
                                final_url=live_host.get('final_url'),
                                cdn_name=live_host.get('cdn_name'),
                                content_type=live_host.get('content_type'),
                                host=live_host.get('host'),
                                chain_status_codes=live_host.get('chain_status_codes'),
                                ipv4_addresses=live_host.get('ipv4_addresses'),
                                ipv6_addresses=live_host.get('ipv6_addresses')
                            )

                            # Save technologies to separate table
                            technologies = live_host.get('technologies', [])
                            if technologies:
                                tech_repo.bulk_create_technologies(subdomain.id, technologies)

                            break

            # Save screenshots
            if results.get('screenshots'):
                for screenshot in results['screenshots']:
                    # Find corresponding subdomain
                    url = screenshot['url']
                    domain_part = url.replace('http://', '').replace('https://', '').split('/')[0]

                    subdomain_id = None
                    subdomains = subdomain_repo.get_subdomains_by_job(job_id)
                    for subdomain in subdomains:
                        if subdomain.subdomain == domain_part:
                            subdomain_id = subdomain.id
                            break

                    # Create screenshot record
                    # Build correct file_path; prefer parser-provided relative path if available
                    file_path = screenshot.get('file_path') if isinstance(screenshot, dict) else None
                    if file_path:
                        # Normalize and ensure it is rooted under jobs/{job_id}
                        # If already starts with jobs/, keep as-is; else prefix with jobs/{job_id}/
                        norm_path = str(file_path).replace('\\', '/').lstrip('/')
                        if norm_path.startswith('jobs/'):
                            final_path = norm_path
                        else:
                            final_path = f"jobs/{job_id}/{norm_path}"
                    else:
                        # Fallback: assume flat shots directory
                        final_path = f"jobs/{job_id}/shots/{screenshot['filename']}"

                    screenshot_repo.create_screenshot(
                        scan_job_id=scan_job.id,
                        url=screenshot['url'],
                        filename=screenshot['filename'],
                        file_path=final_path,
                        subdomain_id=subdomain_id,
                        file_size=screenshot.get('file_size') if isinstance(screenshot, dict) else None
                    )

            # Save WAF detections
            if results.get('waf_detections'):
                waf_repo = WafDetectionRepository(db)
                waf_repo.bulk_create(scan_job.id, results['waf_detections'])

            # Save leak detections
            if results.get('leak_detections'):
                leak_repo = LeakDetectionRepository(db)
                leak_repo.bulk_create(scan_job.id, results['leak_detections'])

        # Update job status to completed
        if results.get('errors'):
            error_message = '; '.join(results['errors'])
            scan_repo.update_scan_status(job_id, ScanStatus.FAILED, error_message)
        else:
            scan_repo.update_scan_status(job_id, ScanStatus.COMPLETED)

        # Final progress update
        final_stats = results.get('stats', {})
        self.update_state(
            state='SUCCESS',
            meta={
                'current': 100,
                'total': 100,
                'status': 'Reconnaissance scan completed successfully!',
                'job_id': job_id,
                'domain': domain,
                'stats': final_stats,
                'results': {
                    'subdomains_found': final_stats.get('total_subdomains', 0),
                    'live_hosts_found': final_stats.get('live_hosts', 0),
                    'screenshots_taken': final_stats.get('screenshots_taken', 0)
                }
            }
        )

        return {
            'job_id': job_id,
            'domain': domain,
            'status': 'completed',
            'stats': final_stats,
            'errors': results.get('errors', [])
        }

    except Exception as e:
        # Check if this is a retryable error
        if self.request.retries < self.max_retries:
            # Log retry attempt
            import logging
            logging.warning(f"Scan {job_id} failed, retrying ({self.request.retries + 1}/{self.max_retries}): {str(e)}")

            # Update progress to show retry
            self.update_state(
                state='RETRY',
                meta={
                    'current': 0,
                    'total': 100,
                    'status': f'Retrying scan... (attempt {self.request.retries + 1}/{self.max_retries})',
                    'error': str(e)
                }
            )

            # Retry the task
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        # Max retries exceeded, mark as failed
        scan_repo = ScanJobRepository(db)
        scan_repo.update_scan_status(job_id, ScanStatus.FAILED, str(e))

        self.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': 100,
                'status': f'Scan failed after {self.max_retries} retries: {str(e)}',
                'job_id': job_id,
                'domain': domain,
                'error': str(e)
            }
        )

        raise e

    finally:
        db.close()


@celery_app.task(bind=True)
def run_subdomain_enumeration(self, job_id: str, domain: str) -> Dict[str, Any]:
    """
    Task to run only subdomain enumeration stage
    """
    try:
        def progress_callback(percentage: int, message: str):
            self.update_state(
                state='PROGRESS',
                meta={'current': percentage, 'total': 100, 'status': message}
            )

        pipeline = ReconPipeline(job_id, domain, progress_callback)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            subdomains = loop.run_until_complete(pipeline.enumerate_subdomains_enhanced())
            return {
                'job_id': job_id,
                'domain': domain,
                'subdomains': subdomains,
                'count': len(subdomains)
            }
        finally:
            loop.close()

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Subdomain enumeration failed: {str(e)}'}
        )
        raise


@celery_app.task(bind=True)
def run_live_host_check(self, job_id: str, domain: str, subdomains: List[str]) -> Dict[str, Any]:
    """
    Task to run only live host checking stage
    """
    try:
        def progress_callback(percentage: int, message: str):
            self.update_state(
                state='PROGRESS',
                meta={'current': percentage, 'total': 100, 'status': message}
            )

        pipeline = ReconPipeline(job_id, domain, progress_callback)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            live_hosts = loop.run_until_complete(pipeline.check_live_hosts_enhanced(subdomains))
            return {
                'job_id': job_id,
                'domain': domain,
                'live_hosts': live_hosts,
                'count': len(live_hosts)
            }
        finally:
            loop.close()

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Live host check failed: {str(e)}'}
        )
        raise


@celery_app.task(bind=True)
def run_screenshot_capture(self, job_id: str, domain: str, live_hosts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Task to run only screenshot capture stage
    """
    try:
        def progress_callback(percentage: int, message: str):
            self.update_state(
                state='PROGRESS',
                meta={'current': percentage, 'total': 100, 'status': message}
            )

        pipeline = ReconPipeline(job_id, domain, progress_callback)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            screenshots = loop.run_until_complete(pipeline.capture_screenshots_enhanced(live_hosts))
            return {
                'job_id': job_id,
                'domain': domain,
                'screenshots': screenshots,
                'count': len(screenshots)
            }
        finally:
            loop.close()

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Screenshot capture failed: {str(e)}'}
        )
        raise


@celery_app.task
def cleanup_old_jobs(days_old: int = 7) -> Dict[str, Any]:
    """
    Cleanup old scan jobs and their files
    """
    import shutil
    from datetime import datetime, timedelta
    from pathlib import Path

    db = SessionLocal()
    try:
        scan_repo = ScanJobRepository(db)

        # Find old jobs
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        old_jobs = db.query(ScanJob).filter(ScanJob.created_at < cutoff_date).all()

        cleaned_count = 0
        for job in old_jobs:
            # Remove job directory
            job_dir = Path(settings.jobs_directory) / job.job_id
            if job_dir.exists():
                shutil.rmtree(job_dir)

            # Remove from database
            db.delete(job)
            cleaned_count += 1

        db.commit()

        return {
            'status': 'completed',
            'cleaned_jobs': cleaned_count,
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()



@celery_app.task(bind=True)
def run_waf_check(self, job_id: str, domain: str, live_hosts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Task to run WAF detection stage on live hosts

    This task is dedicated to WAF detection and can be run independently
    or as part of the full reconnaissance pipeline.
    """
    db = SessionLocal()
    try:
        def progress_callback(percentage: int, message: str):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': percentage,
                    'total': 100,
                    'status': message,
                    'job_id': job_id,
                    'domain': domain
                }
            )

        progress_callback(10, 'Initializing WAF detection...')

        # Create pipeline instance
        pipeline = ReconPipeline(job_id, domain, progress_callback)

        # Run asyncio event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Prepare live URLs file
            urls = [host['url'] for host in live_hosts]
            with open(pipeline.live_urls_file, 'w', encoding='utf-8') as f:
                for url in urls:
                    f.write(f"{url}\n")

            progress_callback(50, f'Running wafw00f on {len(urls)} URLs...')

            # Run WAF detection
            waf_detections = loop.run_until_complete(pipeline._run_wafw00f_cli(live_hosts))

            progress_callback(90, 'Saving WAF detection results...')

            # Save WAF detections to database
            if waf_detections:
                scan_repo = ScanJobRepository(db)
                scan_job = scan_repo.get_scan_job(job_id)
                if scan_job:
                    waf_repo = WafDetectionRepository(db)
                    waf_repo.bulk_create(scan_job.id, waf_detections)

            progress_callback(100, 'WAF detection completed successfully!')

            return {
                'job_id': job_id,
                'domain': domain,
                'status': 'completed',
                'waf_detections': waf_detections,
                'count': len(waf_detections)
            }

        finally:
            loop.close()

    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={
                'status': f'WAF detection failed: {str(e)}',
                'job_id': job_id,
                'domain': domain,
                'error': str(e)
            }
        )
        raise
    finally:
        db.close()


# OLD FUNCTION REMOVED: The old run_sourceleakhacker_check function that was used
# for full pipeline has been deleted because:
# 1. It was a duplicate function name (Python overwrites the first definition)
# 2. SourceLeakHacker has been removed from the full pipeline
# 3. Only the selective scanning version (below) should be used

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_sourceleakhacker_check(self, job_id: str, selected_urls: List[str], mode: str = "tiny") -> Dict[str, Any]:
    db = SessionLocal()

    try:
        # Get scan job from database
        scan_repo = ScanJobRepository(db)
        scan_job = scan_repo.get_scan_job(job_id)

        if not scan_job:
            raise ValueError(f"Scan job {job_id} not found")

        domain = scan_job.domain

        # Progress callback function
        def progress_callback(percentage: int, message: str):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': percentage,
                    'total': 100,
                    'status': message,
                    'job_id': job_id,
                    'domain': domain,
                    'urls_scanned': len(selected_urls),
                    'mode': mode
                }
            )

        # Update initial progress
        progress_callback(0, f'Starting leak scan on {len(selected_urls)} URLs in {mode} mode...')

        # Create pipeline instance
        pipeline = ReconPipeline(job_id, domain, progress_callback)

        # Use asyncio to run the async method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            progress_callback(20, 'Running SourceLeakHacker...')

            # Create minimal live_hosts structure from selected URLs
            live_hosts = [{'url': url} for url in selected_urls]

            # Run SourceLeakHacker with selected URLs
            leak_detections = loop.run_until_complete(
                pipeline._run_sourceleakhacker_cli(
                    live_hosts=live_hosts,
                    waf_detections=[],  # No WAF filtering for selective scans
                    mode=mode,
                    selected_urls=selected_urls
                )
            )

            progress_callback(70, f'Saving {len(leak_detections)} leak detections to database...')

            # Save leak detections to database
            if leak_detections:
                leak_repo = LeakDetectionRepository(db)
                leak_repo.bulk_create(scan_job.id, leak_detections)
                # Note: ScanJob model doesn't have leaks_found column
                # Leak count can be queried from leak_detections relationship

            progress_callback(100, f'Leak scan completed! Found {len(leak_detections)} leaks.')

            return {
                'job_id': job_id,
                'domain': domain,
                'status': 'completed',
                'urls_scanned': len(selected_urls),
                'leaks_found': len(leak_detections),
                'mode': mode,
                'message': f'Scanned {len(selected_urls)} URLs in {mode} mode, found {len(leak_detections)} leaks'
            }

        finally:
            loop.close()

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)

        # Determine if this is a retryable error
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            OSError,  # Includes network and file system errors
        )

        is_retryable = isinstance(e, retryable_errors)

        # Check if we should retry
        if is_retryable and self.request.retries < self.max_retries:
            # Log retry attempt
            logger.warning(
                f"Leak scan {job_id} failed (attempt {self.request.retries + 1}/{self.max_retries}): {str(e)}"
            )

            # Update state to show retry
            self.update_state(
                state='RETRY',
                meta={
                    'current': 0,
                    'total': 100,
                    'status': f'Retrying leak scan... (attempt {self.request.retries + 1}/{self.max_retries})',
                    'job_id': job_id,
                    'urls_scanned': len(selected_urls),
                    'mode': mode,
                    'error': str(e),
                    'retry_count': self.request.retries + 1
                }
            )

            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        # Non-retryable error or max retries exceeded
        logger.error(f"Leak scan {job_id} failed permanently: {str(e)}", exc_info=True)

        # For non-retryable errors, we need to let Celery handle the exception
        # Don't call update_state before raising - it causes serialization issues
        # Instead, just re-raise and let Celery's default error handling work
        raise

    finally:
        db.close()
