param(
    [switch]$SkipBrowser
)

Write-Host "OpenWInD Bb Clarinet Studio setup" -ForegroundColor Cyan

# Ensure Python is available
python --version > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python 3.11 not found. Install from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Create virtual environment
if (-not (Test-Path .\.venv)) {
    Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv .\.venv
}

& .\.venv\Scripts\python -m pip install --upgrade pip wheel

Write-Host "Installing Python requirements (root aggregate)..." -ForegroundColor Yellow
& .\.venv\Scripts\pip install -r requirements.txt

# Ensure Node.js
node --version > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Node.js 20+ not found. Install from https://nodejs.org/en" -ForegroundColor Red
    exit 1
}

$packageManager = "npm"
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    $packageManager = "pnpm"
}

Write-Host "Installing Node dependencies from workspaces..." -ForegroundColor Yellow
if ($packageManager -eq "pnpm") {
    pnpm install
} else {
    npm install
}

# Launch backend
Write-Host "Starting FastAPI server on http://127.0.0.1:8001" -ForegroundColor Cyan
Start-Process -WindowStyle Hidden -FilePath powershell -ArgumentList "-NoExit","-Command","Push-Location server; ..\\.venv\\Scripts\\python -m uvicorn openwind_service.main:app --host 127.0.0.1 --port 8001 --reload"

# Launch frontend
Write-Host "Starting Vite dev server on http://127.0.0.1:5173" -ForegroundColor Cyan
if ($packageManager -eq "pnpm") {
    Start-Process -FilePath pnpm -ArgumentList "run","dev" -WorkingDirectory (Resolve-Path ui)
} else {
    Start-Process -FilePath npm -ArgumentList "run","dev" -WorkingDirectory (Resolve-Path ui)
}

if (-not $SkipBrowser) {
    Start-Process "http://127.0.0.1:5173"
}

Write-Host "Servers launching. Monitor the console windows for logs." -ForegroundColor Green
Write-Host "API routes:" -ForegroundColor Yellow
Write-Host "  http://127.0.0.1:8001/api/v1/health"
Write-Host "  http://127.0.0.1:8001/api/v1/presets/bb_clarinet"
Write-Host "  http://127.0.0.1:8001/api/v1/recommend"
Write-Host "  http://127.0.0.1:8001/api/v1/simulate"
Write-Host "  http://127.0.0.1:8001/api/v1/optimize"
Write-Host "  http://127.0.0.1:8001/api/v1/export/{fmt}"
