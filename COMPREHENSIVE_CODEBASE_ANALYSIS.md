# 📚 COMPREHENSIVE CODEBASE ANALYSIS - RECONNAISSANCE SYSTEM

**Generated:** 2025-11-01  
**Project:** Subdomain Reconnaissance & Screenshot Capture System  
**Version:** 1.0.0

---

## TABLE OF CONTENTS

1. [Development Environment & Technology Stack](#1-development-environment--technology-stack)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Complete Workflow - Full Reconnaissance Pipeline](#3-complete-workflow---full-reconnaissance-pipeline)
4. [Code Flow & Function Calls](#4-code-flow--function-calls)
5. [Data Processing & Storage](#5-data-processing--storage)
6. [Special Features](#6-special-features)
7. [Database Schema](#7-database-schema)
8. [API Endpoints Reference](#8-api-endpoints-reference)
9. [Celery Task Queue Architecture](#9-celery-task-queue-architecture)
10. [File Structure & Organization](#10-file-structure--organization)

---

## 1. DEVELOPMENT ENVIRONMENT & TECHNOLOGY STACK

### 1.1 Core Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.13 | Primary programming language |
| **Web Framework** | FastAPI | 0.109.0 - 0.115.0 | REST API server |
| **ASGI Server** | Uvicorn | 0.27.0 - 0.31.0 | Production-ready ASGI server |
| **Database** | PostgreSQL | Latest | Persistent data storage |
| **ORM** | SQLAlchemy | 2.0.25 - 2.1.0 | Database abstraction layer |
| **Message Broker** | Redis | 5.0.1 - 6.0.0 | Celery message broker & result backend |
| **Task Queue** | Celery | 5.3.6 - 5.5.0 | Distributed task processing |
| **Task Monitor** | Flower | 2.0.1 - 3.0.0 | Celery monitoring dashboard |
| **Migration Tool** | Alembic | 1.13.0 - 1.14.0 | Database schema migrations |
| **Validation** | Pydantic | 2.8.0 - 3.0.0 | Data validation & serialization |
|

**Configuration File:** `requirements.txt` (32 lines)

### 1.2 External CLI Tools Integrated

The system integrates **8 external reconnaissance tools**:

| Tool | Purpose | Language | Installation |
|------|---------|----------|--------------|
| **subfinder** | Subdomain enumeration | Go | `go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| **amass** | Advanced subdomain discovery | Go | `go install -v github.com/owasp-amass/amass/v4/...@master` |
| **assetfinder** | Fast subdomain finder | Go | `go install github.com/tomnomnom/assetfinder@latest` |
| **httprobe** | HTTP/HTTPS probe | Go | `go install github.com/tomnomnom/httprobe@latest` |
| **httpx** | Advanced HTTP toolkit | Go | `go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest` |
| **anew** | Append new lines to file | Go | `go install -v github.com/tomnomnom/anew@latest` |
| **gowitness** | Web screenshot tool | Go | `go install github.com/sensepost/gowitness@latest` |
| **wafw00f** | WAF detection | Python | `pip install wafw00f` |
| **SourceLeakHacker** | Source code leak scanner | Python | Custom script (SourceLeakHacker.py) |

**Tool Paths Configuration:** `app/deps.py` (lines 42-52)

```python
# Tool paths (assuming tools are in PATH)
subfinder_path: str = "subfinder"
amass_path: str = "amass"
assetfinder_path: str = "assetfinder"
httpx_path: str = "httpx"
httprobe_path: str = "httprobe"
anew_path: str = "anew"
gowitness_path: str = "gowitness"
wafw00f_path: str = "wafw00f"
sourceleakhacker_path: str = "SourceLeakHacker.py"
python_executable: str = "python"
```

**Tool Timeouts Configuration:** `app/deps.py` (lines 54-62)

```python
# Tool timeouts (in seconds)
subfinder_timeout: int = 600      # 10 minutes
amass_timeout: int = 1200         # 20 minutes
assetfinder_timeout: int = 300    # 5 minutes
httpx_timeout: int = 900          # 15 minutes
httprobe_timeout: int = 600       # 10 minutes
gowitness_timeout: int = 1800     # 30 minutes
wafw00f_timeout: int = 900        # 15 minutes
sourceleakhacker_timeout: int = 2800  # 46.67 minutes (user modified)
```

### 1.3 Deployment Environment

**Current Environment:** Windows Development

**Evidence:**
- Celery worker uses `--pool=solo` flag (Windows compatibility)
- PowerShell scripts for automation (`start_all.ps1`, `stop_all.ps1`)
- Batch files for quick startup (`start_api.bat`, `start_worker.bat`)

**File:** `start_worker.bat`
```batch
celery -A app.workers.celery_app worker --loglevel=info --pool=solo -Q recon_full
```

**Production Deployment Options:**
- Docker containers (Dockerfiles provided in `docker/` directory)
- Linux servers (recommended for production)
- Kubernetes orchestration (for scaling)

### 1.4 Configuration Management

**Primary Configuration:** `app/deps.py` (Settings class)

```python
class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/recon_db"
    
    # Redis for Celery
    redis_url: str = "redis://localhost:6379/0"
    
    # API settings
    api_title: str = "Recon API"
    api_version: str = "1.0.0"
    
    # CORS settings
    cors_origins: list[str] = [...]
    
    # File storage
    jobs_directory: str = "./jobs"
    
    # Tool paths and timeouts
    # ... (see sections above)
    
    class Config:
        env_file = ".env"  # Load from .env file
```

**Environment Variables:** `.env` file (optional, overrides defaults)

---

## 2. SYSTEM ARCHITECTURE OVERVIEW

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Web Browser  │  │ API Clients  │  │ CLI Scripts  │              │
│  │ (Dashboard)  │  │ (curl, etc.) │  │ (Python)     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                  │                       │
│         └──────────────────┴──────────────────┘                       │
│                            │                                          │
└────────────────────────────┼──────────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────┼──────────────────────────────────────────┐
│                    API LAYER (FastAPI)                                │
│                            │                                          │
│  ┌─────────────────────────▼────────────────────────────┐            │
│  │  app/main.py - FastAPI Application                   │            │
│  │  - CORS middleware                                    │            │
│  │  - Static file serving (/jobs, /dashboard)           │            │
│  │  - API documentation (/docs, /redoc)                 │            │
│  └─────────────────────────┬────────────────────────────┘            │
│                            │                                          │
│  ┌─────────────────────────▼────────────────────────────┐            │
│  │  app/routers/scans.py - API Endpoints                │            │
│  │  - POST /api/v1/scans (create scan)                  │            │
│  │  - GET  /api/v1/scans (list scans)                   │            │
│  │  - GET  /api/v1/scans/{job_id} (get scan details)    │            │
│  │  - POST /api/v1/scans/bulk (bulk scan)               │            │
│  │  - POST /api/v1/scans/{job_id}/leak-scan (selective) │            │
│  │  - POST /api/v1/scans/{job_id}/subdomains (manual)   │            │
│  └─────────────────────────┬────────────────────────────┘            │
│                            │                                          │
└────────────────────────────┼──────────────────────────────────────────┘
                             │ Dispatch Tasks
┌────────────────────────────┼──────────────────────────────────────────┐
│                   TASK QUEUE LAYER (Celery + Redis)                  │
│                            │                                          │
│  ┌─────────────────────────▼────────────────────────────┐            │
│  │  Redis Message Broker                                │            │
│  │  - Task queue: recon_full, leak_check, waf_check     │            │
│  │  - Result backend: stores task results               │            │
│  └─────────────────────────┬────────────────────────────┘            │
│                            │                                          │
│  ┌─────────────────────────▼────────────────────────────┐            │
│  │  app/workers/celery_app.py - Celery Configuration    │            │
│  │  - Task routing to queues                            │            │
│  │  - Retry policies                                    │            │
│  │  - Timeout settings                                  │            │
│  └─────────────────────────┬────────────────────────────┘            │
│                            │                                          │
│  ┌─────────────────────────▼────────────────────────────┐            │
│  │  app/workers/tasks.py - Celery Tasks                 │            │
│  │  - run_recon_scan (full pipeline)                    │            │
│  │  - run_sourceleakhacker_check (selective)            │            │
│  │  - run_waf_check (WAF detection)                     │            │
│  └─────────────────────────┬────────────────────────────┘            │
│                            │                                          │
└────────────────────────────┼──────────────────────────────────────────┘
                             │ Execute Pipeline
┌────────────────────────────┼──────────────────────────────────────────┐
│                  PIPELINE LAYER (Orchestration)                       │
│                            │                                          │
│  ┌─────────────────────────▼────────────────────────────┐            │
│  │  app/services/pipeline.py - ReconPipeline            │            │
│  │  - enumerate_subdomains_enhanced()                   │            │
│  │  - check_live_hosts_enhanced()                       │            │
│  │  - capture_screenshots()                             │            │
│  │  - run_waf_detection()                               │            │
│  │  - run_sourceleakhacker()                            │            │
│  └─────────────────────────┬────────────────────────────┘            │
│                            │                                          │
└────────────────────────────┼──────────────────────────────────────────┘
                             │ Execute CLI Tools
┌────────────────────────────┼──────────────────────────────────────────┐
│                   CLI TOOLS LAYER (External)                          │
│                            │                                          │
│  ┌────────────┬────────────┴────────────┬────────────┬──────────┐   │
│  │            │                         │            │          │   │
│  ▼            ▼                         ▼            ▼          ▼   │
│ subfinder   amass                   httprobe      httpx    gowitness │
│ assetfinder                                                          │
│                                                                      │
│  ┌────────────┬────────────────────────────────────────────────┐   │
│  │            │                                                 │   │
│  ▼            ▼                                                 ▼   │
│ wafw00f   SourceLeakHacker                                          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                             │ Parse Output
┌────────────────────────────┼──────────────────────────────────────────┐
│                   PARSING LAYER                                       │
│                            │                                          │
│  ┌─────────────────────────▼────────────────────────────┐            │
│  │  app/services/parsers.py - Output Parsers            │            │
│  │  - SubfinderParser                                   │            │
│  │  - AmassParser                                       │            │
│  │  - AssetfinderParser                                 │            │
│  │  - HttpxParser                                       │            │
│  └─────────────────────────┬────────────────────────────┘            │
│                            │                                          │
└────────────────────────────┼──────────────────────────────────────────┘
                             │ Store Data
┌────────────────────────────┼──────────────────────────────────────────┐
│                   DATA LAYER (PostgreSQL)                             │
│                            │                                          │
│  ┌─────────────────────────▼────────────────────────────┐            │
│  │  app/storage/repo.py - Repository Layer              │            │
│  │  - ScanJobRepository                                 │            │
│  │  - SubdomainRepository                               │            │
│  │  - ScreenshotRepository                              │            │
│  │  - WafDetectionRepository                            │            │
│  │  - LeakDetectionRepository                           │            │
│  └─────────────────────────┬────────────────────────────┘            │
│                            │                                          │
│  ┌─────────────────────────▼────────────────────────────┐            │
│  │  app/storage/models.py - SQLAlchemy Models           │            │
│  │  - ScanJob                                           │            │
│  │  - Subdomain                                         │            │
│  │  - Screenshot                                        │            │
│  │  - WafDetection                                      │            │
│  │  - LeakDetection                                     │            │
│  └─────────────────────────┬────────────────────────────┘            │
│                            │                                          │
│  ┌─────────────────────────▼────────────────────────────┐            │
│  │  PostgreSQL Database                                 │            │
│  │  Tables: scan_jobs, subdomains, screenshots,         │            │
│  │          waf_detections, leak_detections             │            │
│  └──────────────────────────────────────────────────────┘            │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| **API Server** | `app/main.py` | HTTP server, routing, CORS, static files |
| **API Endpoints** | `app/routers/scans.py` | REST API endpoints, request validation |
| **Task Queue** | `app/workers/celery_app.py` | Celery configuration, task routing |
| **Background Tasks** | `app/workers/tasks.py` | Async task execution, progress tracking |
| **Pipeline Orchestration** | `app/services/pipeline.py` | CLI tool execution, workflow management |
| **Output Parsing** | `app/services/parsers.py` | Parse CLI tool output |
| **Data Access** | `app/storage/repo.py` | Database CRUD operations |
| **Data Models** | `app/storage/models.py` | SQLAlchemy ORM models |
| **Configuration** | `app/deps.py` | Settings, database connection |
| **Frontend** | `web/index.html`, `web/app.js` | Web dashboard UI |

---

## 3. COMPLETE WORKFLOW - FULL RECONNAISSANCE PIPELINE

### 3.1 Pipeline Overview

The full reconnaissance pipeline (`run_recon_scan` task) executes **4 main stages**:

1. **Subdomain Enumeration** - Discover subdomains using 3 tools
2. **Live Host Detection** - Check which subdomains are live
3. **Screenshot Capture** - Take screenshots of live hosts
4. **WAF Detection** - Detect Web Application Firewalls

**Note:** SourceLeakHacker is **NOT** part of the automatic pipeline. It runs only via selective scanning.

### 3.2 Step-by-Step Workflow

#### **STEP 0: API Request Received**

**File:** `app/routers/scans.py` (lines 97-130)

**Endpoint:** `POST /api/v1/scans`

**Request Body:**
```json
{
    "domain": "example.com"
}
```

**Code Flow:**
```python
@router.post("/scans", response_model=ScanResponse)
async def create_scan(scan_request: ScanRequest, db: Session = Depends(get_db)):
    # 1. Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # 2. Validate domain
    domain = scan_request.domain.strip().lower()
    
    # 3. Create scan job in database
    scan_repo = ScanJobRepository(db)
    scan_job = scan_repo.create_scan_job(job_id, domain)
    
    # 4. Dispatch Celery task
    task = run_recon_scan.delay(job_id, domain)
    
    # 5. Store task_id for progress tracking
    scan_repo.update_task_id(job_id, task.id)
    
    # 6. Return response immediately
    return ScanResponse(
        job_id=job_id,
        domain=domain,
        status="pending",
        message=f"Task ID: {task.id}"
    )
```

**Database Changes:**
- Creates new record in `scan_jobs` table with status `pending`

---

#### **STEP 1: Celery Task Dispatched**

**File:** `app/workers/tasks.py` (lines 16-140)

**Task:** `run_recon_scan(job_id, domain)`

**Queue:** `recon_full` (configured in `app/workers/celery_app.py` line 42)

**Code Flow:**
```python
@celery_app.task(bind=True)
def run_recon_scan(self, job_id: str, domain: str) -> Dict[str, Any]:
    # 1. Setup progress callback
    def progress_callback(percentage: int, message: str):
        self.update_state(
            state='PROGRESS',
            meta={'current': percentage, 'total': 100, 'status': message}
        )

    # 2. Create pipeline instance
    pipeline = ReconPipeline(job_id, domain, progress_callback)

    # 3. Update scan status to 'running'
    scan_repo.update_scan_status(job_id, ScanStatus.RUNNING)

    # 4. Execute pipeline (4 stages)
    results = loop.run_until_complete(pipeline.run_full_pipeline())

    # 5. Save results to database
    # ... (see Step 5 for details)

    # 6. Update scan status to 'completed'
    scan_repo.update_scan_status(job_id, ScanStatus.COMPLETED)

    return results
```

**Database Changes:**
- Updates `scan_jobs.status` to `running`
- Updates `scan_jobs.task_id` with Celery task ID

---

#### **STEP 2: Pipeline Initialization**

**File:** `app/services/pipeline.py` (lines 1-100)

**Class:** `ReconPipeline`

**Constructor:**
```python
class ReconPipeline:
    def __init__(self, job_id: str, domain: str, progress_callback=None):
        self.job_id = job_id
        self.domain = domain
        self.progress_callback = progress_callback

        # Create job directory
        self.job_dir = Path(settings.jobs_directory) / job_id
        self.job_dir.mkdir(parents=True, exist_ok=True)

        # Define file paths
        self.subs_file = self.job_dir / "subs.txt"
        self.live_file = self.job_dir / "live.txt"
        self.httpx_json_file = self.job_dir / "httpx.json"
        # ... more file paths
```

**File System Changes:**
- Creates directory: `./jobs/{job_id}/`
- Prepares file paths for tool outputs

---

#### **STEP 3: Stage 1 - Subdomain Enumeration**

**File:** `app/services/pipeline.py` (lines 101-350)

**Method:** `enumerate_subdomains_enhanced()`

**Duration:** ~15-30 minutes (depending on domain size)

**Sub-steps:**

##### **3.1: Run subfinder**

**File:** `app/services/pipeline.py` (lines 150-180)

**CLI Command:**
```bash
subfinder -d example.com -o subs.txt -silent
```

**Code:**
```python
async def _run_subfinder_cli(self):
    cmd = [
        settings.subfinder_path,
        "-d", self.domain,
        "-o", "subs.txt",
        "-silent"
    ]
    await self._run_command_with_logging(cmd, "subfinder")
```

**Output:** `jobs/{job_id}/subs.txt` (one subdomain per line)

**Example Output:**
```
www.example.com
api.example.com
mail.example.com
```

**Parser:** `SubfinderParser` (`app/services/parsers.py` lines 29-49)

**Parsing Logic:**
```python
class SubfinderParser:
    @staticmethod
    def parse(output: str) -> List[SubdomainResult]:
        results = []
        for line in output.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('[') and '.' in line:
                subdomain = line.lower().strip()
                results.append(SubdomainResult(
                    subdomain=subdomain,
                    source="subfinder"
                ))
        return results
```

##### **3.2: Run amass (passive mode)**

**File:** `app/services/pipeline.py` (lines 230-250)

**CLI Command:**
```bash
amass enum -passive -timeout 10 -d example.com -o amass_raw.txt
```

**Code:**
```python
async def _run_amass_cli(self):
    cmd = [
        settings.amass_path,
        "enum",
        "-passive",
        "-timeout", "10",
        "-d", self.domain,
        "-o", "amass_raw.txt"
    ]
    await self._run_command_with_logging(cmd, "amass")

    # Filter FQDNs only
    await self._filter_amass_output(amass_raw_file)

    # Merge with subs.txt using anew
    await self._merge_files_with_anew(self.amass_file, self.subs_file)
```

**Output:** `jobs/{job_id}/amass.txt` (filtered FQDNs)

**Parser:** `AmassParser` (`app/services/parsers.py` lines 52-90)

**Parsing Logic:**
```python
class AmassParser:
    @staticmethod
    def parse(output: str) -> List[SubdomainResult]:
        results = []
        seen_domains = set()
        for line in output.strip().split('\n'):
            # Extract FQDN from various formats
            if line.startswith('FQDN:'):
                domain = line.split('FQDN:')[1].strip()
            elif ',' in line:
                parts = line.split(',')
                domain = parts[0].strip()
            else:
                domain = line.strip()

            # Validate and deduplicate
            if domain and '.' in domain and domain not in seen_domains:
                seen_domains.add(domain)
                results.append(SubdomainResult(
                    subdomain=domain.lower(),
                    source="amass"
                ))
        return results
```

##### **3.3: Run assetfinder**

**File:** `app/services/pipeline.py` (lines 270-290)

**CLI Command:**
```bash
assetfinder --subs-only example.com
```

**Code:**
```python
async def _run_assetfinder_cli(self):
    cmd = [settings.assetfinder_path, "--subs-only", self.domain]
    stdout = await self._run_command_with_logging(cmd, "assetfinder")

    # Parse output and merge with subs.txt
    if stdout:
        temp_file = self.job_dir / "assetfinder_temp.txt"
        with open(temp_file, 'w') as f:
            f.write(stdout)
        await self._merge_files_with_anew(temp_file, self.subs_file)
```

**Output:** Merged into `jobs/{job_id}/subs.txt`

**Parser:** `AssetfinderParser` (`app/services/parsers.py` lines 93-110)

##### **3.4: Deduplicate and Count**

**File:** `app/services/pipeline.py` (lines 320-350)

**Code:**
```python
# Read final deduplicated subdomains
subdomains = await self._read_subdomains_file()

self.progress_callback(30, f'Found {len(subdomains)} unique subdomains')

return subdomains
```

**Result:** List of unique subdomains (e.g., 100-1000+ subdomains)

---

#### **STEP 4: Stage 2 - Live Host Detection**

**File:** `app/services/pipeline.py` (lines 400-550)

**Method:** `check_live_hosts_enhanced()`

**Duration:** ~10-20 minutes

**Sub-steps:**

##### **4.1: Run httprobe**

**File:** `app/services/pipeline.py` (lines 420-450)

**CLI Command:**
```bash
cat subs.txt | httprobe -c 50 > live.txt
```

**Code:**
```python
async def _run_httprobe_cli(self):
    # Read subdomains
    with open(self.subs_file, 'r') as f:
        subdomains_input = f.read()

    # Run httprobe
    cmd = [settings.httprobe_path, "-c", "50"]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=self.job_dir
    )

    stdout, stderr = await asyncio.wait_for(
        process.communicate(input=subdomains_input.encode()),
        timeout=settings.httprobe_timeout
    )

    # Save live hosts
    with open(self.live_file, 'wb') as f:
        f.write(stdout)
```

**Output:** `jobs/{job_id}/live.txt` (URLs with http/https prefix)

**Example Output:**
```
https://www.example.com
http://api.example.com
https://mail.example.com
```

##### **4.2: Run httpx (detailed probing)**

**File:** `app/services/pipeline.py` (lines 470-520)

**CLI Command:**
```bash
cat live.txt | httpx -json -status-code -content-length -title -tech-detect -follow-redirects -timeout 30 -o httpx.json
```

**Code:**
```python
async def _run_httpx_cli(self):
    cmd = [
        settings.httpx_path,
        "-json",
        "-status-code",
        "-content-length",
        "-title",
        "-tech-detect",
        "-follow-redirects",
        "-timeout", "30",
        "-o", "httpx.json"
    ]

    # Read live hosts as input
    with open(self.live_file, 'r') as f:
        live_hosts_input = f.read()

    # Run httpx
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=self.job_dir
    )

    await asyncio.wait_for(
        process.communicate(input=live_hosts_input.encode()),
        timeout=settings.httpx_timeout
    )
```

**Output:** `jobs/{job_id}/httpx.json` (JSONL format - one JSON object per line)

**Example Output:**
```json
{"url":"https://www.example.com","status_code":200,"content_length":1234,"title":"Example Domain","tech":["Nginx"],"response_time":"123ms"}
{"url":"http://api.example.com","status_code":403,"content_length":0,"title":"Forbidden","tech":[],"response_time":"45ms"}
```

**Parser:** `HttpxParser` (`app/services/parsers.py` lines 113-180)

**Parsing Logic:**
```python
class HttpxParser:
    @staticmethod
    def parse_jsonl_file(file_path: Path) -> List[LiveHostResult]:
        results = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())

                    # Determine if host is live based on status code
                    status_code = data.get('status_code', 0)
                    LIVE_STATUS_CODES = {200, 301, 302, 304, 307, 308, 400, 401, 403, 500, 501, 502, 503, 504}
                    is_live = status_code in LIVE_STATUS_CODES

                    results.append(LiveHostResult(
                        url=data.get('url'),
                        status_code=status_code,
                        is_live=is_live,
                        content_length=data.get('content_length'),
                        title=data.get('title'),
                        tech=data.get('tech', []),
                        response_time=data.get('response_time')
                    ))
                except json.JSONDecodeError:
                    continue
        return results
```

**Note:** User modified `LIVE_STATUS_CODES` to exclude 404 and 405 (see `app/services/pipeline.py` line 836)

---

#### **STEP 5: Stage 3 - Screenshot Capture**

**File:** `app/services/pipeline.py` (lines 750-820)

**Method:** `capture_screenshots()`

**Duration:** ~20-30 minutes (depends on number of live hosts)

**CLI Command:**
```bash
gowitness scan file -f live.txt --screenshot-path shots --disable-db --delay 1 --timeout 30
```

**Code:**
```python
async def capture_screenshots(self, live_hosts: List[str]) -> List[Dict[str, Any]]:
    # Create screenshots directory
    shots_dir = self.job_dir / "shots"
    shots_dir.mkdir(exist_ok=True)

    # Save live hosts to file
    with open(self.live_file, 'w') as f:
        f.write('\n'.join(live_hosts))

    # Run gowitness
    cmd = [
        settings.gowitness_path,
        "scan", "file",
        "-f", str(self.live_file),
        "--screenshot-path", str(shots_dir),
        "--disable-db",
        "--delay", "1",
        "--timeout", "30"
    ]

    await self._run_command_with_logging(cmd, "gowitness")

    # Parse screenshot files
    screenshots = []
    for screenshot_file in shots_dir.glob("*.png"):
        file_size = screenshot_file.stat().st_size
        url = self._extract_url_from_filename(screenshot_file.name)

        screenshots.append({
            'url': url,
            'filename': screenshot_file.name,
            'file_path': f"jobs/{self.job_id}/shots/{screenshot_file.name}",
            'file_size': file_size
        })

    return screenshots
```

**Output:** `jobs/{job_id}/shots/*.png` (PNG screenshot files)

**Example Files:**
```
jobs/{job_id}/shots/https-www.example.com.png
jobs/{job_id}/shots/http-api.example.com.png
```

**File Naming Convention:** gowitness converts URLs to filenames by replacing special characters

---

#### **STEP 6: Stage 4 - WAF Detection**

**File:** `app/services/pipeline.py` (lines 900-1000)

**Method:** `run_waf_detection()`

**Duration:** ~10-15 minutes

**CLI Command:**
```bash
wafw00f https://www.example.com -o waf_results.json -f json
```

**Code:**
```python
async def run_waf_detection(self, live_hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    waf_detections = []

    for host in live_hosts:
        url = host['url']

        # Run wafw00f for each URL
        cmd = [
            settings.wafw00f_path,
            url,
            "-o", f"waf_{hash(url)}.json",
            "-f", "json"
        ]

        try:
            stdout = await self._run_command_with_logging(cmd, "wafw00f")

            # Parse JSON output
            waf_data = json.loads(stdout)

            waf_detections.append({
                'url': url,
                'has_waf': len(waf_data.get('firewall', [])) > 0,
                'waf_name': waf_data.get('firewall', [None])[0],
                'waf_manufacturer': waf_data.get('manufacturer')
            })
        except Exception as e:
            # WAF detection failed, mark as no WAF
            waf_detections.append({
                'url': url,
                'has_waf': False,
                'waf_name': None,
                'waf_manufacturer': None
            })

    return waf_detections
```

**Output:** WAF detection results (in-memory, saved to database)

**Example Result:**
```python
[
    {
        'url': 'https://www.example.com',
        'has_waf': True,
        'waf_name': 'Cloudflare',
        'waf_manufacturer': 'Cloudflare Inc.'
    },
    {
        'url': 'http://api.example.com',
        'has_waf': False,
        'waf_name': None,
        'waf_manufacturer': None
    }
]
```

---

#### **STEP 7: Save Results to Database**

**File:** `app/workers/tasks.py` (lines 56-140)

**Code Flow:**
```python
# Get scan job from database
scan_job = scan_repo.get_scan_job(job_id)

# Initialize repositories
subdomain_repo = SubdomainRepository(db)
screenshot_repo = ScreenshotRepository(db)
waf_repo = WafDetectionRepository(db)

# 1. Save discovered subdomains
if results.get('subdomains'):
    subdomain_repo.bulk_create_subdomains(
        scan_job.id,
        results['subdomains'],
        discovered_by="enhanced_pipeline"
    )

# 2. Update subdomain status with live host data
if results.get('live_hosts'):
    for live_host in results['live_hosts']:
        url = live_host['url']
        domain_part = url.replace('http://', '').replace('https://', '').split('/')[0]

        # Find corresponding subdomain
        subdomains = subdomain_repo.get_subdomains_by_job(job_id)
        for subdomain in subdomains:
            if subdomain.subdomain == domain_part:
                status = SubdomainStatus.LIVE if live_host.get('is_live') else SubdomainStatus.DEAD
                subdomain_repo.update_subdomain_status(
                    subdomain.id,
                    status,
                    is_live=live_host.get('is_live', False),
                    http_status=live_host.get('status_code'),
                    response_time=live_host.get('response_time')
                )
                break

# 3. Save screenshots
if results.get('screenshots'):
    for screenshot in results['screenshots']:
        screenshot_repo.create_screenshot(
            scan_job_id=scan_job.id,
            url=screenshot['url'],
            filename=screenshot['filename'],
            file_path=screenshot['file_path'],
            file_size=screenshot.get('file_size')
        )

# 4. Save WAF detections
if results.get('waf_detections'):
    waf_repo.bulk_create(scan_job.id, results['waf_detections'])

# 5. Update scan status to completed
scan_repo.update_scan_status(job_id, ScanStatus.COMPLETED)
scan_repo.update_completed_at(job_id)
```

**Database Changes:**

| Table | Operation | Records |
|-------|-----------|---------|
| `scan_jobs` | UPDATE | 1 (status → completed) |
| `subdomains` | INSERT | 100-1000+ |
| `subdomains` | UPDATE | 10-100 (live hosts) |
| `screenshots` | INSERT | 10-100 |
| `waf_detections` | INSERT | 10-100 |

---

#### **STEP 8: Return Results**

**File:** `app/workers/tasks.py` (lines 130-140)

**Return Value:**
```python
return {
    'job_id': job_id,
    'domain': domain,
    'status': 'completed',
    'subdomains_count': len(results.get('subdomains', [])),
    'live_hosts_count': len(results.get('live_hosts', [])),
    'screenshots_count': len(results.get('screenshots', [])),
    'waf_detections_count': len(results.get('waf_detections', [])),
    'message': f'Scan completed successfully for {domain}'
}
```

**Celery Result Backend:**
- Stores result in Redis with key: `celery-task-meta-{task_id}`
- TTL: 24 hours (default)

---

### 3.3 Pipeline Execution Timeline

```
Time    Stage                           Progress    CLI Tool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0:00    API Request Received            0%          -
0:01    Celery Task Dispatched          5%          -
0:02    Pipeline Initialized            10%         -

        ┌─ STAGE 1: SUBDOMAIN ENUMERATION ─────────────────────────┐
0:03    │ Running subfinder...           15%         subfinder     │
5:00    │ Running amass...               20%         amass         │
15:00   │ Running assetfinder...         25%         assetfinder   │
18:00   │ Deduplicating results...       30%         anew          │
        └──────────────────────────────────────────────────────────┘

        ┌─ STAGE 2: LIVE HOST DETECTION ───────────────────────────┐
18:30   │ Running httprobe...            40%         httprobe      │
23:00   │ Running httpx...               50%         httpx         │
28:00   │ Parsing httpx results...       60%         -             │
        └──────────────────────────────────────────────────────────┘

        ┌─ STAGE 3: SCREENSHOT CAPTURE ────────────────────────────┐
28:30   │ Running gowitness...           70%         gowitness     │
45:00   │ Processing screenshots...      80%         -             │
        └──────────────────────────────────────────────────────────┘

        ┌─ STAGE 4: WAF DETECTION ─────────────────────────────────┐
45:30   │ Running wafw00f...             85%         wafw00f       │
55:00   │ Parsing WAF results...         90%         -             │
        └──────────────────────────────────────────────────────────┘

56:00   Saving to database...           95%         -
57:00   Scan completed!                 100%        -
```

**Total Duration:** ~55-60 minutes for a typical domain

---

## 4. CODE FLOW & FUNCTION CALLS

### 4.1 Complete Call Chain - Full Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. CLIENT REQUEST                                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. FastAPI Endpoint                                                  │
│    File: app/routers/scans.py                                        │
│    Function: create_scan()                                           │
│    Lines: 97-130                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ├─► ScanJobRepository.create_scan_job()
                              │   File: app/storage/repo.py (lines 17-23)
                              │   └─► INSERT INTO scan_jobs
                              │
                              ├─► run_recon_scan.delay()
                              │   File: app/workers/tasks.py (line 16)
                              │   └─► Celery task dispatched to queue
                              │
                              └─► ScanJobRepository.update_task_id()
                                  File: app/storage/repo.py (lines 30-37)
                                  └─► UPDATE scan_jobs SET task_id

                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. Celery Worker Picks Up Task                                      │
│    File: app/workers/tasks.py                                        │
│    Function: run_recon_scan()                                        │
│    Lines: 16-140                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ├─► ScanJobRepository.update_scan_status()
                              │   └─► UPDATE scan_jobs SET status='running'
                              │
                              ├─► ReconPipeline.__init__()
                              │   File: app/services/pipeline.py (lines 20-100)
                              │   └─► Create job directory
                              │
                              └─► ReconPipeline.run_full_pipeline()
                                  File: app/services/pipeline.py (lines 101-150)

                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. Pipeline Execution                                                │
│    File: app/services/pipeline.py                                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ├─► enumerate_subdomains_enhanced()
                              │   Lines: 150-350
                              │   │
                              │   ├─► _run_subfinder_cli()
                              │   │   Lines: 150-180
                              │   │   └─► subprocess: subfinder
                              │   │
                              │   ├─► _run_amass_cli()
                              │   │   Lines: 230-250
                              │   │   └─► subprocess: amass
                              │   │
                              │   ├─► _run_assetfinder_cli()
                              │   │   Lines: 270-290
                              │   │   └─► subprocess: assetfinder
                              │   │
                              │   └─► _read_subdomains_file()
                              │       Lines: 468-476
                              │       └─► Return: List[str]
                              │
                              ├─► check_live_hosts_enhanced()
                              │   Lines: 400-550
                              │   │
                              │   ├─► _run_httprobe_cli()
                              │   │   Lines: 420-450
                              │   │   └─► subprocess: httprobe
                              │   │
                              │   ├─► _run_httpx_cli()
                              │   │   Lines: 470-520
                              │   │   └─► subprocess: httpx
                              │   │
                              │   └─► HttpxParser.parse_jsonl_file()
                              │       File: app/services/parsers.py (lines 113-180)
                              │       └─► Return: List[LiveHostResult]
                              │
                              ├─► capture_screenshots()
                              │   Lines: 750-820
                              │   │
                              │   └─► subprocess: gowitness
                              │       └─► Return: List[Dict]
                              │
                              └─► run_waf_detection()
                                  Lines: 900-1000
                                  │
                                  └─► subprocess: wafw00f (for each URL)
                                      └─► Return: List[Dict]

                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. Save Results to Database                                          │
│    File: app/workers/tasks.py                                        │
│    Lines: 56-140                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ├─► SubdomainRepository.bulk_create_subdomains()
                              │   File: app/storage/repo.py (lines 75-88)
                              │   └─► INSERT INTO subdomains (bulk)
                              │
                              ├─► SubdomainRepository.update_subdomain_status()
                              │   File: app/storage/repo.py (lines 90-104)
                              │   └─► UPDATE subdomains (for each live host)
                              │
                              ├─► ScreenshotRepository.create_screenshot()
                              │   File: app/storage/repo.py (lines 124-139)
                              │   └─► INSERT INTO screenshots (for each)
                              │
                              ├─► WafDetectionRepository.bulk_create()
                              │   File: app/storage/repo.py (lines 156-171)
                              │   └─► INSERT INTO waf_detections (bulk)
                              │
                              └─► ScanJobRepository.update_scan_status()
                                  └─► UPDATE scan_jobs SET status='completed'

                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. Return Results                                                    │
│    Celery stores result in Redis                                     │
│    Client can poll GET /api/v1/scans/{job_id}                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. DATA PROCESSING & STORAGE

### 5.1 Data Flow Diagram

```
CLI Tool Output → Parser → Repository → Database Table
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

subfinder        SubfinderParser      SubdomainRepository    subdomains
  │                    │                      │                    │
  ├─► subs.txt ───────►│                      │                    │
  │   (text file)      │                      │                    │
  │                    ├─► List[SubdomainResult]                   │
  │                    │                      │                    │
  │                    │                      ├─► bulk_create()    │
  │                    │                      │                    │
  │                    │                      └───────────────────►│
  │                                                                 │
  │                                                    INSERT INTO subdomains
  │                                                    (subdomain, discovered_by)

amass            AmassParser          SubdomainRepository    subdomains
  │                    │                      │                    │
  ├─► amass.txt ──────►│                      │                    │
  │   (FQDN list)      │                      │                    │
  │                    ├─► List[SubdomainResult]                   │
  │                    │                      │                    │
  │                    │                      ├─► bulk_create()    │
  │                    │                      │                    │
  │                    │                      └───────────────────►│

httpx            HttpxParser          SubdomainRepository    subdomains
  │                    │                      │                    │
  ├─► httpx.json ─────►│                      │                    │
  │   (JSONL)          │                      │                    │
  │                    ├─► List[LiveHostResult]                    │
  │                    │                      │                    │
  │                    │                      ├─► update_subdomain_status()
  │                    │                      │                    │
  │                    │                      └───────────────────►│
  │                                                                 │
  │                                                    UPDATE subdomains
  │                                                    SET is_live, http_status

gowitness         (No parser)          ScreenshotRepository   screenshots
  │                                           │                    │
  ├─► shots/*.png ────────────────────────────►│                   │
  │   (PNG files)                              │                   │
  │                                            ├─► create_screenshot()
  │                                            │                   │
  │                                            └──────────────────►│
  │                                                                │
  │                                                   INSERT INTO screenshots
  │                                                   (url, filename, file_path)

wafw00f          (JSON parsing)       WafDetectionRepository waf_detections
  │                                           │                    │
  ├─► JSON output ────────────────────────────►│                   │
  │   (in-memory)                              │                   │
  │                                            ├─► bulk_create()   │
  │                                            │                   │
  │                                            └──────────────────►│
  │                                                                │
  │                                                   INSERT INTO waf_detections
  │                                                   (url, has_waf, waf_name)

SourceLeakHacker (CSV + STDOUT)       LeakDetectionRepository leak_detections
  │                                           │                    │
  ├─► 200.csv ────────────────────────────────►│                   │
  ├─► 403.csv                                  │                   │
  ├─► 502.csv                                  │                   │
  │   (CSV files)                              │                   │
  │                                            ├─► bulk_create()   │
  │                                            │                   │
  │                                            └──────────────────►│
  │                                                                │
  │                                                   INSERT INTO leak_detections
  │                                                   (base_url, leaked_file_url, http_status)
```

### 5.2 Parser Details

#### **SubfinderParser**

**File:** `app/services/parsers.py` (lines 29-49)

**Input Format:** Plain text (one subdomain per line)
```
www.example.com
api.example.com
mail.example.com
```

**Output:** `List[SubdomainResult]`
```python
[
    SubdomainResult(subdomain="www.example.com", source="subfinder"),
    SubdomainResult(subdomain="api.example.com", source="subfinder"),
    SubdomainResult(subdomain="mail.example.com", source="subfinder")
]
```

**Parsing Logic:**
- Strip whitespace
- Filter out lines starting with `[` (log messages)
- Validate domain format (must contain `.`)
- Convert to lowercase
- Deduplicate

---

#### **HttpxParser**

**File:** `app/services/parsers.py` (lines 113-180)

**Input Format:** JSONL (JSON Lines - one JSON object per line)
```json
{"url":"https://www.example.com","status_code":200,"content_length":1234,"title":"Example"}
{"url":"http://api.example.com","status_code":403,"content_length":0,"title":"Forbidden"}
```

**Output:** `List[LiveHostResult]`
```python
[
    LiveHostResult(
        url="https://www.example.com",
        status_code=200,
        is_live=True,
        content_length=1234,
        title="Example",
        tech=[],
        response_time="123ms"
    ),
    LiveHostResult(
        url="http://api.example.com",
        status_code=403,
        is_live=True,  # 403 is considered "live"
        content_length=0,
        title="Forbidden",
        tech=[],
        response_time="45ms"
    )
]
```

**Parsing Logic:**
- Read file line by line
- Parse each line as JSON
- Extract fields: url, status_code, content_length, title, tech, response_time
- Determine `is_live` based on status code:
  - **Live:** 200, 301, 302, 304, 307, 308, 400, 401, 403, 500, 501, 502, 503, 504
  - **Dead:** 404, 405, or any other code
- Handle JSON parsing errors gracefully

---

#### **SourceLeakHacker Parser**

**File:** `app/services/pipeline.py` (lines 638-724)

**Input Format 1:** STDOUT (regex parsing)
```
[200] 0 0.07s text/html https://example.com/.git/config
[403] 0 0.05s text/html https://example.com/.env
[502] 0 0.12s text/html https://example.com/backup.sql
```

**Input Format 2:** CSV files (200.csv, 403.csv, 502.csv, etc.)
```csv
https://example.com/.git/config,text/html,1234
https://example.com/.htaccess,text/plain,567
```

**Parsing Logic:**
```python
# Parse STDOUT with regex
pattern = r'\[(\d+)\]\s+(\d+)\s+([\d.]+)s?\s+(\S+)\s+(.+)'
match = re.match(pattern, line)

if match:
    http_status = int(match.group(1))  # 200, 403, 502, etc.
    file_size = int(match.group(2))
    response_time = match.group(3)
    content_type = match.group(4)
    url = match.group(5)

    # Skip 404 status codes (not actual leaks)
    if http_status == 404:
        continue

    # Determine severity based on HTTP status
    if http_status == 200:
        severity = "high"  # Accessible leak
    elif http_status == 403:
        severity = "medium"  # Forbidden but exists
    else:
        severity = "low"  # Other status codes

    results.append({
        'base_url': base_url,
        'leaked_file_url': url,
        'file_type': content_type,
        'severity': severity,
        'file_size': file_size,
        'http_status': http_status
    })
```

**Output:** `List[Dict]`
```python
[
    {
        'base_url': 'https://example.com',
        'leaked_file_url': 'https://example.com/.git/config',
        'file_type': 'text/html',
        'severity': 'high',
        'file_size': 1234,
        'http_status': 200
    },
    {
        'base_url': 'https://example.com',
        'leaked_file_url': 'https://example.com/.env',
        'file_type': 'text/html',
        'severity': 'medium',
        'file_size': 0,
        'http_status': 403
    }
]
```

---

### 5.3 Repository Layer

The repository layer provides an abstraction over database operations.

**File:** `app/storage/repo.py` (202 lines)

#### **ScanJobRepository**

**Methods:**
- `create_scan_job(job_id, domain)` - Create new scan
- `get_scan_job(job_id)` - Get scan by job_id
- `update_scan_status(job_id, status)` - Update status
- `update_task_id(job_id, task_id)` - Store Celery task ID
- `update_completed_at(job_id)` - Set completion timestamp
- `get_recent_scans(limit, offset)` - Paginated scan list

#### **SubdomainRepository**

**Methods:**
- `create_subdomain(scan_job_id, subdomain, discovered_by)` - Create single subdomain
- `bulk_create_subdomains(scan_job_id, subdomains, discovered_by)` - Bulk insert
- `update_subdomain_status(subdomain_id, status, is_live, http_status, response_time)` - Update status
- `get_subdomains_by_job(job_id)` - Get all subdomains for a scan
- `get_live_subdomains_by_job(job_id)` - Get only live subdomains

#### **ScreenshotRepository**

**Methods:**
- `create_screenshot(scan_job_id, url, filename, file_path, subdomain_id, file_size)` - Create screenshot record
- `get_screenshots_by_job(job_id)` - Get all screenshots for a scan
- `get_screenshots_by_subdomain(subdomain_id)` - Get screenshots for specific subdomain

#### **WafDetectionRepository**

**Methods:**
- `bulk_create(scan_job_id, detections)` - Bulk insert WAF detections

#### **LeakDetectionRepository**

**Methods:**
- `bulk_create(scan_job_id, leaks)` - Bulk insert leak detections

---

## 6. SPECIAL FEATURES

### 6.1 Selective Leak Scanning

**Purpose:** Allow users to manually select specific URLs for leak scanning (instead of scanning all live hosts)

**Workflow:**

```
User selects URLs → API endpoint → Celery task → SourceLeakHacker → Database
```

**API Endpoint:** `POST /api/v1/scans/{job_id}/leak-scan`

**File:** `app/routers/scans.py` (lines 440-540)

**Request Body:**
```json
{
    "urls": [
        "https://www.example.com",
        "https://api.example.com"
    ],
    "mode": "tiny"
}
```

**Response:**
```json
{
    "task_id": "abc123...",
    "job_id": "uuid...",
    "urls_to_scan": 2,
    "mode": "tiny",
    "message": "Leak scan started on 2 URLs in 'tiny' mode",
    "status": "started"
}
```

**Celery Task:** `run_sourceleakhacker_check`

**File:** `app/workers/tasks.py` (lines 460-555)

**Queue:** `leak_check` (separate from full pipeline)

**Code Flow:**
```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_sourceleakhacker_check(self, job_id: str, selected_urls: List[str], mode: str = "tiny"):
    # 1. Get scan job
    scan_job = scan_repo.get_scan_job(job_id)

    # 2. Prepare live hosts data
    live_hosts = [{'url': url, 'is_live': True} for url in selected_urls]

    # 3. Run SourceLeakHacker
    leak_detections = loop.run_until_complete(
        pipeline._run_sourceleakhacker_cli(
            live_hosts=live_hosts,
            waf_detections=[],
            mode=mode,
            selected_urls=selected_urls
        )
    )

    # 4. Save leak detections to database
    if leak_detections:
        leak_repo = LeakDetectionRepository(db)
        leak_repo.bulk_create(scan_job.id, leak_detections)

    # 5. Return results
    return {
        'job_id': job_id,
        'status': 'completed',
        'urls_scanned': len(selected_urls),
        'leaks_found': len(leak_detections),
        'mode': mode
    }
```

**Frontend Integration:**

**File:** `web/app.js` (lines 580-820)

**UI Components:**
- URL selection checkboxes
- Scan mode dropdown (tiny/full)
- Submit button
- Progress bar
- Results display

**Key Functions:**
- `loadSelectiveScanUrls(scanData)` - Load available URLs
- `toggleUrlSelection(url)` - Handle checkbox clicks
- `submitSelectiveScan()` - Submit scan request
- `startSelectiveScanMonitoring(taskId)` - Poll for results
- `showSelectiveScanResults(scanData)` - Display results

---

### 6.2 Manual Subdomain Addition

**Purpose:** Allow users to manually add subdomains that weren't discovered by automated tools

**API Endpoint:** `POST /api/v1/scans/{job_id}/subdomains`

**File:** `app/routers/scans.py` (lines 542-654)

**Request Body:**
```json
{
    "subdomain": "admin.example.com",
    "is_live": true,
    "http_status": 200
}
```

**Response:**
```json
{
    "id": 12345,
    "subdomain": "admin.example.com",
    "status": "live",
    "is_live": true,
    "http_status": 200,
    "discovered_by": "manual",
    "message": "Subdomain 'admin.example.com' added successfully"
}
```

**Validation Logic:**
```python
# 1. Remove protocol if present
if subdomain_str.startswith('http://') or subdomain_str.startswith('https://'):
    parsed = urlparse(subdomain_str)
    subdomain_str = parsed.netloc

# 2. Validate subdomain format
if not subdomain_str or '.' not in subdomain_str:
    raise HTTPException(400, "Invalid subdomain format")

# 3. Validate subdomain belongs to scan's domain
if not subdomain_str.endswith(scan_job.domain):
    raise HTTPException(400, f"Subdomain must belong to {scan_job.domain}")

# 4. Check for duplicates
existing_subdomains = subdomain_repo.get_subdomains_by_job(job_id)
for existing in existing_subdomains:
    if existing.subdomain.lower() == subdomain_str.lower():
        raise HTTPException(409, "Subdomain already exists")

# 5. Create subdomain
subdomain = subdomain_repo.create_subdomain(
    scan_job_id=scan_job.id,
    subdomain=subdomain_str,
    discovered_by="manual"
)
```

**Frontend Integration:**

**File:** `web/index.html` (lines 97-155)

**UI Components:**
- Collapsible form
- Subdomain input field
- Is Live dropdown (Auto-detect, Yes, No)
- HTTP Status input field
- Submit button
- Success/error messages

**File:** `web/app.js` (lines 838-937)

**Key Functions:**
- `toggleManualSubdomainForm()` - Show/hide form
- `addSubdomainManually()` - Submit form and handle response

---

### 6.3 WAF Detection Integration

**Purpose:** Detect Web Application Firewalls protecting live hosts

**Tool:** wafw00f (Python-based WAF detection tool)

**Integration Point:** Stage 4 of full pipeline

**File:** `app/services/pipeline.py` (lines 900-1000)

**CLI Command:**
```bash
wafw00f https://www.example.com -o waf_results.json -f json
```

**Parsing Logic:**
```python
# Parse JSON output from wafw00f
waf_data = json.loads(stdout)

waf_detection = {
    'url': url,
    'has_waf': len(waf_data.get('firewall', [])) > 0,
    'waf_name': waf_data.get('firewall', [None])[0],
    'waf_manufacturer': waf_data.get('manufacturer')
}
```

**Database Storage:**

**Table:** `waf_detections`

**Columns:**
- `id` - Primary key
- `scan_job_id` - Foreign key to scan_jobs
- `url` - URL that was checked
- `has_waf` - Boolean (True if WAF detected)
- `waf_name` - Name of WAF (e.g., "Cloudflare", "AWS WAF")
- `waf_manufacturer` - Manufacturer (e.g., "Cloudflare Inc.")
- `created_at` - Timestamp

**Frontend Display:**

**File:** `web/app.js` (lines 201-237)

**Function:** `displayWafDetections(waf_detections)`

**UI:** Table with columns: URL, WAF Status, WAF Name, Manufacturer

---

### 6.4 HTTP Status Code Capture & Display

**Purpose:** Show HTTP status codes for both live hosts and leak detections

**Implementation:**

#### **For Live Hosts:**

**Captured by:** httpx tool

**File:** `app/services/pipeline.py` (lines 470-520)

**Stored in:** `subdomains.http_status` column

**Frontend Display:**

**File:** `web/app.js` (lines 160-199)

**Function:** `displaySubdomains(subdomains)`

**UI:** Badge with color coding:
- **200** - Green badge
- **403** - Yellow badge
- **Other** - Gray badge

#### **For Leak Detections:**

**Captured by:** SourceLeakHacker tool

**File:** `app/services/pipeline.py` (lines 638-724)

**Stored in:** `leak_detections.http_status` column

**Frontend Display:**

**File:** `web/app.js` (lines 205-237)

**Function:** `displayLeakDetections(leaks)`

**UI:** Badge with color coding (same as live hosts)

**CSS Styling:**

**File:** `web/styles.css` (lines 400-450)

```css
.status-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 600;
}

.status-200 {
    background: rgba(34, 197, 94, 0.2);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

.status-403 {
    background: rgba(234, 179, 8, 0.2);
    color: #eab308;
    border: 1px solid rgba(234, 179, 8, 0.3);
}

.status-other {
    background: rgba(161, 161, 170, 0.2);
    color: #a1a1aa;
    border: 1px solid rgba(161, 161, 170, 0.3);
}
```

---

## 7. DATABASE SCHEMA

### 7.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          scan_jobs                                   │
├─────────────────────────────────────────────────────────────────────┤
│ PK │ id                INTEGER                                       │
│    │ job_id            VARCHAR(36)  UNIQUE                           │
│    │ task_id           VARCHAR(255) NULLABLE                         │
│    │ domain            VARCHAR(255)                                  │
│    │ status            ENUM(pending, running, completed, failed)     │
│    │ created_at        TIMESTAMP                                     │
│    │ updated_at        TIMESTAMP                                     │
│    │ completed_at      TIMESTAMP NULLABLE                            │
│    │ error_message     TEXT NULLABLE                                 │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              │
        ┌─────────────────────┼─────────────────────┬─────────────────┐
        │                     │                     │                 │
        ▼                     ▼                     ▼                 ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  subdomains   │   │ screenshots   │   │waf_detections │   │leak_detections│
├───────────────┤   ├───────────────┤   ├───────────────┤   ├───────────────┤
│PK│id          │   │PK│id          │   │PK│id          │   │PK│id          │
│FK│scan_job_id │   │FK│scan_job_id │   │FK│scan_job_id │   │FK│scan_job_id │
│  │subdomain   │   │FK│subdomain_id│   │  │url         │   │  │base_url    │
│  │status      │   │  │url         │   │  │has_waf     │   │  │leaked_file │
│  │is_live     │   │  │filename    │   │  │waf_name    │   │  │file_type   │
│  │http_status │   │  │file_path   │   │  │waf_mfr     │   │  │severity    │
│  │response_tm │   │  │file_size   │   │  │created_at  │   │  │file_size   │
│  │discovered  │   │  │created_at  │   └───────────────┘   │  │http_status │
│  │created_at  │   └───────────────┘                       │  │created_at  │
└───────────────┘                                            └───────────────┘
        │
        │ 1:N
        │
        ▼
┌───────────────┐
│ screenshots   │
│ (subdomain)   │
└───────────────┘
```

### 7.2 Table Definitions

#### **scan_jobs**

**File:** `app/storage/models.py` (lines 27-45)

```python
class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, index=True, nullable=False)
    task_id = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=False)
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    subdomains = relationship("Subdomain", back_populates="scan_job", cascade="all, delete-orphan")
    screenshots = relationship("Screenshot", back_populates="scan_job", cascade="all, delete-orphan")
    waf_detections = relationship("WafDetection", back_populates="scan_job", cascade="all, delete-orphan")
    leak_detections = relationship("LeakDetection", back_populates="scan_job", cascade="all, delete-orphan")
```

**Indexes:**
- `job_id` (UNIQUE)
- `id` (PRIMARY KEY)

**Cascade Delete:** Deleting a scan job deletes all related subdomains, screenshots, WAF detections, and leak detections

---

#### **subdomains**

**File:** `app/storage/models.py` (lines 48-64)

```python
class Subdomain(Base):
    __tablename__ = "subdomains"

    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=False)
    subdomain = Column(String(255), nullable=False)
    status = Column(Enum(SubdomainStatus), default=SubdomainStatus.FOUND)
    is_live = Column(Boolean, default=False)
    http_status = Column(Integer, nullable=True)
    response_time = Column(String(50), nullable=True)
    discovered_by = Column(String(100), nullable=True)  # "subfinder", "amass", "manual", etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan_job = relationship("ScanJob", back_populates="subdomains")
    screenshots = relationship("Screenshot", back_populates="subdomain")
```

**Indexes:**
- `id` (PRIMARY KEY)
- `scan_job_id` (FOREIGN KEY)

**Status Values:**
- `FOUND` - Discovered but not yet checked
- `LIVE` - Confirmed live
- `DEAD` - Not responding

---

#### **screenshots**

**File:** `app/storage/models.py` (lines 67-82)

```python
class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=False)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"), nullable=True)
    url = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan_job = relationship("ScanJob", back_populates="screenshots")
    subdomain = relationship("Subdomain", back_populates="screenshots")
```

**File Storage:** Screenshots are stored in `./jobs/{job_id}/shots/*.png`

---

#### **waf_detections**

**File:** `app/storage/models.py` (lines 85-98)

```python
class WafDetection(Base):
    __tablename__ = "waf_detections"

    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=False)
    url = Column(String(500), nullable=False)
    has_waf = Column(Boolean, default=False)
    waf_name = Column(String(255), nullable=True)
    waf_manufacturer = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    scan_job = relationship("ScanJob", back_populates="waf_detections")
```

---

#### **leak_detections**

**File:** `app/storage/models.py` (lines 101-116)

```python
class LeakDetection(Base):
    __tablename__ = "leak_detections"

    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=False)
    base_url = Column(String(500), nullable=False)
    leaked_file_url = Column(String(1000), nullable=False)
    file_type = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)  # "high", "medium", "low"
    file_size = Column(Integer, nullable=True)
    http_status = Column(Integer, nullable=True)  # ✅ ADDED (Issue #1 fix)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    scan_job = relationship("ScanJob", back_populates="leak_detections")
```

**Severity Levels:**
- `high` - HTTP 200 (accessible leak)
- `medium` - HTTP 403 (forbidden but exists)
- `low` - Other status codes

---

## 8. API ENDPOINTS REFERENCE

### 8.1 Complete API List

**Base URL:** `http://localhost:8000/api/v1`

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| **POST** | `/scans` | Create new scan | `{domain}` | `{job_id, status, message}` |
| **POST** | `/scans/bulk` | Bulk scan submission | `{domains[]}` | `{jobs[]}` |
| **GET** | `/scans` | List all scans | Query: `page`, `limit` | `{scans[], total, page, limit}` |
| **GET** | `/scans/{job_id}` | Get scan details | - | `{job_id, domain, status, subdomains[], ...}` |
| **POST** | `/scans/{job_id}/leak-scan` | Selective leak scan | `{urls[], mode}` | `{task_id, status}` |
| **POST** | `/scans/{job_id}/subdomains` | Add subdomain manually | `{subdomain, is_live?, http_status?}` | `{id, subdomain, status}` |

### 8.2 Detailed Endpoint Documentation

#### **POST /api/v1/scans**

**Purpose:** Create a new reconnaissance scan

**File:** `app/routers/scans.py` (lines 97-130)

**Request:**
```json
{
    "domain": "example.com"
}
```

**Response (200 OK):**
```json
{
    "job_id": "269ac526-2ab5-4db9-b57b-2a8ca67d69a4",
    "domain": "example.com",
    "status": "pending",
    "message": "Scan job created successfully. Task ID: abc123..."
}
```

**Validation:**
- Domain must not be empty
- Domain is converted to lowercase
- Whitespace is trimmed

**Side Effects:**
- Creates record in `scan_jobs` table
- Dispatches Celery task `run_recon_scan`
- Updates `task_id` in database

---

#### **POST /api/v1/scans/bulk**

**Purpose:** Submit multiple domains for scanning

**File:** `app/routers/scans.py` (lines 133-180)

**Request:**
```json
{
    "domains": [
        "example.com",
        "test.com",
        "demo.org"
    ]
}
```

**Response (200 OK):**
```json
{
    "total_submitted": 3,
    "jobs": [
        {
            "job_id": "uuid-1",
            "domain": "example.com",
            "status": "pending",
            "task_id": "task-1"
        },
        {
            "job_id": "uuid-2",
            "domain": "test.com",
            "status": "pending",
            "task_id": "task-2"
        },
        {
            "job_id": "uuid-3",
            "domain": "demo.org",
            "status": "pending",
            "task_id": "task-3"
        }
    ]
}
```

**Limits:**
- Maximum 100 domains per request

---

#### **GET /api/v1/scans**

**Purpose:** List all scans with pagination

**File:** `app/routers/scans.py` (lines 183-230)

**Query Parameters:**
- `page` (default: 1)
- `limit` (default: 20, max: 100)

**Request:**
```
GET /api/v1/scans?page=1&limit=20
```

**Response (200 OK):**
```json
{
    "scans": [
        {
            "job_id": "uuid-1",
            "domain": "example.com",
            "status": "completed",
            "created_at": "2025-11-01T10:00:00",
            "completed_at": "2025-11-01T11:00:00",
            "subdomains_count": 150,
            "live_hosts_count": 45,
            "screenshots_count": 42,
            "waf_detections_count": 10,
            "leak_detections_count": 5
        }
    ],
    "total": 100,
    "page": 1,
    "limit": 20,
    "total_pages": 5
}
```

---

#### **GET /api/v1/scans/{job_id}**

**Purpose:** Get detailed information about a specific scan

**File:** `app/routers/scans.py` (lines 233-420)

**Request:**
```
GET /api/v1/scans/269ac526-2ab5-4db9-b57b-2a8ca67d69a4
```

**Response (200 OK):**
```json
{
    "job_id": "269ac526-2ab5-4db9-b57b-2a8ca67d69a4",
    "domain": "fpt.ai",
    "status": "completed",
    "created_at": "2025-11-01T10:00:00",
    "completed_at": "2025-11-01T11:00:00",
    "subdomains": [
        {
            "id": 1,
            "subdomain": "www.fpt.ai",
            "status": "live",
            "is_live": true,
            "http_status": 200,
            "response_time": "123ms",
            "discovered_by": "subfinder"
        }
    ],
    "screenshots": [
        {
            "id": 1,
            "url": "https://www.fpt.ai",
            "filename": "https-www.fpt.ai.png",
            "file_path": "jobs/269ac526.../shots/https-www.fpt.ai.png",
            "file_size": 123456
        }
    ],
    "waf_detections": [
        {
            "id": 1,
            "url": "https://www.fpt.ai",
            "has_waf": true,
            "waf_name": "Cloudflare",
            "waf_manufacturer": "Cloudflare Inc."
        }
    ],
    "leak_detections": [
        {
            "id": 1,
            "base_url": "https://www.fpt.ai",
            "leaked_file_url": "https://www.fpt.ai/.git/config",
            "file_type": "text/html",
            "severity": "high",
            "file_size": 1234,
            "http_status": 200
        }
    ]
}
```

**Error Responses:**
- `404 Not Found` - Scan job not found

---

#### **POST /api/v1/scans/{job_id}/leak-scan**

**Purpose:** Run selective leak scanning on specific URLs

**File:** `app/routers/scans.py` (lines 440-540)

**Request:**
```json
{
    "urls": [
        "https://www.example.com",
        "https://api.example.com"
    ],
    "mode": "tiny"
}
```

**Response (200 OK):**
```json
{
    "task_id": "abc123-def456-...",
    "job_id": "269ac526-2ab5-4db9-b57b-2a8ca67d69a4",
    "urls_to_scan": 2,
    "mode": "tiny",
    "message": "Leak scan started on 2 URLs in 'tiny' mode",
    "status": "started"
}
```

**Validation:**
- `urls` must be a non-empty list
- `mode` must be "tiny" or "full" (default: "tiny")

**Side Effects:**
- Dispatches Celery task `run_sourceleakhacker_check` to `leak_check` queue
- Does NOT block (returns immediately with task_id)

---

#### **POST /api/v1/scans/{job_id}/subdomains** ✅ NEW

**Purpose:** Manually add a subdomain to an existing scan

**File:** `app/routers/scans.py` (lines 542-654)

**Request:**
```json
{
    "subdomain": "admin.example.com",
    "is_live": true,
    "http_status": 200
}
```

**Response (200 OK):**
```json
{
    "id": 12345,
    "subdomain": "admin.example.com",
    "status": "live",
    "is_live": true,
    "http_status": 200,
    "discovered_by": "manual",
    "message": "Subdomain 'admin.example.com' added successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid subdomain format
- `400 Bad Request` - Subdomain doesn't belong to scan's domain
- `404 Not Found` - Scan job not found
- `409 Conflict` - Subdomain already exists

**Validation:**
- Removes `http://` or `https://` prefix if present
- Removes trailing slashes
- Validates subdomain format (must contain `.`)
- Validates subdomain belongs to scan's domain
- Checks for duplicates (case-insensitive)

**Side Effects:**
- Creates record in `subdomains` table with `discovered_by="manual"`
- Updates `status` to `live` if `is_live=true`
- Sets `http_status` if provided

---

## 9. CELERY TASK QUEUE ARCHITECTURE

### 9.1 Queue Configuration

**File:** `app/workers/celery_app.py` (lines 40-54)

**Queues:**

| Queue Name | Purpose | Tasks | Priority |
|------------|---------|-------|----------|
| `recon_full` | Full reconnaissance pipeline | `run_recon_scan` | High |
| `recon_enum` | Subdomain enumeration only | `run_subdomain_enumeration` | Medium |
| `recon_check` | Live host checking only | `run_live_host_check` | Medium |
| `recon_screenshot` | Screenshot capture only | `run_screenshot_capture` | Low |
| `waf_check` | WAF detection | `run_waf_check` | Low |
| `leak_check` | Source leak scanning | `run_sourceleakhacker_check` | Medium |
| `maintenance` | Cleanup tasks | `cleanup_old_jobs` | Low |

**Task Routing:**
```python
task_routes = {
    'app.workers.tasks.run_recon_scan': {'queue': 'recon_full'},
    'app.workers.tasks.run_subdomain_enumeration': {'queue': 'recon_enum'},
    'app.workers.tasks.run_live_host_check': {'queue': 'recon_check'},
    'app.workers.tasks.run_screenshot_capture': {'queue': 'recon_screenshot'},
    'app.workers.tasks.run_waf_check': {'queue': 'waf_check'},
    'app.workers.tasks.run_sourceleakhacker_check': {'queue': 'leak_check'},
    'app.workers.tasks.cleanup_old_jobs': {'queue': 'maintenance'},
}
```

### 9.2 Worker Configuration

**Start Command:**
```bash
celery -A app.workers.celery_app worker --loglevel=info --pool=solo -Q recon_full,leak_check,waf_check
```

**Configuration:**
- `--pool=solo` - Windows compatibility (avoids billiard PermissionError)
- `-Q recon_full,leak_check,waf_check` - Listen to specific queues
- `--loglevel=info` - Log level

**Multiple Workers:**
```bash
# Worker 1: Full pipeline
celery -A app.workers.celery_app worker --pool=solo -Q recon_full -n worker1@%h

# Worker 2: Leak scanning
celery -A app.workers.celery_app worker --pool=solo -Q leak_check -n worker2@%h

# Worker 3: WAF detection
celery -A app.workers.celery_app worker --pool=solo -Q waf_check -n worker3@%h
```

### 9.3 Task Retry Configuration

**File:** `app/workers/celery_app.py` (lines 17-36)

```python
celery_app.conf.update(
    task_default_retry_delay=60,  # Retry after 60 seconds
    task_max_retries=3,            # Maximum 3 retries
    task_acks_late=True,           # Acknowledge after task completion
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    task_time_limit=2700,          # 45 minutes hard limit
    task_soft_time_limit=2400,     # 40 minutes soft limit
)
```

**Retry Example:**
```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_sourceleakhacker_check(self, job_id, selected_urls, mode="tiny"):
    try:
        # ... task logic ...
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
```

---

## 10. FILE STRUCTURE & ORGANIZATION

### 10.1 Project Directory Tree

```
reconnaissance-system/
│
├── app/                                # Main application package
│   ├── __init__.py
│   ├── main.py                         # FastAPI application entry point
│   ├── deps.py                         # Configuration & dependencies
│   │
│   ├── routers/                        # API route handlers
│   │   ├── __init__.py
│   │   └── scans.py                    # Scan endpoints
│   │
│   ├── services/                       # Business logic layer
│   │   ├── __init__.py
│   │   ├── pipeline.py                 # Pipeline orchestration
│   │   └── parsers.py                  # CLI tool output parsers
│   │
│   ├── storage/                        # Data access layer
│   │   ├── __init__.py
│   │   ├── models.py                   # SQLAlchemy models
│   │   └── repo.py                     # Repository pattern
│   │
│   └── workers/                        # Celery workers
│       ├── __init__.py
│       ├── celery_app.py               # Celery configuration
│       └── tasks.py                    # Celery task definitions
│
├── web/                                # Frontend web interface
│   ├── index.html                      # Main HTML page
│   ├── app.js                          # JavaScript logic
│   └── styles.css                      # CSS styling
│
├── jobs/                               # Job output directory (created at runtime)
│   └── {job_id}/                       # Per-job directory
│       ├── subs.txt                    # Discovered subdomains
│       ├── live.txt                    # Live hosts
│       ├── httpx.json                  # httpx results
│       ├── shots/                      # Screenshots directory
│       │   └── *.png                   # Screenshot files
│       └── *.csv                       # SourceLeakHacker CSV files
│
├── alembic/                            # Database migrations
│   ├── versions/                       # Migration scripts
│   └── env.py                          # Alembic configuration
│
├── scripts/                            # Utility scripts
│   ├── clear_redis_corrupted_data.py   # Redis cleanup
│   └── setup_database.py               # Database initialization
│
├── docker/                             # Docker configuration
│   ├── Dockerfile.api                  # API server image
│   ├── Dockerfile.worker               # Celery worker image
│   └── docker-compose.yml              # Multi-container setup
│
├── requirements.txt                    # Python dependencies
├── .env                                # Environment variables (not in git)
├── .gitignore                          # Git ignore rules
├── README.md                           # Project documentation
│
├── start_all.ps1                       # PowerShell: Start all services
├── stop_all.ps1                        # PowerShell: Stop all services
├── start_api.bat                       # Batch: Start API server
└── start_worker.bat                    # Batch: Start Celery worker
```

### 10.2 Key File Descriptions

| File | Lines | Purpose |
|------|-------|---------|
| `app/main.py` | 143 | FastAPI app initialization, CORS, static files |
| `app/deps.py` | 99 | Settings, database connection, tool paths |
| `app/routers/scans.py` | 654 | API endpoints for scan operations |
| `app/services/pipeline.py` | 1000+ | Pipeline orchestration, CLI tool execution |
| `app/services/parsers.py` | 180 | Output parsers for CLI tools |
| `app/storage/models.py` | 116 | SQLAlchemy ORM models |
| `app/storage/repo.py` | 202 | Repository pattern for database access |
| `app/workers/celery_app.py` | 54 | Celery configuration, task routing |
| `app/workers/tasks.py` | 555 | Celery task definitions |
| `web/index.html` | 200+ | Frontend HTML structure |
| `web/app.js` | 937 | Frontend JavaScript logic |
| `web/styles.css` | 1060 | Frontend CSS styling |
| `requirements.txt` | 32 | Python package dependencies |

---

## 📊 SUMMARY STATISTICS

### Project Metrics

- **Total Python Files:** 12
- **Total Lines of Code:** ~5,000+
- **External CLI Tools:** 8
- **Database Tables:** 5
- **API Endpoints:** 6
- **Celery Queues:** 7
- **Celery Tasks:** 7

### Technology Count

- **Backend:** Python 3.13, FastAPI, SQLAlchemy, Celery
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Database:** PostgreSQL
- **Message Broker:** Redis
- **CLI Tools:** Go (6), Python (2)

### Feature Highlights

✅ **Full Reconnaissance Pipeline** - 4-stage automated workflow
✅ **Selective Leak Scanning** - User-selected URL scanning
✅ **Manual Subdomain Addition** - Add missed subdomains
✅ **WAF Detection** - Identify web application firewalls
✅ **HTTP Status Display** - Color-coded status badges
✅ **Screenshot Capture** - Visual evidence of live hosts
✅ **Bulk Scanning** - Submit multiple domains at once
✅ **Pagination** - Efficient data browsing
✅ **Progress Tracking** - Real-time task monitoring
✅ **Error Handling** - Retry mechanisms and error logging

---

## 🎯 CONCLUSION

This reconnaissance system is a **comprehensive, production-ready solution** for subdomain enumeration, live host detection, screenshot capture, WAF detection, and source code leak scanning.

**Key Strengths:**
1. **Modular Architecture** - Clear separation of concerns (API, services, storage, workers)
2. **Scalable Design** - Celery task queues allow horizontal scaling
3. **Robust Error Handling** - Retry mechanisms, timeout handling, exception logging
4. **User-Friendly Interface** - Clean web dashboard with real-time updates
5. **Flexible Scanning** - Both automated full pipeline and manual selective scanning
6. **Comprehensive Data Storage** - All results stored in PostgreSQL for analysis

**Recent Improvements:**
- ✅ Fixed HTTP status code display in leak detections
- ✅ Added manual subdomain addition feature
- ✅ Improved SourceLeakHacker parsing (all CSV files, all status codes)
- ✅ Removed 404/405 from live status codes
- ✅ Increased SourceLeakHacker timeout to 2800 seconds

**Next Steps for Enhancement:**
1. Add export functionality (CSV, JSON, PDF reports)
2. Implement user authentication and multi-tenancy
3. Add email notifications for scan completion
4. Create API rate limiting
5. Add more CLI tools (nuclei, nmap, etc.)
6. Implement caching for frequently scanned domains
7. Add scheduled/recurring scans

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-01
**Author:** AI Assistant (Augment Agent)
**Project:** Subdomain Reconnaissance & Screenshot Capture System


