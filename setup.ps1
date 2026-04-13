# ============================================================
#  FaceID Attendance System - Setup Script
#  Usage:
#    .\setup.ps1                        (if already cloned)
#    .\setup.ps1 -GitUrl <repo_url>     (clone then setup)
# ============================================================

param(
    [string]$GitUrl = ""
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host "`n>>> $msg" -ForegroundColor Cyan
}

function Write-OK($msg) {
    Write-Host "    [OK] $msg" -ForegroundColor Green
}

function Write-Fail($msg) {
    Write-Host "    [FAIL] $msg" -ForegroundColor Red
    exit 1
}

# ── 1. Clone repo (optional) ─────────────────────────────────
if ($GitUrl -ne "") {
    Write-Step "Cloning repository..."
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Fail "Git is not installed. Download from https://git-scm.com"
    }
    git clone $GitUrl faceID
    Set-Location faceID
    Write-OK "Repository cloned."
}

# ── 2. Check Python 3.10 ─────────────────────────────────────
Write-Step "Checking Python..."

$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "3\.10") {
            $python = $cmd
            break
        }
    } catch {}
}

if (-not $python) {
    # Try py launcher for Python 3.10 specifically
    try {
        $ver = & py -3.10 --version 2>&1
        if ($ver -match "3\.10") { $python = "py -3.10" }
    } catch {}
}

if (-not $python) {
    Write-Fail "Python 3.10 not found. Download from https://www.python.org/downloads/release/python-31011/"
}

Write-OK "Found: $(& $python --version 2>&1)"

# ── 3. Create virtual environment ────────────────────────────
Write-Step "Creating virtual environment..."

if (Test-Path "venv") {
    Write-Host "    venv already exists, skipping." -ForegroundColor Yellow
} else {
    & $python -m venv venv
    Write-OK "venv created."
}

$pip    = "venv\Scripts\pip.exe"
$python = "venv\Scripts\python.exe"

# ── 4. Upgrade pip ───────────────────────────────────────────
Write-Step "Upgrading pip..."
& $python -m pip install --upgrade pip --quiet
Write-OK "pip upgraded."

# ── 5. Install base dependencies ─────────────────────────────
Write-Step "Installing Django and base packages..."
# opencv-contrib-python is required (not opencv-python) — it includes the
# cv2.face module needed for LBPH face recognition. Do NOT install both.
& $pip install `
    "Django==5.2.13" `
    "numpy==2.2.6" `
    "opencv-contrib-python" `
    "Pillow==12.2.0" `
    "sqlparse==0.5.5" `
    "tzdata" `
    --quiet
Write-OK "Base packages installed."

# ── 6. Verify LBPH recognizer is available ───────────────────
Write-Step "Verifying opencv-contrib-python (LBPH)..."
$lbphCheck = & $python -c "import cv2; cv2.face.LBPHFaceRecognizer_create(); print('OK')" 2>&1
if ($lbphCheck -eq "OK") {
    Write-OK "cv2.face.LBPHFaceRecognizer is available."
} else {
    Write-Fail "LBPH check failed. Make sure opencv-contrib-python installed correctly: $lbphCheck"
}

# ── 7. Run Django migrations ─────────────────────────────────
Write-Step "Running database migrations..."
& $python manage.py migrate
Write-OK "Migrations applied."

# ── 9. Create media directories ──────────────────────────────
Write-Step "Creating media directories..."
New-Item -ItemType Directory -Force -Path "media\faces" | Out-Null
Write-OK "media/faces directory ready."

# ── 10. Create superuser (optional) ──────────────────────────
Write-Step "Create Django admin superuser?"
$answer = Read-Host "    Do you want to create a superuser now? (y/n)"
if ($answer -eq "y" -or $answer -eq "Y") {
    & $python manage.py createsuperuser
}

# ── Done ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Setup complete! Start the server with:" -ForegroundColor Green
Write-Host ""
Write-Host "    venv\Scripts\activate" -ForegroundColor White
Write-Host "    python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "  Then open: http://127.0.0.1:8000" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
