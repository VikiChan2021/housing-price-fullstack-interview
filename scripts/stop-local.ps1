[CmdletBinding()]
param([switch]$Quiet)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeRoot = Join-Path $repositoryRoot "tmp\local-dev"
$statePath = Join-Path $runtimeRoot "state.json"

if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
    if (-not $Quiet) {
        Write-Host "No local development state was found."
    }
    return
}

$state = Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json
# Capture one consistent process snapshot before resolving parent-child ownership.
$allProcesses = @(Get-CimInstance Win32_Process)

function Get-DescendantProcessIds {
    param([int]$ParentId)

    foreach ($child in $allProcesses | Where-Object { $_.ParentProcessId -eq $ParentId }) {
        # Yield descendants before parents so shells do not orphan their service processes.
        Get-DescendantProcessIds -ParentId ([int]$child.ProcessId)
        [int]$child.ProcessId
    }
}

$services = @($state.services)
# Reverse startup order so consumers stop before their dependencies.
[array]::Reverse($services)
foreach ($service in $services) {
    $processInfo = $allProcesses | Where-Object { $_.ProcessId -eq [int]$service.pid } |
        Select-Object -First 1
    if (-not $processInfo) {
        continue
    }

    $commandLine = [string]$processInfo.CommandLine
    # PIDs can be reused; the recorded command marker proves this is still our process tree.
    if (-not $commandLine.Contains([string]$service.marker)) {
        Write-Warning "Skipped PID $($service.pid): its command no longer matches $($service.name)."
        continue
    }

    $processIds = @((Get-DescendantProcessIds -ParentId ([int]$service.pid)))
    $processIds += [int]$service.pid
    # Force is limited to verified local-development process trees recorded in state.json.
    foreach ($processId in $processIds) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    if (-not $Quiet) {
        Write-Host "Stopped $($service.name)."
    }
}

# Retain the state file as an audit record instead of deleting diagnostic paths and timestamps.
$state.status = "stopped"
$state | Add-Member -NotePropertyName "stopped_at" -NotePropertyValue (
    (Get-Date).ToUniversalTime().ToString("o")
) -Force
$state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statePath -Encoding utf8

if (-not $Quiet) {
    Write-Host "Local development services are stopped."
}
