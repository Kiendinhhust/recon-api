# ============================================================================
# SCRIPT UPLOAD CODE LÊN VPS TỪ WINDOWS
# ============================================================================
# Sử dụng: .\upload_to_vps.ps1
# Yêu cầu: OpenSSH client đã được cài đặt trên Windows
# ============================================================================

param(
    [string]$VpsIp = "124.197.22.184",
    [string]$VpsUser = "root",
    [string]$VpsPath = "/home/recon/recon-api"
)

Write-Host "🚀 UPLOAD CODE LÊN VPS" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Màu sắc
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"

# Function để print với màu
function Print-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor $Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor $Red
}

function Print-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor $Yellow
}

# ============================================================================
# 1. KIỂM TRA SSH
# ============================================================================
Print-Info "Bước 1: Kiểm tra kết nối SSH..."

try {
    $sshTest = ssh -o ConnectTimeout=5 -o BatchMode=yes $VpsUser@$VpsIp "echo OK" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Print-Success "Kết nối SSH thành công"
    } else {
        Print-Error "Không thể kết nối SSH. Vui lòng kiểm tra:"
        Write-Host "  - IP VPS: $VpsIp"
        Write-Host "  - User: $VpsUser"
        Write-Host "  - SSH key hoặc password"
        exit 1
    }
} catch {
    Print-Error "Lỗi khi kiểm tra SSH: $_"
    exit 1
}

# ============================================================================
# 2. TẠO THƯ MỤC TRÊN VPS
# ============================================================================
Print-Info "Bước 2: Tạo thư mục trên VPS..."

ssh $VpsUser@$VpsIp "mkdir -p $VpsPath"
if ($LASTEXITCODE -eq 0) {
    Print-Success "Thư mục đã được tạo: $VpsPath"
} else {
    Print-Error "Không thể tạo thư mục trên VPS"
    exit 1
}

# ============================================================================
# 3. UPLOAD CODE
# ============================================================================
Print-Info "Bước 3: Upload code lên VPS..."

# Danh sách files/folders cần upload
$itemsToUpload = @(
    "app",
    "web",
    "alembic",
    "systemd",
    "nginx",
    "requirements.txt",
    "alembic.ini",
    "deploy_to_vps.sh",
    "SourceLeakHacker.py",
    "VPS_DEPLOYMENT_GUIDE.md",
    "COMPREHENSIVE_CODEBASE_ANALYSIS.md"
)

# Danh sách files/folders cần loại trừ
$excludeItems = @(
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".git",
    ".vscode",
    "venv",
    "jobs",
    ".env",
    "*.log"
)

# Tạo exclude arguments cho scp
$excludeArgs = $excludeItems | ForEach-Object { "--exclude=$_" }

Print-Info "Đang upload files..."

foreach ($item in $itemsToUpload) {
    if (Test-Path $item) {
        Write-Host "  Uploading: $item" -ForegroundColor Gray
        
        if (Test-Path $item -PathType Container) {
            # Nếu là folder, dùng scp -r
            scp -r $item ${VpsUser}@${VpsIp}:${VpsPath}/
        } else {
            # Nếu là file, dùng scp
            scp $item ${VpsUser}@${VpsIp}:${VpsPath}/
        }
        
        if ($LASTEXITCODE -eq 0) {
            Print-Success "Uploaded: $item"
        } else {
            Print-Error "Failed to upload: $item"
        }
    } else {
        Print-Info "Skipped (not found): $item"
    }
}

# ============================================================================
# 4. SET PERMISSIONS
# ============================================================================
Print-Info "Bước 4: Cấu hình permissions..."

ssh $VpsUser@$VpsIp "chmod +x $VpsPath/deploy_to_vps.sh"
ssh $VpsUser@$VpsIp "chmod 644 $VpsPath/requirements.txt"
ssh $VpsUser@$VpsIp "chmod 644 $VpsPath/alembic.ini"

if (Test-Path "SourceLeakHacker.py") {
    ssh $VpsUser@$VpsIp "chmod +x $VpsPath/SourceLeakHacker.py"
}

Print-Success "Permissions đã được cấu hình"

# ============================================================================
# 5. KIỂM TRA FILES ĐÃ UPLOAD
# ============================================================================
Print-Info "Bước 5: Kiểm tra files đã upload..."

$fileCount = ssh $VpsUser@$VpsIp "ls -la $VpsPath | wc -l"
Print-Success "Tổng số files/folders: $fileCount"

# ============================================================================
# 6. HOÀN TẤT
# ============================================================================
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Print-Success "UPLOAD HOÀN TẤT!"
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 BƯỚC TIẾP THEO:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. SSH vào VPS:" -ForegroundColor White
Write-Host "   ssh $VpsUser@$VpsIp" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Chuyển đến thư mục project:" -ForegroundColor White
Write-Host "   cd $VpsPath" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Chạy deployment script:" -ForegroundColor White
Write-Host "   chmod +x deploy_to_vps.sh" -ForegroundColor Gray
Write-Host "   ./deploy_to_vps.sh" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Hoặc làm theo hướng dẫn trong:" -ForegroundColor White
Write-Host "   VPS_DEPLOYMENT_GUIDE.md" -ForegroundColor Gray
Write-Host ""
Print-Success "Chúc mừng! 🎉"

