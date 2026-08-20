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

# Finding docker.exe proves only the CLI exists; docker info also verifies the Engine connection.
$dockerInfo = & $docker.Source info --format "{{.ServerVersion}}" 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is not running or is unhealthy. Start Docker Desktop and retry. Run 'docker info' separately for the engine error."
}
Write-Host "Docker Engine: $dockerInfo"

Push-Location $repositoryRoot
try {
    # Validate interpolation and schema before any image build or container mutation.
    & $docker.Source compose config --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose config validation failed."
    }

    # Build an argument array so optional flags remain separate and safely quoted.
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
    # Always restore the caller's working directory, including failed Compose runs.
    Pop-Location
}

Write-Host "Docker services are ready at http://localhost:3000"
if (-not $NoBrowser) {
    Start-Process "http://localhost:3000"
}
