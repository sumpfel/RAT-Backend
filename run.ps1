<#
.SYNOPSIS
  RAT-Backend launcher (Windows, PowerShell).
  Creates a .venv if missing, installs src/requirements.txt, then runs the FastAPI server.

.EXAMPLE
  ./run.ps1
  ./run.ps1 -BindHost 0.0.0.0 -Port 8080
  ./run.ps1 -Reload          # auto-reload on code changes (development)

.NOTES
  If PowerShell blocks the script, run:
    powershell -ExecutionPolicy Bypass -File run.ps1
#>
param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$venvDir = ".venv"
$req     = "src\requirements.txt"
$venvPy  = Join-Path $venvDir "Scripts\python.exe"

# pick a python launcher: prefer the py launcher, fall back to python
$bootstrap = if (Get-Command py -ErrorAction SilentlyContinue) { @("py","-3") }
             elseif (Get-Command python -ErrorAction SilentlyContinue) { @("python") }
             else { throw "Python 3 is not installed or not on PATH." }

# 1) virtual environment
if (-not (Test-Path $venvPy)) {
    Write-Host ">> Creating virtual environment in $venvDir ..."
    & $bootstrap[0] $bootstrap[1..($bootstrap.Length-1)] -m venv $venvDir
}

# 2) dependencies
Write-Host ">> Installing dependencies from $req ..."
& $venvPy -m pip install --upgrade pip | Out-Null
& $venvPy -m pip install -r $req

# 3) run (uvicorn imports main:app from src/, so host/port are configurable here)
$venvPyFull = (Resolve-Path $venvPy).Path
$args = @("-m","uvicorn","main:app","--host",$BindHost,"--port",$Port)
if ($Reload) { $args += "--reload" }

Write-Host ">> Starting RAT-Backend on http://${BindHost}:$Port  (Swagger UI at /docs)"
Set-Location src
& $venvPyFull @args
