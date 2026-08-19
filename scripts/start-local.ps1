[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [ValidateRange(30, 600)]
    [int]$StartupTimeoutSeconds = 240
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeRoot = Join-Path $repositoryRoot "tmp\local-dev"
$statePath = Join-Path $runtimeRoot "state.json"
$runDirectory = Join-Path $runtimeRoot (Get-Date -Format "yyyyMMdd-HHmmss")

$mlRoot = Join-Path $repositoryRoot "services\ml-api"
$estimatorRoot = Join-Path $repositoryRoot "services\estimator-api"
$marketRoot = Join-Path $repositoryRoot "services\market-api"
$webRoot = Join-Path $repositoryRoot "apps\web"

$mlPython = Join-Path $mlRoot ".venv\Scripts\python.exe"
$estimatorPython = Join-Path $estimatorRoot ".venv\Scripts\python.exe"
$mavenWrapper = Join-Path $marketRoot "mvnw.cmd"
$webPackagePath = Join-Path $webRoot "package.json"
$nextEnvironmentPath = Join-Path $webRoot "next-env.d.ts"
$nextEnvironmentSnapshot = if (Test-Path -LiteralPath $nextEnvironmentPath -PathType Leaf) {
    [System.IO.File]::ReadAllBytes($nextEnvironmentPath)
}
else {
    $null
}

function Assert-FileExists {
    param([string]$Path, [string]$Guidance)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required file is missing: $Path`n$Guidance"
    }
}

function Resolve-JavaHome {
    $candidates = [System.Collections.Generic.List[string]]::new()
    if ($env:JAVA_HOME) {
        $candidates.Add($env:JAVA_HOME)
    }
    if ($env:ProgramFiles) {
        $candidates.Add((Join-Path $env:ProgramFiles "Java\latest\jdk-21"))
        $javaRoot = Join-Path $env:ProgramFiles "Java"
        if (Test-Path -LiteralPath $javaRoot -PathType Container) {
            Get-ChildItem -LiteralPath $javaRoot -Directory -Filter "jdk-21*" |
                ForEach-Object { $candidates.Add($_.FullName) }
        }
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath (Join-Path $candidate "bin\java.exe") -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw "Java 21 JDK was not found. Install JDK 21 or set JAVA_HOME to its installation directory."
}

function Resolve-NodeToolchain {
    $package = Get-Content -LiteralPath $webPackagePath -Raw -Encoding utf8 | ConvertFrom-Json
    $requiredNode = [string]$package.engines.node
    $candidates = [System.Collections.Generic.List[string]]::new()

    if ($env:NVM_HOME) {
        $candidates.Add((Join-Path $env:NVM_HOME "v$requiredNode"))
    }

    $currentNode = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($currentNode) {
        $candidates.Add((Split-Path $currentNode.Source -Parent))
    }

    foreach ($candidate in $candidates) {
        $nodePath = Join-Path $candidate "node.exe"
        $corepackPath = Join-Path $candidate "corepack.cmd"
        if (-not (Test-Path -LiteralPath $nodePath -PathType Leaf)) {
            continue
        }
        if (-not (Test-Path -LiteralPath $corepackPath -PathType Leaf)) {
            continue
        }
        $actualNode = (& $nodePath --version).Trim().TrimStart("v")
        if ($actualNode -eq $requiredNode) {
            return [pscustomobject]@{
                Home = (Resolve-Path -LiteralPath $candidate).Path
                Node = $nodePath
                Corepack = $corepackPath
                Version = $actualNode
            }
        }
    }

    throw "Node.js $requiredNode with Corepack was not found. Install it or add it under NVM_HOME."
}

function Invoke-WithEnvironment {
    param(
        [hashtable]$Environment,
        [scriptblock]$Action
    )

    $original = @{}
    try {
        foreach ($entry in $Environment.GetEnumerator()) {
            $original[$entry.Key] = [Environment]::GetEnvironmentVariable(
                [string]$entry.Key,
                [EnvironmentVariableTarget]::Process
            )
            [Environment]::SetEnvironmentVariable(
                [string]$entry.Key,
                [string]$entry.Value,
                [EnvironmentVariableTarget]::Process
            )
        }
        & $Action
    }
    finally {
        foreach ($entry in $original.GetEnumerator()) {
            [Environment]::SetEnvironmentVariable(
                [string]$entry.Key,
                $entry.Value,
                [EnvironmentVariableTarget]::Process
            )
        }
    }
}

function Start-LoggedProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory,
        [hashtable]$Environment,
        [string]$Marker
    )

    $stdoutPath = Join-Path $runDirectory "$Name.out.log"
    $stderrPath = Join-Path $runDirectory "$Name.err.log"
    $process = Invoke-WithEnvironment -Environment $Environment -Action {
        Start-Process `
            -FilePath $FilePath `
            -ArgumentList $ArgumentList `
            -WorkingDirectory $WorkingDirectory `
            -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath `
            -PassThru
    }

    return [pscustomobject]@{
        name = $Name
        pid = $process.Id
        marker = $Marker
        process = $process
        stdout = $stdoutPath
        stderr = $stderrPath
    }
}

function Wait-ForEndpoint {
    param(
        [string]$Name,
        [string]$Uri,
        [System.Diagnostics.Process]$Process
    )

    $deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $Process.Refresh()
        if ($Process.HasExited) {
            throw "$Name exited before becoming ready. Check the logs in $runDirectory"
        }
        try {
            $response = Invoke-WebRequest -Uri $Uri -TimeoutSec 3 -UseBasicParsing
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
                Write-Host "[ready] $Name -> $Uri"
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }
    throw "$Name did not become ready within $StartupTimeoutSeconds seconds: $Uri"
}

function Write-State {
    param([string]$Status, [object[]]$Services)

    $state = [ordered]@{
        status = $Status
        repository_root = $repositoryRoot
        started_at = (Get-Date).ToUniversalTime().ToString("o")
        log_directory = $runDirectory
        services = @(
            $Services | ForEach-Object {
                [ordered]@{
                    name = $_.name
                    pid = $_.pid
                    marker = $_.marker
                    stdout = $_.stdout
                    stderr = $_.stderr
                }
            }
        )
    }
    $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statePath -Encoding utf8
}

function Assert-PortAvailable {
    param([int]$Port)

    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) {
        throw "Port $Port is already in use by PID $($listener.OwningProcess). Stop that process or the Docker stack first."
    }
}

function Restore-NextEnvironmentFile {
    if ($null -ne $nextEnvironmentSnapshot) {
        [System.IO.File]::WriteAllBytes($nextEnvironmentPath, $nextEnvironmentSnapshot)
    }
}

Assert-FileExists $mlPython "Run 'uv sync --frozen' in services\ml-api first."
Assert-FileExists $estimatorPython "Run 'uv sync --frozen' in services\estimator-api first."
Assert-FileExists $mavenWrapper "The Maven Wrapper must remain committed with market-api."
Assert-FileExists $webPackagePath "The Web package manifest must remain committed."

$javaHome = Resolve-JavaHome
$nodeToolchain = Resolve-NodeToolchain

New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null

if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    & (Join-Path $PSScriptRoot "stop-local.ps1") -Quiet
}

foreach ($port in 8000, 8001, 8080, 3000) {
    Assert-PortAvailable $port
}

$modelPath = Join-Path $repositoryRoot "models\model.joblib"
$metadataPath = Join-Path $repositoryRoot "models\metadata.json"
if (-not (Test-Path -LiteralPath $modelPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $metadataPath -PathType Leaf)) {
    Write-Host "Model artifacts are missing; training them once before startup..."
    Push-Location $mlRoot
    try {
        & $mlPython -m app.training
        if ($LASTEXITCODE -ne 0) {
            throw "Model training failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

$nodeModules = Join-Path $webRoot "node_modules"
if (-not (Test-Path -LiteralPath $nodeModules -PathType Container)) {
    Write-Host "Web dependencies are missing; installing the frozen lockfile once..."
    Invoke-WithEnvironment -Environment @{ Path = "$($nodeToolchain.Home);$env:Path" } -Action {
        Push-Location $webRoot
        try {
            & $nodeToolchain.Corepack pnpm install --frozen-lockfile
            if ($LASTEXITCODE -ne 0) {
                throw "pnpm install failed with exit code $LASTEXITCODE."
            }
        }
        finally {
            Pop-Location
        }
    }
}

$startedServices = [System.Collections.Generic.List[object]]::new()
try {
    $ml = Start-LoggedProcess `
        -Name "ml-api" `
        -FilePath $mlPython `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $mlRoot `
        -Environment @{ PYTHONUNBUFFERED = "1" } `
        -Marker "--port 8000"
    $startedServices.Add($ml)
    Write-State -Status "starting" -Services $startedServices
    Wait-ForEndpoint -Name "ml-api" -Uri "http://127.0.0.1:8000/ready" -Process $ml.process

    $estimator = Start-LoggedProcess `
        -Name "estimator-api" `
        -FilePath $estimatorPython `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8001") `
        -WorkingDirectory $estimatorRoot `
        -Environment @{
            PYTHONUNBUFFERED = "1"
            ML_API_BASE_URL = "http://127.0.0.1:8000"
            ML_API_TIMEOUT_SECONDS = "5"
        } `
        -Marker "--port 8001"
    $startedServices.Add($estimator)
    Write-State -Status "starting" -Services $startedServices
    Wait-ForEndpoint -Name "estimator-api" -Uri "http://127.0.0.1:8001/ready" -Process $estimator.process

    $market = Start-LoggedProcess `
        -Name "market-api" `
        -FilePath "cmd.exe" `
        -ArgumentList @("/d", "/c", "mvnw.cmd spring-boot:run") `
        -WorkingDirectory $marketRoot `
        -Environment @{
            JAVA_HOME = $javaHome
            Path = "$(Join-Path $javaHome 'bin');$env:Path"
            ML_API_BASE_URL = "http://127.0.0.1:8000"
            ML_API_TIMEOUT_SECONDS = "5"
        } `
        -Marker "spring-boot:run"
    $startedServices.Add($market)
    Write-State -Status "starting" -Services $startedServices
    Wait-ForEndpoint -Name "market-api" -Uri "http://127.0.0.1:8080/health" -Process $market.process

    $web = Start-LoggedProcess `
        -Name "web" `
        -FilePath "cmd.exe" `
        -ArgumentList @("/d", "/c", "corepack.cmd pnpm dev") `
        -WorkingDirectory $webRoot `
        -Environment @{
            Path = "$($nodeToolchain.Home);$env:Path"
            ESTIMATOR_API_BASE_URL = "http://127.0.0.1:8001"
            MARKET_API_BASE_URL = "http://127.0.0.1:8080"
            NEXT_PUBLIC_BASE_PATH = ""
        } `
        -Marker "pnpm dev"
    $startedServices.Add($web)
    Write-State -Status "starting" -Services $startedServices
    Wait-ForEndpoint -Name "web" -Uri "http://127.0.0.1:3000/api/ready" -Process $web.process
    Restore-NextEnvironmentFile

    Write-State -Status "running" -Services $startedServices
    Write-Host ""
    Write-Host "All local services are ready."
    Write-Host "Portal:        http://localhost:3000"
    Write-Host "ML Swagger:    http://localhost:8000/docs"
    Write-Host "Estimator API: http://localhost:8001/docs"
    Write-Host "Market API:    http://localhost:8080"
    Write-Host "Logs:          $runDirectory"
    Write-Host "Stop:          .\scripts\stop-local.ps1"

    if (-not $NoBrowser) {
        Start-Process "http://localhost:3000"
    }
}
catch {
    Restore-NextEnvironmentFile
    Write-State -Status "failed" -Services $startedServices
    & (Join-Path $PSScriptRoot "stop-local.ps1") -Quiet
    throw
}
