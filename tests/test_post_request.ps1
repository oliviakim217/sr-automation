# Test POST /api/sr/create endpoint
$endpoint = "http://localhost:8000/api/sr/create"

$testFiles = @(
    @{file="valid_sr_payload.json"; name="Valid payload"},
    @{file="minimal_valid_sr_payload.json"; name="Minimal payload"},
    @{file="edge_case_payload.json"; name="Edge cases"},
    @{file="max_length_payload.json"; name="Max length"},
    @{file="missing_fields_payload.json"; name="Missing fields"},
    @{file="invalid_format_payload.json"; name="Invalid format"}
)

foreach ($test in $testFiles) {
    Write-Host "Test: $($test.name)"
    $payload = Get-Content -Path "tests\test_data\$($test.file)" -Raw
    try {
        Invoke-RestMethod -Uri $endpoint -Method POST -ContentType "application/json" -Body $payload | ConvertTo-Json
    } catch {
        Write-Host "Error: $($_.Exception.Message)"
    }
    Write-Host ""
}
