[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# Web readiness covers both business APIs; direct service probes identify the failing layer.
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
        # A timeout, connection failure, or non-success status all mean unavailable to this summary.
        [pscustomobject]@{
            Service = $check.Service
            Status = "down"
            Http = "-"
            Uri = $check.Uri
        }
    }
}

$results | Format-Table -AutoSize
# A nonzero exit code makes this script suitable for CI or shell health gates.
if ($results.Status -contains "down") {
    exit 1
}
