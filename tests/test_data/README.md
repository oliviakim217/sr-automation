# Test Data Directory

This directory contains sample bot payload files for testing the POST /api/sr/create endpoint.

## Test Files:

- `valid_sr_payload.json` - Valid service request with all fields
- `minimal_valid_sr_payload.json` - Valid payload with only required field (short_description)
- `missing_fields_payload.json` - Missing required field (should fail validation)
- `invalid_format_payload.json` - Invalid data types (should fail validation)
- `edge_case_payload.json` - Edge cases (minimum length, empty optional fields)
- `max_length_payload.json` - Maximum length short_description (500 chars)

## Testing:

**PowerShell script:**
```powershell
.\tests\test_post_request.ps1
```

**Manual test:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/sr/create" -Method POST -ContentType "application/json" -Body (Get-Content -Path "tests\test_data\valid_sr_payload.json" -Raw)
```

These files simulate what the bot might send to the service.

