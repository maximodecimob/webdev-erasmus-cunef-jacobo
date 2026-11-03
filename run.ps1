# One command to run the app on Windows: installs the libraries and starts the server.
# The database is a SQLite file (vibe_tickets.db), created automatically. Needs Python 3.12.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# Stop any copy of the server left running from an earlier run, so port 3000 is free
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like '*uvicorn app.main:app*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

# 1. Libraries, in a local .venv (created once, then reused)
$py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py -3" }
if (-not (Test-Path ".venv")) {
    Invoke-Expression "$py -m venv .venv"
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. The app. Open http://localhost:3000 in your browser. Stop it with Ctrl+C.
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 3000
