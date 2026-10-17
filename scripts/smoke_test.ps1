param(
    [string]$BaseUrl = "http://localhost:8000/api/v1"
)

$ErrorActionPreference = "Stop"

$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get -TimeoutSec 10
if ($health.status -ne "ok" -or $health.database -ne "ok") {
    throw "Backend или PostgreSQL не готовы"
}

$payload = ConvertTo-Json -InputObject @(
    @{
        id = "smoke-1"
        raw_address = "город Алматы, Мкр Аксай 3а, 59, кв 70"
    }
)

$result = Invoke-RestMethod `
    -Uri "$BaseUrl/parse/batch" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($payload)) `
    -TimeoutSec 30

if ($result.Count -ne 1 -or -not $result[0].city -or -not $result[0].house -or -not $result[0].record_id) {
    throw "Разбор адреса вернул неполный результат"
}

$saved = Invoke-RestMethod `
    -Uri "$BaseUrl/records?limit=500" `
    -Method Get `
    -TimeoutSec 10 | Where-Object { $_.record_id -eq $result[0].record_id }

if (-not $saved) {
    throw "Результат не сохранился в PostgreSQL"
}

Write-Host "PASS: frontend contract, backend, reference and PostgreSQL persistence are ready" -ForegroundColor Green
$result | ConvertTo-Json -Depth 5
