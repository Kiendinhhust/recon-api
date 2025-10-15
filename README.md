# Recon API - Subdomain Scanner

A comprehensive subdomain reconnaissance and screenshot capture API built with FastAPI, Celery, and modern recon tools.

## Features

- **Subdomain Enumeration**: Uses multiple tools (subfinder, amass, assetfinder) for comprehensive discovery
- **Live Host Detection**: Validates discovered subdomains with httpx
- **Screenshot Capture**: Automatically captures screenshots of live hosts using gowitness
- **Async Processing**: Background job processing with Celery and Redis
- **REST API**: Full REST API with Swagger documentation
- **Web Interface**: Simple web interface for easy interaction
- **Docker Support**: Complete containerized deployment

## Architecture

```
recon-api/
├── app/
│   ├── main.py              # FastAPI app with Swagger docs
│   ├── deps.py              # CORS, settings, database config
│   ├── routers/
│   │   └── scans.py         # REST endpoints for scan operations
│   ├── services/
│   │   ├── pipeline.py      # Tool orchestration pipeline
│   │   └── parsers.py       # Output parsers for each tool
│   ├── workers/
│   │   ├── celery_app.py    # Celery configuration
│   │   └── tasks.py         # Background task definitions
│   └── storage/
│       ├── models.py        # SQLAlchemy database models
│       └── repo.py          # Repository pattern for data access
├── jobs/                    # Job output directory
│   └── {job_id}/
│       ├── subs.txt         # Discovered subdomains
│       ├── live.txt         # Live hosts
│       └── shots/           # Screenshots
├── docker/
│   ├── Dockerfile.api       # API container
│   └── Dockerfile.worker    # Worker container
└── docker-compose.yml       # Complete stack deployment
```

## Quick Start

### Using Docker (Recommended)

1. **Clone and setup**:
```bash
git clone <repository>
cd recon-api
cp .env.example .env
```

2. **Start the stack**:
```bash
docker-compose up -d
```

3. **Initialize database**:
```bash
docker-compose exec api alembic upgrade head
```

4. **Access the application**:
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Celery monitoring: http://localhost:5555

### Manual Installation

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Install recon tools**:
```bash
# Install Go tools
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/tomnomnom/assetfinder@latest
go install github.com/tomnomnom/anew@latest
go install github.com/sensepost/gowitness@latest

# Install Amass
wget https://github.com/owasp-amass/amass/releases/latest/download/amass_linux_amd64.zip
unzip amass_linux_amd64.zip
sudo mv amass_linux_amd64/amass /usr/local/bin/
```

3. **Setup services**:
```bash
# Start PostgreSQL and Redis
sudo systemctl start postgresql redis

# Create database
createdb recon_db

# Run migrations
alembic upgrade head
```

4. **Start services**:
```bash
# Terminal 1: API server
uvicorn app.main:app --reload

# Terminal 2: Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3: Celery flower (optional)
celery -A app.workers.celery_app flower
```

## API Usage

### Start a Scan

```bash
curl -X POST "http://localhost:8000/api/v1/scans" \
     -H "Content-Type: application/json" \
     -d '{"domain": "example.com"}'
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "domain": "example.com",
  "status": "pending",
  "message": "Scan job created successfully"
}
```

### Check Scan Results

```bash
curl "http://localhost:8000/api/v1/scans/{job_id}"
```

### List Recent Scans

```bash
curl "http://localhost:8000/api/v1/scans"
```

## Configuration

Environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JOBS_DIRECTORY`: Directory for storing scan outputs
- Tool paths: `SUBFINDER_PATH`, `AMASS_PATH`, etc.

## Enhanced Pipeline Flow

### 1. Subdomain Enumeration (Multi-tool approach)
```bash
# Step 1: subfinder for comprehensive passive discovery
subfinder -d example.com -silent -o subs.txt

# Step 2: amass for additional passive sources
amass enum -passive -d example.com -o amass.txt
cat amass.txt | anew subs.txt

# Step 3: assetfinder for quick OSINT sources
assetfinder --subs-only example.com | anew subs.txt
```

### 2. Live Host Detection (Two-stage approach)
```bash
# Stage 1: Quick live check with httprobe (optional)
cat subs.txt | httprobe > httprobe.txt

# Stage 2: Detailed analysis with httpx
cat subs.txt | httpx -silent -mc 200,301,302,403,401 -title -tech-detect -json > live.txt
```

### 3. Screenshot Capture (Batch processing)
```bash
# Prepare URLs and capture screenshots
cat live.txt | gowitness scan file -f - --threads 4 --screenshot-path jobs/{job_id}/shots
```

### Enhanced Features
- **Retry Logic**: Automatic retry on tool failures with exponential backoff
- **Progress Streaming**: Real-time progress updates via Celery task states
- **Multi-stage Tasks**: Can run individual pipeline stages separately
- **Enhanced Logging**: Detailed logging for debugging and monitoring
- **Queue Management**: Different Celery queues for different workload types

## Monitoring

- **Celery Flower**: http://localhost:5555 - Monitor background tasks
- **API Docs**: http://localhost:8000/docs - Interactive API documentation
- **Logs**: Check Docker logs with `docker-compose logs -f`

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
isort app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Security Considerations

- Run in isolated environment (Docker recommended)
- Limit scan targets to authorized domains only
- Configure rate limiting for production use
- Secure Redis and PostgreSQL instances
- Use environment variables for sensitive configuration

## Troubleshooting

### Common Issues

1. **Tools not found**: Ensure all recon tools are installed and in PATH
2. **Permission errors**: Check file permissions for jobs directory
3. **Database connection**: Verify PostgreSQL is running and accessible
4. **Redis connection**: Ensure Redis is running for Celery tasks

### Logs

```bash
# Docker logs
docker-compose logs -f api
docker-compose logs -f worker

# Manual installation
tail -f /var/log/celery/worker.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details
