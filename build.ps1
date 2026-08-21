Write-Host "Building Docker images (no cache)..." -ForegroundColor Cyan
docker compose build --no-cache

Write-Host "Starting services..." -ForegroundColor Cyan
docker compose up --build

Write-Host "Done." -ForegroundColor Green
