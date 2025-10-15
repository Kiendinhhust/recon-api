# Changelog

## [Enhanced Version] - 2024

### 🎯 Major Features Added

#### 1. Enhanced Amass Output Filtering
- **Problem**: Amass outputs graph format with relationships (FQDN → a_record → IP, ASN, Netblocks, etc.)
- **Solution**: Automatic filtering to extract only FQDNs (subdomains)
- **Implementation**:
  - Smart regex pattern matching to identify FQDN lines
  - Filters out IP addresses, netblocks, ASN information
  - Only keeps subdomains matching target domain
  - Automatic deduplication

**Example:**
```
Input (57 lines):
  bot.fpt.ai (FQDN) --> a_record --> 124.197.26.207 (IPAddress)
  172.64.0.0/18 (Netblock) --> contains --> 172.64.33.114 (IPAddress)
  13335 (ASN) --> announces --> 172.64.0.0/18 (Netblock)
  ...

Output (8 unique FQDNs):
  bot.fpt.ai
  cdn-static-v3.fpt.ai
  staging-callcenter.fpt.ai
  ...
```

#### 2. Enhanced CLI Tool Integration
- **Direct file I/O**: Tools write directly to files instead of memory
- **Pipe operations**: Efficient chaining with `anew` for deduplication
- **Streaming logs**: Real-time output from long-running commands
- **Enhanced error handling**: Detailed logging for debugging

**Tool Commands:**
```bash
# Subfinder
subfinder -d domain.com -silent -o subs.txt

# Amass with filtering
amass enum -passive -d domain.com -o amass_raw.txt
# → Automatic filtering → amass.txt
cat amass.txt | anew subs.txt

# Assetfinder
assetfinder --subs-only domain.com | anew subs.txt

# Httprobe (quick check)
cat subs.txt | httprobe > httprobe.txt

# Httpx (detailed analysis)
cat subs.txt | httpx -silent -mc 200,301,302 -title -tech-detect -json > live.txt

# Gowitness (screenshots)
gowitness scan file -f live.txt --threads 4 --screenshot-path shots/
```

#### 3. Enhanced Celery Processing
- **Retry Logic**: Automatic retry on failures (max 3 attempts)
- **Exponential Backoff**: Increasing delay between retries
- **Progress Streaming**: Real-time progress updates via Celery states
- **Multi-stage Tasks**: Can run individual pipeline stages separately
- **Queue Management**: Different queues for different workload types

**Queues:**
- `recon_full` - Full reconnaissance scans
- `recon_enum` - Subdomain enumeration only
- `recon_check` - Live host checking only
- `recon_screenshot` - Screenshot capture only
- `maintenance` - Cleanup tasks

#### 4. Enhanced Progress Tracking
- **Percentage-based**: 0-100% progress tracking
- **Stage messages**: Detailed status for each pipeline stage
- **Real-time updates**: Via Celery task states
- **Callback system**: Progress callback for custom handling

**Progress Flow:**
```
0%   → Initializing...
10%  → Running subfinder...
25%  → Running amass...
35%  → Running assetfinder...
50%  → Running httprobe...
65%  → Running httpx...
80%  → Capturing screenshots...
95%  → Saving to database...
100% → Completed!
```

### 🔧 Technical Improvements

#### Pipeline Architecture
- **File-based processing**: Reduced memory usage
- **Stream processing**: Handle large datasets efficiently
- **Error isolation**: Failures in one tool don't stop entire pipeline
- **Graceful degradation**: Continue with available results

#### Code Quality
- **Enhanced logging**: Detailed logs for debugging
- **Type hints**: Better code documentation
- **Error handling**: Comprehensive exception handling
- **Testing**: Test scripts for validation

### 📚 Documentation Added

1. **SETUP_GUIDE.md**: Complete setup instructions
2. **QUICKSTART.md**: Quick start guide (5 minutes)
3. **CHANGELOG.md**: This file
4. **Test Scripts**:
   - `scripts/test_amass_filter.py` - Test Amass filtering
   - `scripts/test_pipeline.py` - Test full pipeline
   - `scripts/quick_start.sh` - Automated setup

### 🚀 New Commands

```bash
# Quick start
make quick-start

# Test Amass filtering
make test-amass

# Test full pipeline
make test-pipeline

# Run multiple workers
make worker-multi
```

### 🐛 Bug Fixes

- Fixed Amass output parsing for graph format
- Fixed memory issues with large subdomain lists
- Fixed timeout handling for long-running tools
- Fixed database connection pooling

### ⚡ Performance Improvements

- **Parallel processing**: Multiple workers for different queues
- **Efficient deduplication**: Using `anew` for fast deduplication
- **Streaming I/O**: Reduced memory footprint
- **Optimized database queries**: Bulk operations

### 🔒 Security Enhancements

- **Input validation**: Domain validation before scanning
- **Rate limiting ready**: Infrastructure for rate limiting
- **Error sanitization**: Safe error messages
- **Secure file handling**: Proper path validation

### 📊 Monitoring Improvements

- **Celery Flower**: Enhanced task monitoring
- **Progress API**: Real-time progress endpoint
- **File-based tracking**: Easy to monitor via filesystem
- **Detailed logging**: Comprehensive log output

### 🎨 User Experience

- **Web Interface**: Simple UI for creating and monitoring scans
- **API Documentation**: Auto-generated Swagger docs
- **Progress Updates**: Real-time status updates
- **Error Messages**: Clear, actionable error messages

### 🔄 Migration Notes

No breaking changes. All existing functionality preserved.

New features are opt-in and backward compatible.

### 📝 Usage Examples

#### Basic Scan
```bash
curl -X POST "http://localhost:8000/api/v1/scans" \
     -H "Content-Type: application/json" \
     -d '{"domain": "fpt.ai"}'
```

#### Monitor Progress
```bash
curl "http://localhost:8000/api/v1/scans/{job_id}/progress"
```

#### Get Results
```bash
curl "http://localhost:8000/api/v1/scans/{job_id}"
```

### 🙏 Credits

- **Subfinder**: ProjectDiscovery
- **Amass**: OWASP
- **Httpx**: ProjectDiscovery
- **Assetfinder**: Tom Hudson
- **Httprobe**: Tom Hudson
- **Anew**: Tom Hudson
- **Gowitness**: SensePost

### 📅 Roadmap

- [ ] Add more subdomain enumeration tools
- [ ] Implement rate limiting
- [ ] Add webhook notifications
- [ ] Export results to multiple formats
- [ ] Add vulnerability scanning integration
- [ ] Implement distributed scanning
- [ ] Add API authentication
- [ ] Create web dashboard

### 🐛 Known Issues

None at this time.

### 💬 Support

For issues or questions:
1. Check SETUP_GUIDE.md
2. Check QUICKSTART.md
3. Review logs
4. Test with test scripts
