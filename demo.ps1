$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$api = "http://localhost:30080"

# NodePort is not published on localhost for every Docker Desktop cluster type.
# If the API is unreachable, fall back to kubectl port-forward on the same port.
$pf = $null
try { Invoke-RestMethod "$api/healthz" -TimeoutSec 3 | Out-Null }
catch {
    Write-Host "NodePort not reachable, starting kubectl port-forward on 30080..."
    kubectl rollout status deployment/orders-api -n orders --timeout=120s
    $pf = Start-Process kubectl -ArgumentList "port-forward -n orders svc/orders-api 30080:80" -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 4
    Invoke-RestMethod "$api/healthz" -TimeoutSec 5 | Out-Null   # fails clearly if still unreachable
}

Write-Host "==> 1/2. Customers place orders (stored in MySQL as PENDING)"
1..5 | ForEach-Object {
    $body = @{ customer_name = "customer$_"; product = "widget"; quantity = $_; amount = 9.99 * $_ } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri "$api/orders" -ContentType "application/json" -Body $body | ConvertTo-Json -Compress
}
Write-Host "Pending orders:"
(Invoke-RestMethod "$api/orders?status=PENDING").Count

Write-Host "==> 3. Run the processing Job"
kubectl delete job process-orders -n orders --ignore-not-found
kubectl apply -f k8s/20-job-process-orders.yaml
kubectl wait --for=condition=complete job/process-orders -n orders --timeout=180s
kubectl logs job/process-orders -n orders
Write-Host "Pending orders now:"
(Invoke-RestMethod "$api/orders?status=PENDING").Count

Write-Host "==> 4. Trigger the daily-report CronJob manually"
$name = "manual-report-$(Get-Date -Format 'HHmmss')"
kubectl create job $name --from=cronjob/daily-report -n orders
kubectl wait --for=condition=complete "job/$name" -n orders --timeout=120s
kubectl logs "job/$name" -n orders
Invoke-RestMethod "$api/reports" | ConvertTo-Json

Write-Host "==> 5. Run a failing Job so Grafana shows a failure"
kubectl delete job process-orders-fail-demo -n orders --ignore-not-found
kubectl apply -f k8s/21-job-process-orders-fail.yaml
if ($pf) { Stop-Process -Id $pf.Id -ErrorAction SilentlyContinue }
Write-Host "Open Grafana: http://localhost:30030 (admin/admin)"
Write-Host "If Grafana is not reachable, run: kubectl port-forward -n monitoring svc/grafana 30030:3000"
