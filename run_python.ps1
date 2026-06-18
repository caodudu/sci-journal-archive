param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $PythonArgs
)

$PythonExe = "$env:LocalAppData\Programs\Python\Python312\python.exe"

if (-not (Test-Path $PythonExe)) {
    throw "Python not found at $PythonExe. See docs\tools.md for setup notes."
}

& $PythonExe @PythonArgs
exit $LASTEXITCODE
