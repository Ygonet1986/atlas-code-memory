# Atlas Chat Windows startup - serve API (+ static UI) then open browser.
param(
  [string]$OpenUrl = "http://127.0.0.1:8765/",
  [int]$Port = 8765,
  [int]$WaitSeconds = 60
)

$ErrorActionPreference = "Continue"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
$env:ATLAS_LIFE_ROOT = [System.Environment]::GetEnvironmentVariable("ATLAS_LIFE_ROOT","User")
if (-not $env:ATLAS_LIFE_ROOT) { $env:ATLAS_LIFE_ROOT = Join-Path $env:USERPROFILE "atlas-life" }
$env:DEEPSEEK_API_KEY = [System.Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY","User")

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Static = Join-Path $Repo "apps\atlas-chat\dist"
$LogDir = Join-Path $env:LOCALAPPDATA "AtlasChat"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir "startup.log"

function Write-Log([string]$msg) {
  $line = "{0} {1}" -f (Get-Date -Format o), $msg
  Add-Content -Path $Log -Value $line -Encoding utf8
}

Write-Log ("start repo={0} root={1}" -f $Repo, $env:ATLAS_LIFE_ROOT)

try {
  $h = Invoke-WebRequest -Uri ("http://127.0.0.1:{0}/api/health" -f $Port) -UseBasicParsing -TimeoutSec 2
  if ($h.StatusCode -eq 200) {
    Write-Log "already running"
    Start-Process $OpenUrl
    exit 0
  }
} catch { }

$pyCmd = Get-Command py -ErrorAction SilentlyContinue
$argList = @("-3", "-m", "atlas_memory.cli", "life", "serve", "--life-root", $env:ATLAS_LIFE_ROOT, "--port", "$Port", "--host", "127.0.0.1")
if (Test-Path $Static) {
  $argList += @("--static", $Static)
  Write-Log ("static={0}" -f $Static)
}

if ($null -ne $pyCmd) {
  Write-Log ("launch py={0}" -f $pyCmd.Source)
  Start-Process -FilePath $pyCmd.Source -ArgumentList $argList -WindowStyle Hidden -WorkingDirectory $Repo
} else {
  $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($null -eq $pythonCmd) {
    Write-Log "ERROR: py/python not found on PATH"
    exit 1
  }
  Write-Log ("launch python={0}" -f $pythonCmd.Source)
  Start-Process -FilePath $pythonCmd.Source -ArgumentList ($argList | Select-Object -Skip 1) -WindowStyle Hidden -WorkingDirectory $Repo
}

$ok = $false
for ($i = 0; $i -lt $WaitSeconds; $i++) {
  Start-Sleep -Seconds 1
  try {
    $h = Invoke-WebRequest -Uri ("http://127.0.0.1:{0}/api/health" -f $Port) -UseBasicParsing -TimeoutSec 2
    if ($h.StatusCode -eq 200) { $ok = $true; break }
  } catch { }
}

if ($ok) {
  Write-Log ("healthy opening {0}" -f $OpenUrl)
  if (-not (Test-Path $Static)) {
    try {
      $null = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -UseBasicParsing -TimeoutSec 1
      $OpenUrl = "http://127.0.0.1:5173/"
    } catch { }
  }
  Start-Process $OpenUrl
  exit 0
}

Write-Log "FAILED health check"
exit 1
