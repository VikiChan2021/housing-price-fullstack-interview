[CmdletBinding()]
param(
    [switch]$NoBuild,
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$docker = Get-Command docker.exe -ErrorAction SilentlyContinue
if (-not $docker) {
    throw "Docker CLI was not found. Install and start Docker Desktop first."
}

$dockerInfo = & $docker.Source info --format "{{.ServerVersion}}" 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is not running or is unhealthy. Start Docker Desktop and retry. Run 'docker info' separately for the engine error."
}
Write-Host "Docker Engine: $dockerInfo"

Push-Location $repositoryRoot
try {
    & $docker.Source compose config --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose config validation failed."
    }

    $arguments = [System.Collections.Generic.List[string]]::new()
    $arguments.Add("compose")
    $arguments.Add("up")
    if (-not $NoBuild) {
        $arguments.Add("--build")
    }
    $arguments.Add("-d")
    $arguments.Add("--wait")
    $arguments.Add("--wait-timeout")
    $arguments.Add("300")

    $argumentArray = $arguments.ToArray()
    & $docker.Source @argumentArray
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose startup failed. Run 'docker compose ps' and inspect the logs."
    }
}
finally {
    Pop-Location
}

Write-Host "Docker services are ready at http://localhost:3000"
if (-not $NoBrowser) {
    Start-Process "http://localhost:3000"
}
