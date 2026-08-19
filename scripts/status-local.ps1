[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$checks = @(
    @{ Service = "web"; Uri = "http://127.0.0.1:3000/api/ready" },
    @{ Service = "ml-api"; Uri = "http://127.0.0.1:8000/health" },
    @{ Service = "estimator-api"; Uri = "http://127.0.0.1:8001/health" },
    @{ Service = "market-api"; Uri = "http://127.0.0.1:8080/health" }
)

$results = foreach ($check in $checks) {
    try {
        $response = Invoke-WebRequest -Uri $check.Uri -TimeoutSec 3 -UseBasicParsing
        [pscustomobject]@{
            Service = $check.Service
            Status = "ready"
            Http = $response.StatusCode
            Uri = $check.Uri
        }
    }
    catch {
        [pscustomobject]@{
            Service = $check.Service
            Status = "down"
            Http = "-"
            Uri = $check.Uri
        }
    }
}

$results | Format-Table -AutoSize
if ($results.Status -contains "down") {
    exit 1
}
