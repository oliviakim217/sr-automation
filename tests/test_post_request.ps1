# Test POST /api/sr/create endpoint
$endpoint = "http://localhost:8000/api/sr/create"

# Test 1: Valid payload
Write-Host "Test 1: Valid payload"
$payload = Get-Content -Path "tests\test_data\valid_sr_payload.json" -Raw
Invoke-RestMethod -Uri $endpoint -Method POST -ContentType "application/json" -Body $payload | ConvertTo-Json
Write-Host ""

# Test 2: Minimal payload
Write-Host "Test 2: Minimal payload"
$payload = Get-Content -Path "tests\test_data\minimal_valid_sr_payload.json" -Raw
Invoke-RestMethod -Uri $endpoint -Method POST -ContentType "application/json" -Body $payload | ConvertTo-Json
Write-Host ""
