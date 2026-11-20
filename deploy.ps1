$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==> Checking Kubernetes (Docker Desktop)"
kubectl config use-context docker-desktop
if ($LASTEXITCODE -ne 0) { throw "Enable Kubernetes in Docker Desktop: Settings > Kubernetes > Enable" }

Write-Host "==> Building image orders-app:1.0 (local image, visible to Docker Desktop's cluster)"
docker build -t orders-app:1.0 ./app
if ($LASTEXITCODE -ne 0) { throw "docker build failed" }

Write-Host "==> Deploying MySQL + API"
kubectl apply -f k8s/00-namespace-mysql.yaml
kubectl apply -f k8s/10-api.yaml
kubectl rollout status deployment/mysql -n orders --timeout=300s
kubectl rollout status deployment/orders-api -n orders --timeout=180s

Write-Host "==> Deploying CronJob"
kubectl apply -f k8s/30-cronjob-daily-report.yaml

Write-Host "==> Deploying monitoring (kube-state-metrics, Prometheus, Grafana)"
kubectl apply -f monitoring/monitoring.yaml
kubectl create configmap grafana-dashboards -n monitoring `
    --from-file=monitoring/dashboards --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/grafana -n monitoring
kubectl rollout status deployment/grafana -n monitoring --timeout=180s

Write-Host ""
Write-Host "Ready:"
Write-Host "  Orders API : http://localhost:30080"
Write-Host "  Grafana    : http://localhost:30030   (admin / admin)  Dashboard: Orders > Orders - Job & CronJob Monitoring"
Write-Host "Try it:  .\demo.ps1"
