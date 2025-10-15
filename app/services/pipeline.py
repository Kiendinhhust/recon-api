"""
Pipeline service for orchestrating reconnaissance tools
"""
import os
import asyncio
import subprocess
import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from app.deps import settings
from app.services.parsers import (
    SubfinderParser, AmassParser, AssetfinderParser,
    HttpxParser, GoWitnessParser, OutputCombiner
)

# Setup logging
logger = logging.getLogger(__name__)


class ReconPipeline:
    """Main reconnaissance pipeline with enhanced CLI tool integration"""

    def __init__(self, job_id: str, domain: str, progress_callback: Optional[Callable] = None):
        self.job_id = job_id
        self.domain = domain
        self.job_dir = Path(settings.jobs_directory) / job_id
        self.shots_dir = self.job_dir / "shots"
        self.progress_callback = progress_callback

        # Create job directories
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self.shots_dir.mkdir(parents=True, exist_ok=True)

        # File paths for pipeline stages
        self.subs_file = self.job_dir / "subs.txt"
        self.amass_file = self.job_dir / "amass.txt"
        self.live_file = self.job_dir / "live.txt"
        self.httprobe_file = self.job_dir / "httprobe.txt"
    
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """Run the complete reconnaissance pipeline with enhanced CLI integration"""
        results = {
            'job_id': self.job_id,
            'domain': self.domain,
            'subdomains': [],
            'live_hosts': [],
            'screenshots': [],
            'errors': [],
            'stats': {
                'total_subdomains': 0,
                'live_hosts': 0,
                'screenshots_taken': 0
            }
        }

        try:
            # Step 1: Subdomain enumeration (subfinder + amass + assetfinder)
            self._update_progress(10, "Starting subdomain enumeration...")
            logger.info(f"[{self.job_id}] Starting subdomain enumeration for {self.domain}")

            subdomains = await self.enumerate_subdomains_enhanced()
            results['subdomains'] = subdomains
            results['stats']['total_subdomains'] = len(subdomains)

            if not subdomains:
                results['errors'].append("No subdomains found")
                return results

            # Step 2: Live host detection (httprobe + httpx)
            self._update_progress(50, f"Checking live hosts for {len(subdomains)} subdomains...")
            logger.info(f"[{self.job_id}] Checking live hosts for {len(subdomains)} subdomains")

            live_hosts = await self.check_live_hosts_enhanced(subdomains)
            results['live_hosts'] = live_hosts
            results['stats']['live_hosts'] = len(live_hosts)

            if not live_hosts:
                results['errors'].append("No live hosts found")
                return results

            # Step 3: Screenshot capture (gowitness)
            self._update_progress(80, f"Capturing screenshots for {len(live_hosts)} live hosts...")
            logger.info(f"[{self.job_id}] Capturing screenshots for {len(live_hosts)} live hosts")

            screenshots = await self.capture_screenshots_enhanced(live_hosts)
            results['screenshots'] = screenshots
            results['stats']['screenshots_taken'] = len(screenshots)

            self._update_progress(100, "Pipeline completed successfully!")

        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(f"[{self.job_id}] {error_msg}")

        return results
    
    async def enumerate_subdomains_enhanced(self) -> List[str]:
        """Enhanced subdomain enumeration with proper CLI tool integration"""

        # Step 1: Run subfinder
        self._update_progress(15, "Running subfinder...")
        try:
            await self._run_subfinder_cli()
            logger.info(f"[{self.job_id}] Subfinder completed")
        except Exception as e:
            logger.error(f"[{self.job_id}] Subfinder error: {e}")

        # Step 2: Run amass (passive mode)
        self._update_progress(25, "Running amass...")
        try:
            await self._run_amass_cli()
            logger.info(f"[{self.job_id}] Amass completed")
        except Exception as e:
            logger.error(f"[{self.job_id}] Amass error: {e}")

        # Step 3: Run assetfinder and merge with anew
        self._update_progress(35, "Running assetfinder...")
        try:
            await self._run_assetfinder_cli()
            logger.info(f"[{self.job_id}] Assetfinder completed")
        except Exception as e:
            logger.error(f"[{self.job_id}] Assetfinder error: {e}")

        # Step 4: Read and return final subdomain list
        subdomains = await self._read_subdomains_file()
        self._update_progress(40, f"Found {len(subdomains)} unique subdomains")

        return subdomains
    
    async def check_live_hosts_enhanced(self, subdomains: List[str]) -> List[Dict[str, Any]]:
        """Enhanced live host detection with httprobe + httpx"""

        # Step 1: Quick live check with httprobe (optional, faster initial filter)
        self._update_progress(55, "Running httprobe for quick live check...")
        try:
            await self._run_httprobe_cli()
            logger.info(f"[{self.job_id}] Httprobe completed")
        except Exception as e:
            logger.warning(f"[{self.job_id}] Httprobe error (continuing with httpx): {e}")

        # Step 2: Detailed analysis with httpx
        self._update_progress(65, "Running httpx for detailed analysis...")
        try:
            await self._run_httpx_cli()
            logger.info(f"[{self.job_id}] Httpx completed")
        except Exception as e:
            logger.error(f"[{self.job_id}] Httpx error: {e}")
            return []

        # Step 3: Parse results
        live_hosts = await self._parse_live_results()
        self._update_progress(75, f"Found {len(live_hosts)} live hosts")

        return live_hosts
    
    async def capture_screenshots_enhanced(self, live_hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhanced screenshot capture using gowitness with file input"""
        try:
            # Step 1: Prepare URLs file for gowitness
            urls = [host['url'] for host in live_hosts]
            await self._prepare_urls_for_gowitness(urls)

            # Step 2: Run gowitness with file input
            self._update_progress(90, f"Capturing screenshots for {len(urls)} URLs...")
            await self._run_gowitness_cli()
            logger.info(f"[{self.job_id}] Gowitness completed")

            # Step 3: Parse screenshot results
            screenshots = await self._parse_screenshot_results()

            return screenshots
        except Exception as e:
            logger.error(f"[{self.job_id}] Gowitness error: {e}")
            return []
    
    # Enhanced CLI tool methods
    async def _run_subfinder_cli(self):
        """Run subfinder with direct file output"""
        cmd = [
            settings.subfinder_path,
            "-d", self.domain,
            "-silent",
            "-o", "subs.txt"  # Just filename since cwd is job_dir
        ]
        await self._run_command_with_logging(cmd, "subfinder")

    async def _run_amass_cli(self):
        """Run amass in passive mode with file output and filter only FQDNs"""
        # Run amass and save raw output
        amass_raw_file = self.job_dir / "amass_raw.txt"

        cmd = [
            settings.amass_path,
            "enum",
            "-passive",
            "-timeout", "10",
            "-d", self.domain,
            "-o", "amass_raw.txt"  # Just filename since cwd is job_dir
        ]
        await self._run_command_with_logging(cmd, "amass")

        # Filter and extract only FQDNs from amass output
        if amass_raw_file.exists():
            await self._filter_amass_output(amass_raw_file)

            # Merge filtered amass results with main subs file using anew (Windows-safe)
            if self.amass_file.exists():
                await self._merge_files_with_anew(self.amass_file, self.subs_file)

    async def _merge_files_with_anew(self, source_file: Path, target_file: Path):
        """Merge source file into target file using anew (Windows-safe)"""
        import subprocess

        # Read source file content
        with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Use anew via stdin to merge into target
        result = subprocess.run(
            [settings.anew_path, str(target_file)],
            input=content,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        logger.info(f"[{self.job_id}] Merged {source_file.name} into {target_file.name}")

    async def _merge_text_with_anew(self, text: str, target_file: Path):
        """Merge text content into target file using anew (Windows-safe)"""
        import subprocess

        result = subprocess.run(
            [settings.anew_path, str(target_file)],
            input=text,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        logger.debug(f"[{self.job_id}] Merged text into {target_file.name}")

    async def _filter_amass_output(self, raw_file: Path):
        """Filter amass output to extract only FQDNs"""
        import re

        fqdns = set()

        with open(raw_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Check if this is graph format (contains -->)
                if '-->' in line:
                    # Extract FQDN from graph format
                    # Pattern: "domain.com (FQDN) --> ..."
                    match = re.match(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\s+\(FQDN\)', line)
                    if match:
                        domain = line.split('(FQDN)')[0].strip().lower()
                        # Only add if it's a subdomain of target domain
                        if domain.endswith(self.domain):
                            fqdns.add(domain)
                else:
                    # Simple format - just domain names
                    parts = line.split()
                    if parts and '.' in parts[0]:
                        domain = parts[0].lower().strip()
                        if domain.endswith(self.domain):
                            fqdns.add(domain)

        # Write filtered FQDNs to amass output file
        with open(self.amass_file, 'w', encoding='utf-8') as f:
            for fqdn in sorted(fqdns):
                f.write(f"{fqdn}\n")

        logger.info(f"[{self.job_id}] Filtered {len(fqdns)} unique FQDNs from amass output")

    async def _run_assetfinder_cli(self):
        """Run assetfinder and merge with anew (Windows-safe)"""
        # Run assetfinder to get output
        import subprocess
        result = subprocess.run(
            [settings.assetfinder_path, "--subs-only", self.domain],
            capture_output=True,
            text=True,
            timeout=settings.assetfinder_timeout,
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode == 0 and result.stdout:
            # Merge with existing subs using anew via stdin
            await self._merge_text_with_anew(result.stdout, self.subs_file)
            logger.info(f"[{self.job_id}] Assetfinder completed")

    async def _run_httprobe_cli(self):
        """Run httprobe for quick live check (Windows-safe)"""
        if not self.subs_file.exists():
            return

        # Read subs and pipe to httprobe via stdin
        import subprocess
        with open(self.subs_file, 'r', encoding='utf-8', errors='ignore') as f:
            subs_content = f.read()

        result = subprocess.run(
            [settings.httprobe_path],
            input=subs_content,
            capture_output=True,
            text=True,
            timeout=settings.httprobe_timeout,
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode == 0 and result.stdout:
            with open(self.httprobe_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            logger.info(f"[{self.job_id}] Httprobe completed")

    async def _run_httpx_cli(self):
        """Run httpx for detailed live host analysis (Windows-safe)"""
        if not self.subs_file.exists():
            return

        # Read subs and pipe to httpx via stdin
        import subprocess
        with open(self.subs_file, 'r', encoding='utf-8', errors='ignore') as f:
            subs_content = f.read()

        result = subprocess.run(
            [settings.httpx_path, "-silent", "-mc", "200,301,302,403,401", "-title", "-tech-detect", "-json"],
            input=subs_content,
            capture_output=True,
            text=True,
            timeout=settings.httpx_timeout,
            cwd=str(self.job_dir),
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode == 0 and result.stdout:
            with open(self.live_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            logger.info(f"[{self.job_id}] Httpx completed")

    async def _run_gowitness_cli(self):
        """Run gowitness for screenshot capture (v3.x compatible)"""
        urls_file = self.job_dir / "urls_for_gowitness.txt"
        if not urls_file.exists() or urls_file.stat().st_size == 0:
            logger.warning(f"[{self.job_id}] Skip gowitness: URLs file missing/empty")
            return

        # Ensure screenshots directory exists
        self.shots_dir.mkdir(exist_ok=True)

        # Count URLs
        with open(urls_file, 'r', encoding='utf-8') as f:
            url_count = len([line for line in f if line.strip()])

        logger.info(f"[{self.job_id}] Starting gowitness for {url_count} URLs")
        logger.info(f"[{self.job_id}] URLs file: {urls_file.resolve()}")
        logger.info(f"[{self.job_id}] Screenshots dir: {self.shots_dir.resolve()}")

        # Gowitness v3.x syntax: gowitness scan file -f <file> --screenshot-path <path>
        # Use absolute paths for Windows compatibility
        cmd = [
            settings.gowitness_path,
            "scan",
            "file",
            "-f", str(urls_file.resolve()),  # Absolute path
            "--screenshot-path", str(self.shots_dir.resolve()),  # Absolute path
            "--threads", "4",
            "--timeout", "30"
        ]

        logger.info(f"[{self.job_id}] Gowitness command: {' '.join(cmd)}")

        # Note: Don't set cwd for gowitness to avoid path issues
        import subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.gowitness_timeout,
            encoding='utf-8',
            errors='ignore'
        )

        # Log output
        if result.stdout:
            logger.info(f"[{self.job_id}] Gowitness stdout: {result.stdout[:1000]}")
        if result.stderr:
            logger.info(f"[{self.job_id}] Gowitness stderr: {result.stderr[:1000]}")

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            logger.error(f"[{self.job_id}] gowitness failed with code {result.returncode}: {error_msg[:500]}")
            # Don't raise - screenshots are optional
        else:
            # Count screenshots created
            screenshot_files = list(self.shots_dir.glob("*.png"))
            logger.info(f"[{self.job_id}] gowitness completed successfully - {len(screenshot_files)} screenshots captured")
    
    # Helper methods for file operations and parsing
    async def _read_subdomains_file(self) -> List[str]:
        """Read subdomains from file"""
        if not self.subs_file.exists():
            return []

        with open(self.subs_file, 'r', encoding='utf-8', errors='ignore') as f:
            subdomains = [line.strip() for line in f if line.strip()]

        return list(set(subdomains))  # Deduplicate

    async def _parse_live_results(self) -> List[Dict[str, Any]]:
        """Parse httpx JSON output"""
        if not self.live_file.exists():
            return []

        live_hosts = []
        with open(self.live_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    import json
                    data = json.loads(line)
                    live_hosts.append({
                        'url': data.get('url', ''),
                        'status_code': data.get('status_code'),
                        'response_time': data.get('response_time'),
                        'title': data.get('title', '').strip() if data.get('title') else None,
                        'tech': data.get('tech', []) if data.get('tech') else [],
                        'content_length': data.get('content_length'),
                        'final_url': data.get('final_url')
                    })
                except json.JSONDecodeError:
                    continue

        return live_hosts

    async def _prepare_urls_for_gowitness(self, urls: List[str]):
        """Prepare URLs file for gowitness input"""
        urls_file = self.job_dir / "urls_for_gowitness.txt"
        with open(urls_file, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")

        logger.info(f"[{self.job_id}] Prepared {len(urls)} URLs for gowitness: {urls_file}")

    async def _parse_screenshot_results(self) -> List[Dict[str, Any]]:
        """Parse gowitness v3.x results from screenshot files"""
        screenshots = []

        # Check if screenshots directory exists
        if not self.shots_dir.exists():
            logger.warning(f"[{self.job_id}] Screenshots directory does not exist: {self.shots_dir}")
            return []

        # List all screenshot image files (support nested folders and jpg/png)
        screenshot_files = list(self.shots_dir.rglob("*.png")) + list(self.shots_dir.rglob("*.jpg")) + list(self.shots_dir.rglob("*.jpeg"))

        if not screenshot_files:
            logger.warning(f"[{self.job_id}] No screenshot files found in {self.shots_dir}")
            return []

        logger.info(f"[{self.job_id}] Found {len(screenshot_files)} screenshot files")

        # Parse each screenshot file
        for screenshot_file in screenshot_files:
            try:
                # Gowitness v3.x filename format: <url-encoded>.png
                # Example: https-example-com.png
                filename = screenshot_file.name

                # Try to extract URL from filename
                # Remove .png extension
                url_part = filename.replace('.png', '')

                # Convert filename back to URL
                # https-example-com -> https://example.com
                if url_part.startswith('https-'):
                    url = 'https://' + url_part[6:].replace('-', '.')
                elif url_part.startswith('http-'):
                    url = 'http://' + url_part[5:].replace('-', '.')
                else:
                    url = url_part.replace('-', '.')

                screenshots.append({
                    'url': url,
                    'filename': filename,
                    'file_path': str(screenshot_file.relative_to(self.job_dir)),
                    'file_size': screenshot_file.stat().st_size
                })

            except Exception as e:
                logger.warning(f"[{self.job_id}] Error parsing screenshot {screenshot_file.name}: {e}")
                continue

        logger.info(f"[{self.job_id}] Parsed {len(screenshots)} screenshots")
        return screenshots
    
    async def _run_assetfinder(self):
        """Run assetfinder"""
        cmd = [settings.assetfinder_path, self.domain]
        output = await self._run_command(cmd)
        return AssetfinderParser.parse(output)
    
    async def _run_httpx(self, subdomains: List[str]):
        """Run httpx to check live hosts"""
        # Save subdomains to temp file
        subs_file = self.job_dir / "temp_subs.txt"
        with open(subs_file, 'w') as f:
            for sub in subdomains:
                f.write(f"{sub}\n")
        
        cmd = [
            settings.httpx_path,
            "-l", str(subs_file),
            "-json",
            "-silent",
            "-timeout", "10",
            "-retries", "2"
        ]
        
        output = await self._run_command(cmd)
        
        # Clean up temp file
        subs_file.unlink(missing_ok=True)
        
        return HttpxParser.parse(output)
    
    async def _run_gowitness(self, urls: List[str]):
        """Run gowitness to capture screenshots"""
        # Save URLs to temp file
        urls_file = self.job_dir / "temp_urls.txt"
        with open(urls_file, 'w') as f:
            for url in urls:
                f.write(f"{url}\n")
        
        db_file = self.shots_dir / "gowitness.db"
        
        cmd = [
            settings.gowitness_path,
            "file",
            "-f", str(urls_file),
            "-P", str(self.shots_dir),
            "--db", str(db_file),
            "--timeout", "15",
            "--delay", "3"
        ]
        
        await self._run_command(cmd)
        
        # Parse results from database
        screenshots = []
        if db_file.exists():
            db_results = GoWitnessParser.parse_db_output(str(db_file))
            for result in db_results:
                if result['filename']:
                    screenshots.append({
                        'url': result['url'],
                        'filename': result['filename'],
                        'status_code': result['status_code'],
                        'title': result['title']
                    })
        
        # Clean up temp file
        urls_file.unlink(missing_ok=True)
        
        return screenshots
    
    # Enhanced command execution methods
    async def _run_command_with_logging(self, cmd: List[str], tool_name: str, timeout: int = 1900) -> str:
        """Run a command with enhanced logging and progress tracking (Windows compatible)"""
        try:
            logger.info(f"[{self.job_id}] Starting {tool_name}: {' '.join(cmd)}")
            logger.info(f"[{self.job_id}] Working directory: {self.job_dir}")
            logger.info(f"[{self.job_id}] Command executable: {cmd[0]}")

            # Check if executable exists
            import os
            if not os.path.exists(cmd[0]):
                raise FileNotFoundError(f"Tool not found: {cmd[0]}")

            # Use synchronous subprocess for Windows compatibility
            import subprocess

            result = subprocess.run(
                cmd,
                cwd=str(self.job_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )

            # Log output
            if result.stdout:
                logger.debug(f"[{self.job_id}] {tool_name} stdout: {result.stdout[:500]}")
            if result.stderr:
                logger.debug(f"[{self.job_id}] {tool_name} stderr: {result.stderr[:500]}")

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"[{self.job_id}] {tool_name} failed with code {result.returncode}: {error_msg[:500]}")
                raise Exception(f"{tool_name} failed: {error_msg[:200]}")

            logger.info(f"[{self.job_id}] {tool_name} completed successfully")
            return result.stdout

        except subprocess.TimeoutExpired:
            logger.error(f"[{self.job_id}] {tool_name} timed out after {timeout} seconds")
            raise Exception(f"{tool_name} timed out")
        except FileNotFoundError as e:
            logger.error(f"[{self.job_id}] {tool_name} executable not found: {str(e)}")
            raise Exception(f"{tool_name} not found: {str(e)}")
        except PermissionError as e:
            logger.error(f"[{self.job_id}] {tool_name} permission denied: {str(e)}")
            raise Exception(f"{tool_name} permission denied: {str(e)}")
        except Exception as e:
            logger.error(f"[{self.job_id}] {tool_name} execution error: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"[{self.job_id}] Traceback: {traceback.format_exc()}")
            raise

    async def _run_shell_command(self, cmd: str, tool_name: str, timeout: int = 600) -> str:
        """Run a shell command with pipes (Windows compatible)"""
        try:
            logger.info(f"[{self.job_id}] Starting {tool_name}: {cmd}")

            # Use synchronous subprocess for Windows compatibility
            import subprocess

            result = subprocess.run(
                cmd,
                shell=True,
                cwd=str(self.job_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"[{self.job_id}] {tool_name} failed: {error_msg[:500]}")
                raise Exception(f"{tool_name} failed: {error_msg[:200]}")

            logger.info(f"[{self.job_id}] {tool_name} completed successfully")
            return result.stdout

        except subprocess.TimeoutExpired:
            logger.error(f"[{self.job_id}] {tool_name} timed out")
            raise Exception(f"{tool_name} timed out")
        except Exception as e:
            logger.error(f"[{self.job_id}] {tool_name} error: {str(e)}")
            raise
    
    def _update_progress(self, percentage: int, message: str):
        """Update progress via callback"""
        if self.progress_callback:
            self.progress_callback(percentage, message)
        logger.info(f"[{self.job_id}] Progress {percentage}%: {message}")

    async def _save_subdomains(self, subdomains: List[str]):
        """Save subdomains to file"""
        with open(self.subs_file, 'w') as f:
            for sub in sorted(subdomains):
                f.write(f"{sub}\n")

    async def _save_live_hosts(self, live_hosts: List[str]):
        """Save live hosts to file"""
        with open(self.live_file, 'w') as f:
            for host in sorted(live_hosts):
                f.write(f"{host}\n")
