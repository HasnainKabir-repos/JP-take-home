$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "AI Invoice Processing Agent"
Write-Host "========================================"

Write-Host "`nStarting accounting API..."

$apiProcess = Start-Process `
    -FilePath "python" `
    -ArgumentList "accounting_api.py" `
    -PassThru `
    -NoNewWindow

Write-Host "Accounting API started. PID: $($apiProcess.Id)"


Write-Host "`nWaiting for accounting API..."

$headers = @{
    "X-API-Key" = "demo-key-1234"
}

$apiReady = $false

for ($i = 1; $i -le 20; $i++) {
    try {
        Invoke-RestMethod `
            -Uri "http://localhost:8080/partners" `
            -Method Get `
            -Headers $headers `
            -TimeoutSec 2 | Out-Null

        $apiReady = $true
        break
    }
    catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $apiReady) {
    Write-Host "ERROR: Accounting API did not become ready."

    if ($apiProcess -and -not $apiProcess.HasExited) {
        Stop-Process `
            -Id $apiProcess.Id `
            -Force `
            -ErrorAction SilentlyContinue
    }

    exit 1
}

Write-Host "Accounting API is ready."


try {
    Write-Host "`n========================================"
    Write-Host "Processing all invoices..."
    Write-Host "========================================`n"

    python process_all.py

    if ($LASTEXITCODE -ne 0) {
        throw "Invoice processing failed with exit code $LASTEXITCODE"
    }

    Write-Host "`n========================================"
    Write-Host "PROCESSING COMPLETE"
    Write-Host "========================================"
    Write-Host "Detailed results: results/batch_results.json"
}
finally {
    Write-Host "`nStopping accounting API..."

    if ($apiProcess -and -not $apiProcess.HasExited) {
        Stop-Process `
            -Id $apiProcess.Id `
            -Force `
            -ErrorAction SilentlyContinue
    }

    Write-Host "Accounting API stopped."
}