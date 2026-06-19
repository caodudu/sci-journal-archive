param(
    [string] $Email = "",
    [int[]] $Years = @(2021, 2022, 2023, 2024, 2025),
    [int] $SampleSize = 20,
    [double] $Delay = 0.5,
    [int] $Retries = 5,
    [double] $RetryDelay = 3.0
)

$Root = Split-Path -Parent $PSScriptRoot
$PythonExe = "$env:LocalAppData\Programs\Python\Python312\python.exe"
$LogDir = Join-Path $Root "logs"
$LogPath = Join-Path $LogDir "pubmed_collect_2025_biomed.log"
$ErrPath = Join-Path $LogDir "pubmed_collect_2025_biomed.err.log"
$ProgressPath = Join-Path $LogDir "pubmed_collect_2025_biomed.progress.log"
$StatusPath = Join-Path $LogDir "pubmed_collect_2025_biomed.status.json"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path $PythonExe)) {
    throw "Python not found at $PythonExe"
}

$Args = @(
    "scripts\pubmed_collect.py",
    "--years"
) + ($Years | ForEach-Object { "$_" }) + @(
    "--sample-size", "$SampleSize",
    "--delay", "$Delay",
    "--retries", "$Retries",
    "--retry-delay", "$RetryDelay",
    "--progress-log", $ProgressPath,
    "--status-json", $StatusPath,
    "--only-biomed",
    "--skip-existing"
)

if ($Email.Trim()) {
    $Args += @("--email", $Email.Trim())
}

$process = Start-Process `
    -FilePath $PythonExe `
    -ArgumentList $Args `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $LogPath `
    -RedirectStandardError $ErrPath `
    -WindowStyle Hidden `
    -PassThru

"Started PubMed background scan. PID=$($process.Id)"
"stdout: $LogPath"
"stderr: $ErrPath"
"progress: $ProgressPath"
"status: $StatusPath"
