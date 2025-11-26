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

    def __init__(self, job_id: str, domain: str, progress_callback: Optional[Callable] = None, amass_config: dict = None):
        self.job_id = job_id
        self.domain = domain
        self.job_dir = Path(settings.jobs_directory) / job_id
        self.shots_dir = self.job_dir / "shots"
        self.progress_callback = progress_callback

        # Amass configuration
        self.amass_config = amass_config or {
            "mode": "passive",
            "timeout": 30,
            "max_dns_queries": 40,
            "use_wordlist": False
        }

        # Create job directories
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self.shots_dir.mkdir(parents=True, exist_ok=True)

        # File paths for pipeline stages
        self.subs_file = self.job_dir / "subs.txt"
        self.amass_file = self.job_dir / "amass.txt"
        self.live_file = self.job_dir / "live.txt"
        self.httprobe_file = self.job_dir / "httprobe.txt"
        # WAF and leak detection files
        self.live_urls_file = self.job_dir / "live_urls.txt"
        self.waf_results_file = self.job_dir / "waf_results.json"
        self.urls_no_waf_file = self.job_dir / "urls_no_waf.txt"
        self.leaks_output_dir = self.job_dir / "leaks_results"
    
    async def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete reconnaissance pipeline with enhanced CLI integration

        Pipeline Steps (4 steps total):
        1. Subdomain enumeration (subfinder + amass + assetfinder)
        2. Live host detection (httprobe + httpx)
        3. WAF detection (wafw00f)
        4. Screenshot capture (gowitness)

        NOTE: Source leak detection (SourceLeakHacker) has been REMOVED from the full pipeline.
        Use the selective scanning API endpoint instead: POST /api/v1/scans/{job_id}/leak-scan
        """
        results = {
            'job_id': self.job_id,
            'domain': self.domain,
            'subdomains': [],
            'live_hosts': [],
            'screenshots': [],
            'waf_detections': [],
            'leak_detections': [],  # Will be empty - use selective scanning API instead
            'errors': [],
            'stats': {
                'total_subdomains': 0,
                'live_hosts': 0,
                'screenshots_taken': 0,
                'waf_protected': 0,
                'leaks_found': 0  # Will be 0 - use selective scanning API instead
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
            self._update_progress(40, f"Checking live hosts for {len(subdomains)} subdomains...")
            logger.info(f"[{self.job_id}] Checking live hosts for {len(subdomains)} subdomains")

            live_hosts = await self.check_live_hosts_enhanced(subdomains)
            results['live_hosts'] = live_hosts
            results['stats']['live_hosts'] = len(live_hosts)

            if not live_hosts:
                results['errors'].append("No live hosts found")
                return results

            # Step 3: WAF detection (wafw00f)
            self._update_progress(70, "Detecting WAFs with wafw00f...")
            logger.info(f"[{self.job_id}] Running WAF detection on {len(live_hosts)} live hosts")
            waf_detections = []
            try:
                waf_detections = await self._run_wafw00f_cli(live_hosts)
                results['waf_detections'] = waf_detections
                results['stats']['waf_protected'] = len([w for w in waf_detections if w.get('has_waf')])

                # Filter out WAF-protected URLs
                waf_urls = {w.get('url') for w in waf_detections if w.get('has_waf')}
                non_waf_hosts = [h for h in live_hosts if h.get('url') not in waf_urls]

                logger.info(f"[{self.job_id}] WAF detection: {len(waf_urls)} WAF-protected, {len(non_waf_hosts)} non-WAF")
            except Exception as e:
                logger.warning(f"[{self.job_id}] WAF detection failed: {e}")
                results['errors'].append(f"WAF detection error: {str(e)}")
                non_waf_hosts = live_hosts  # Fallback to all hosts if WAF detection fails

            # Step 4: Screenshot capture (gowitness)
            self._update_progress(85, f"Capturing screenshots for {len(live_hosts)} live hosts...")
            logger.info(f"[{self.job_id}] Capturing screenshots for {len(live_hosts)} live hosts")

            screenshots = await self.capture_screenshots_enhanced(live_hosts)
            results['screenshots'] = screenshots
            results['stats']['screenshots_taken'] = len(screenshots)

            # Pipeline completed - 4 steps only
            # For leak detection, use the selective scanning API: POST /api/v1/scans/{job_id}/leak-scan
            self._update_progress(100, "Pipeline completed successfully! (4/4 steps)")
            logger.info(f"[{self.job_id}] Full pipeline completed. Use selective scanning API for leak detection.")

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

        # Step 2: Run amass with configured mode
        amass_mode = self.amass_config.get("mode", "passive")
        self._update_progress(25, f"Running amass ({amass_mode} mode)...")
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
        """Enhanced live host detection with httpx (httprobe removed for optimization)"""

        # Run httpx for comprehensive live host analysis
        self._update_progress(55, "Running httpx for live host detection and analysis...")
        try:
            await self._run_httpx_cli()
            logger.info(f"[{self.job_id}] Httpx completed")
        except Exception as e:
            logger.error(f"[{self.job_id}] Httpx error: {e}")
            return []

        # Parse httpx JSON results
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
        """Run amass with configurable mode, timeout, and options"""
        # Run amass and save raw output
        amass_raw_file = self.job_dir / "amass_raw.txt"

        # Build base command
        cmd = [
            settings.amass_path,
            "enum",
            "-d", self.domain,
        ]

        # Add mode flag (passive or active)
        mode = self.amass_config.get("mode", "passive")
        if mode == "active":
            cmd.append("-active")
        else:
            cmd.append("-passive")

        # Add timeout (in minutes)
        timeout = self.amass_config.get("timeout", 30)
        cmd.extend(["-timeout", str(timeout)])

        # Add active mode specific options
        if mode == "active":
            # Add max DNS queries
            max_dns_queries = self.amass_config.get("max_dns_queries", 40)
            cmd.extend(["-max-dns-queries", str(max_dns_queries)])

            # Add config file for deep scan (use absolute path)
            # Get project root directory (3 levels up from this file: app/services/pipeline.py -> app/services -> app -> root)
            project_root = Path(__file__).parent.parent.parent
            config_file = project_root / "config" / "deep_scan.yaml"
            if config_file.exists():
                cmd.extend(["-config", str(config_file.resolve())])
                logger.info(f"[{self.job_id}] Using Amass config file: {config_file.resolve()}")
            else:
                logger.warning(f"[{self.job_id}] Amass config file not found: {config_file.resolve()}")

            # Add wordlist if enabled (use absolute path)
            use_wordlist = self.amass_config.get("use_wordlist", False)
            if use_wordlist:
                wordlist_file = project_root / "wordlists" / "httparchive_subdomains_2025_10_27.txt"
                if wordlist_file.exists():
                    cmd.extend(["-w", str(wordlist_file.resolve())])
                    logger.info(f"[{self.job_id}] Using Amass wordlist: {wordlist_file.resolve()}")
                else:
                    logger.warning(f"[{self.job_id}] Wordlist file not found: {wordlist_file.resolve()}")

        # Add output file
        cmd.extend(["-o", "amass_raw.txt"])

        logger.info(f"[{self.job_id}] Running Amass with config: mode={mode}, timeout={timeout}min, max_dns_queries={self.amass_config.get('max_dns_queries', 40)}, use_wordlist={self.amass_config.get('use_wordlist', False)}")

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



    async def _run_httpx_cli(self):
        """Run httpx for detailed live host analysis (Windows-safe)"""
        if not self.subs_file.exists():
            return

        # Read subs and pipe to httpx via stdin
        import subprocess
        with open(self.subs_file, 'r', encoding='utf-8', errors='ignore') as f:
            subs_content = f.read()

        # Capture ALL status codes including 5xx errors
        # Added flags:
        # -retries 3: Retry failed requests up to 3 times (fixes domains that timeout on first attempt)
        # -timeout 30: Set timeout to 30 seconds per request
        # -follow-redirects: Follow HTTP redirects to get final status code
        result = subprocess.run(
            [
                settings.httpx_path,
                "-silent",
                "-title",
                "-tech-detect",
                "-json",
                "-retries", "3",
                "-timeout", "30",
                "-follow-redirects"
            ],
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
            logger.info(f"[{self.job_id}] Httpx completed with retries and follow-redirects enabled")

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

    async def _write_live_urls_file(self, live_hosts: List[Dict[str, Any]]):
        """Write live URLs to a file for wafw00f input"""
        urls = [h.get('url') for h in live_hosts if h.get('url')]
        urls = list(dict.fromkeys(urls))  # Deduplicate while preserving order

        with open(self.live_urls_file, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")

        logger.info(f"[{self.job_id}] Wrote {len(urls)} live URLs to {self.live_urls_file}")

    async def _run_wafw00f_cli(self, live_hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run wafw00f to detect WAF/CDN protection"""
        try:
            # Write live URLs to file
            await self._write_live_urls_file(live_hosts)

            if not self.live_urls_file.exists() or self.live_urls_file.stat().st_size == 0:
                logger.warning(f"[{self.job_id}] No live URLs to scan for WAF")
                return []

            # Run wafw00f
            cmd = [
                settings.wafw00f_path,
                "-i", str(self.live_urls_file.name),
                "-o", str(self.waf_results_file.name),
                "-f", "json"
            ]

            await self._run_command_with_logging(cmd, "wafw00f", timeout=getattr(settings, 'wafw00f_timeout', 900))

            # Parse wafw00f JSON output
            # wafw00f outputs JSON array format with fields: detected, firewall, manufacturer, url
            import json
            detections: List[Dict[str, Any]] = []

            if self.waf_results_file.exists():
                try:
                    with open(self.waf_results_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().strip()
                        if content:
                            try:
                                # wafw00f outputs a JSON array
                                data_list = json.loads(content)
                                if not isinstance(data_list, list):
                                    data_list = [data_list]

                                for data in data_list:
                                    if isinstance(data, dict):
                                        # Extract WAF name and manufacturer from wafw00f output
                                        firewall = data.get('firewall', 'None')
                                        manufacturer = data.get('manufacturer', 'None')

                                        # Only mark as WAF if detected is True and firewall is not "None"
                                        has_waf = data.get('detected', False) and firewall != 'None'

                                        detections.append({
                                            'url': data.get('url'),
                                            'has_waf': has_waf,
                                            'waf_name': firewall if firewall != 'None' else None,
                                            'waf_manufacturer': manufacturer if manufacturer != 'None' else None
                                        })
                            except json.JSONDecodeError as je:
                                logger.warning(f"[{self.job_id}] Failed to parse wafw00f JSON: {je}")
                except Exception as e:
                    logger.warning(f"[{self.job_id}] Failed to parse wafw00f results: {e}")

            logger.info(f"[{self.job_id}] WAF detection completed: {len(detections)} URLs analyzed")
            return detections

        except Exception as e:
            logger.error(f"[{self.job_id}] WAF detection error: {e}")
            raise

    async def _run_sourceleakhacker_cli(
        self,
        live_hosts: List[Dict[str, Any]],
        waf_detections: List[Dict[str, Any]],
        mode: Optional[str] = None,
        selected_urls: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Run SourceLeakHacker on non-WAF URLs to detect source code leaks

        Args:
            live_hosts: List of live host dictionaries
            waf_detections: List of WAF detection results
            mode: Override scan mode (tiny/full), defaults to settings.sourceleakhacker_mode
            selected_urls: Optional list of specific URLs to scan (for selective scanning)
        """
        try:
            # Filter out WAF-protected URLs
            waf_urls = {w.get('url') for w in waf_detections if w.get('has_waf')}
            non_waf_urls = [h.get('url') for h in live_hosts if h.get('url') not in waf_urls]

            # If selected_urls provided, filter to only those
            if selected_urls:
                non_waf_urls = [url for url in non_waf_urls if url in selected_urls]

            if not non_waf_urls:
                logger.info(f"[{self.job_id}] All URLs are WAF-protected, skipping leak detection")
                return []

            # Write non-WAF URLs to file
            with open(self.urls_no_waf_file, 'w', encoding='utf-8') as f:
                for url in non_waf_urls:
                    f.write(f"{url}\n")

            # Use override mode if provided, otherwise use settings
            scan_mode = mode or getattr(settings, 'sourceleakhacker_mode', 'tiny')

            logger.info(f"[{self.job_id}] Running SourceLeakHacker on {len(non_waf_urls)} non-WAF URLs (mode: {scan_mode})")

            # Create output directory
            self.leaks_output_dir.mkdir(parents=True, exist_ok=True)

            # Run SourceLeakHacker
            import subprocess
            from pathlib import Path

            # SourceLeakHacker needs to run from its own directory (for dict files)
            sourceleakhacker_dir = Path(settings.sourceleakhacker_path).parent

            # Convert paths to absolute paths since SourceLeakHacker runs from its own directory
            urls_file_absolute = Path(self.urls_no_waf_file).resolve()
            output_dir_absolute = Path(self.leaks_output_dir).resolve()

            cmd = [
                settings.python_executable,
                str(settings.sourceleakhacker_path),
                f"--urls={str(urls_file_absolute)}",  # Use absolute path
                f"--scale={scan_mode}",  # ADD: scale parameter for tiny/full mode
                "--output", str(output_dir_absolute),  # Use absolute path
                "--threads", str(getattr(settings, 'sourceleakhacker_threads', 8)),
                "--timeout", str(getattr(settings, 'sourceleakhacker_timeout', 2800))
            ]

            logger.info(f"[{self.job_id}] SourceLeakHacker command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=str(sourceleakhacker_dir),  # Changed to SourceLeakHacker directory
                capture_output=True,
                text=True,
                timeout=getattr(settings, 'sourceleakhacker_timeout', 2800),
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode != 0:
                logger.warning(f"[{self.job_id}] SourceLeakHacker returned code {result.returncode}: {result.stderr[:500]}")

            # Parse SourceLeakHacker results from STDOUT and CSV files
            leaks = await self._parse_sourceleakhacker_results(result.stdout)
            logger.info(f"[{self.job_id}] Leak detection completed: {len(leaks)} leaks found")
            return leaks

        except Exception as e:
            logger.error(f"[{self.job_id}] Source leak detection error: {e}")
            raise

    async def _parse_sourceleakhacker_results(self, stdout_output: str = "") -> List[Dict[str, Any]]:
        """Parse SourceLeakHacker results from STDOUT and CSV files

        Args:
            stdout_output: STDOUT output from SourceLeakHacker command

        Returns:
            List of leak detection dictionaries
        """
        results: List[Dict[str, Any]] = []

        # Parse STDOUT output first (real-time results)
        # Format: [CODE]  SIZE    TIME    CONTENT_TYPE    URL
        if stdout_output:
            logger.info(f"[{self.job_id}] Parsing SourceLeakHacker STDOUT output...")
            import re
            from urllib.parse import urlparse

            for line in stdout_output.splitlines():
                line = line.strip()
                # Parse ALL status codes, not just [200]
                # Format: [403] 0 0.07s text/html https://example.com/.htaccess
                match = re.match(r'\[(\d+)\]\s+(\d+)\s+([\d.]+)s?\s+(\S+)\s+(.+)', line)
                if match:
                    try:
                        http_status = int(match.group(1))

                        # Skip 404 status codes - these are "Not Found", not actual leaks
                        if http_status == 404:
                            continue

                        # Convert file_size to integer (database expects Integer type)
                        file_size_str = match.group(2)
                        file_size = int(file_size_str) if file_size_str.isdigit() else 0

                        response_time = match.group(3)
                        content_type = match.group(4)
                        url = match.group(5)

                        # Extract base URL
                        parsed = urlparse(url)
                        base_url = f"{parsed.scheme}://{parsed.netloc}"

                        # Determine severity based on HTTP status and file type
                        severity = 'low'

                        # High severity: Accessible sensitive files (200)
                        if http_status == 200:
                            severity = 'high'
                        # Medium severity: Forbidden files (403) - file exists but access denied
                        elif http_status == 403:
                            severity = 'medium'
                        # Low severity: Other status codes
                        else:
                            severity = 'low'

                        # Upgrade severity for critical file types
                        if any(x in url.lower() for x in ['.sql', '.env', '.git/config', 'backup', 'database']):
                            if severity == 'medium':
                                severity = 'high'
                            elif severity == 'low':
                                severity = 'medium'
                        elif any(x in url.lower() for x in ['.zip', '.tar', '.rar', '.bak', '.7z']):
                            if severity == 'low':
                                severity = 'medium'

                        results.append({
                            'base_url': base_url,
                            'leaked_file_url': url,
                            'file_type': content_type,
                            'severity': severity,
                            'file_size': file_size,  # Now an integer
                            'http_status': http_status
                        })
                    except Exception as e:
                        logger.warning(f"[{self.job_id}] Failed to parse STDOUT line: {line} - {e}")

        # Parse CSV files (if they exist)
        if self.leaks_output_dir.exists():
            logger.info(f"[{self.job_id}] Parsing SourceLeakHacker CSV files...")
            csv_results = await self._parse_sourceleakhacker_csv_files()

            # Merge results, avoiding duplicates
            existing_urls = {r['leaked_file_url'] for r in results}
            for csv_result in csv_results:
                if csv_result['leaked_file_url'] not in existing_urls:
                    results.append(csv_result)

        logger.info(f"[{self.job_id}] Total leaks parsed: {len(results)}")
        return results

    async def _parse_sourceleakhacker_csv_files(self) -> List[Dict[str, Any]]:
        """Parse CSV files from SourceLeakHacker output directory

        SourceLeakHacker creates separate CSV files for each HTTP status code:
        - 200.csv: Successful requests (accessible leaks)
        - 403.csv: Forbidden (still leaks, just access denied)
        - 404.csv: Not found (potential leaks)
        - 0.csv: Connection errors
        - etc.

        CSV format: Code, Length, Time, Type, URL

        NOTE: We parse ALL CSV files, not just 200.csv, because:
        - 403 = File exists but forbidden (LEAK!)
        - 404 = File might exist with different path
        - Other codes = Still valuable information
        """
        results = []

        try:
            import csv
            from urllib.parse import urlparse

            # Parse ALL CSV files in the output directory (EXCEPT 404.csv)
            csv_files = list(self.leaks_output_dir.glob("*.csv"))

            if not csv_files:
                logger.info(f"[{self.job_id}] No CSV files found in {self.leaks_output_dir}")
                return results

            logger.info(f"[{self.job_id}] Found {len(csv_files)} CSV files to parse")

            for csv_file in csv_files:
                http_status = csv_file.stem  # e.g., "200", "403", "404"

                # Skip 404.csv - these are "Not Found" responses, not actual leaks
                if http_status == "404":
                    logger.info(f"[{self.job_id}] Skipping {csv_file.name} (404 = Not Found, not a leak)")
                    continue

                logger.info(f"[{self.job_id}] Parsing {csv_file.name}...")

                file_count = 0
                with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            url = row.get('URL', '')
                            if not url:
                                continue

                            # Extract base URL
                            parsed = urlparse(url)
                            base_url = f"{parsed.scheme}://{parsed.netloc}"

                            # Determine severity based on HTTP status and file type
                            severity = 'low'

                            # High severity: Accessible sensitive files (200)
                            if http_status == '200':
                                severity = 'high'
                            # Medium severity: Forbidden files (403) - file exists but access denied
                            elif http_status == '403':
                                severity = 'medium'
                            # Low severity: Other status codes
                            else:
                                severity = 'low'

                            # Upgrade severity for critical file types
                            if any(x in url.lower() for x in ['.sql', '.env', '.git/config', 'backup', 'database']):
                                if severity == 'medium':
                                    severity = 'high'
                                elif severity == 'low':
                                    severity = 'medium'
                            elif any(x in url.lower() for x in ['.zip', '.tar', '.rar', '.bak', '.7z']):
                                if severity == 'low':
                                    severity = 'medium'

                            results.append({
                                'base_url': base_url,
                                'leaked_file_url': url,
                                'file_type': row.get('Type', 'unknown'),
                                'severity': severity,
                                'file_size': row.get('Length'),
                                'http_status': int(http_status) if http_status.isdigit() else 0
                            })
                            file_count += 1
                        except Exception as e:
                            logger.warning(f"[{self.job_id}] Failed to parse CSV row in {csv_file.name}: {row} - {e}")

                logger.info(f"[{self.job_id}] Parsed {file_count} leaks from {csv_file.name}")

            logger.info(f"[{self.job_id}] Total leaks from all CSV files: {len(results)}")

        except Exception as e:
            logger.warning(f"[{self.job_id}] Failed parsing CSV files: {e}")

        return results

    async def _parse_live_results(self) -> List[Dict[str, Any]]:
        """Parse httpx JSON output - includes both live and dead hosts with all httpx fields"""
        if not self.live_file.exists():
            return []

        # Status codes that indicate a "live" host (server is responding)
        # 2xx: Success
        # 3xx: Redirects (server is responding)
        # 4xx: Client errors (server is responding)
        # 5xx: Server errors (server is responding - important for visibility!)
        LIVE_STATUS_CODES = {200, 201, 202, 204, 301, 302, 303, 304, 307, 308, 400, 401, 403, 404, 500, 501, 502, 503, 504}

        live_hosts = []
        with open(self.live_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    import json
                    data = json.loads(line)
                    status_code = data.get('status_code')
                    is_live = status_code in LIVE_STATUS_CODES if status_code else False

                    # Extract all httpx JSON fields
                    live_hosts.append({
                        # Core fields
                        'url': data.get('url', ''),
                        'status_code': status_code,
                        'is_live': is_live,

                        # Essential httpx fields
                        'title': data.get('title', '').strip() if data.get('title') else None,
                        'content_length': data.get('content_length'),
                        'webserver': data.get('webserver'),
                        'final_url': data.get('final_url'),

                        # Useful httpx fields
                        'response_time': data.get('time'),  # httpx uses 'time' field (e.g., "11.4100539s")
                        'cdn_name': data.get('cdn_name'),
                        'content_type': data.get('content_type'),
                        'host': data.get('host'),  # Primary IP address

                        # Array fields
                        'chain_status_codes': data.get('chain_status_codes', []),
                        'ipv4_addresses': data.get('a', []),  # httpx uses 'a' for IPv4
                        'ipv6_addresses': data.get('aaaa', []),  # httpx uses 'aaaa' for IPv6
                        'technologies': data.get('tech', [])  # httpx uses 'tech' for technologies
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
    async def _run_command_with_logging(self, cmd: List[str], tool_name: str, timeout: int = 2600) -> str:
        """Run a command with enhanced logging and progress tracking (Windows compatible)"""
        try:
            logger.info(f"[{self.job_id}] Starting {tool_name}: {' '.join(cmd)}")
            logger.info(f"[{self.job_id}] Working directory: {self.job_dir}")
            logger.info(f"[{self.job_id}] Command executable: {cmd[0]}")

            # Check if executable exists
            if not os.path.exists(cmd[0]):
                raise FileNotFoundError(f"Tool not found: {cmd[0]}")

            # Use synchronous subprocess for Windows compatibility
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
