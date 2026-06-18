# Local Tools And Runtime Notes

Last updated: 2026-06-18

## Python

System `python` currently resolves to the WindowsApps placeholder:

```powershell
C:\Users\caojun\AppData\Local\Microsoft\WindowsApps\python.exe
```

Use the real installed Python directly:

```powershell
& "$env:LocalAppData\Programs\Python\Python312\python.exe" --version
```

Current verified version:

```text
Python 3.12.10
```

Verified executable:

```text
C:\Users\caojun\AppData\Local\Programs\Python\Python312\python.exe
```

Verified SQLite bundled with Python:

```text
SQLite 3.49.1
```

Recommended project command form:

```powershell
$py = "$env:LocalAppData\Programs\Python\Python312\python.exe"
& $py scripts\init_db.py
& $py scripts\import_jcr.py --year 2025 --csv data\raw\jcr_exports\jcr_2025.csv
& $py scripts\import_jcr.py --year 2026 --csv data\raw\jcr_exports\jcr_2026.csv
& $py scripts\build_biomed_subset.py
& $py scripts\pubmed_collect.py --sample-size 20 --email your.name@example.com
& $py scripts\export_viewer_data.py
```

Shortcut from this repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\init_db.py
powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\export_viewer_data.py
```

Direct `.\run_python.ps1 ...` may be blocked by the local PowerShell execution policy.

## Proxy

FlClash is running and Windows system proxy is enabled.

Verified local proxy:

```text
127.0.0.1:7890
```

Verified owning process:

```text
FlClashCore
```

Use proxy explicitly in PowerShell for commands that do not read the Windows proxy settings:

```powershell
$env:HTTP_PROXY = "http://127.0.0.1:7890"
$env:HTTPS_PROXY = "http://127.0.0.1:7890"
$env:ALL_PROXY = "socks5://127.0.0.1:7890"
```

Clear proxy environment variables:

```powershell
Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:ALL_PROXY -ErrorAction SilentlyContinue
```

Check Windows proxy:

```powershell
Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' |
  Select-Object ProxyEnable, ProxyServer, AutoConfigURL
```

Check listening proxy ports:

```powershell
Get-NetTCPConnection -State Listen |
  Where-Object { $_.LocalAddress -in @('127.0.0.1','::1','0.0.0.0') } |
  Sort-Object LocalPort |
  Select-Object LocalAddress, LocalPort, OwningProcess
```

## Package And Install Tools

Verified available:

```powershell
winget --version
```

Current winget version:

```text
v1.10.320
```

The previous Python install command used:

```powershell
winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements --silent
```

The command timed out in the shell, but Python 3.12.10 was installed successfully under the user profile.

## Useful Checks

Find commands:

```powershell
Get-Command winget, python, py, git, node, sqlite3 -ErrorAction SilentlyContinue |
  Select-Object Name, Source
```

Inspect active install/download processes:

```powershell
Get-Process |
  Where-Object { $_.ProcessName -match 'winget|python|msiexec|curl|git' } |
  Select-Object ProcessName, Id, CPU
```

List project files:

```powershell
Get-ChildItem -Recurse -File | Select-Object FullName, Length
```

## SCI Archive Pipeline

Initialize database:

```powershell
$py = "$env:LocalAppData\Programs\Python\Python312\python.exe"
& $py scripts\init_db.py
```

Import authorized or verified JCR CSV files:

```powershell
& $py scripts\import_jcr.py --year 2025 --csv data\raw\jcr_exports\jcr_2025.csv
& $py scripts\import_jcr.py --year 2026 --csv data\raw\jcr_exports\jcr_2026.csv
```

Build biomedical subset:

```powershell
& $py scripts\build_biomed_subset.py
```

Collect PubMed data for the most recent three years:

```powershell
& $py scripts\pubmed_collect.py --sample-size 20 --email your.name@example.com
```

Start the slow background PubMed scan for 2021-2025 biomedical/cross-biology journals:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_pubmed_background.ps1 -Email your.name@example.com
```

Logs:

```text
logs\pubmed_collect_2025_biomed.log
logs\pubmed_collect_2025_biomed.err.log
```

Export viewer data:

```powershell
& $py scripts\export_viewer_data.py
```

Export 2025-only viewer data for the current UI review:

```powershell
& $py scripts\export_viewer_data.py --years 2025
```

Later, export 2026 or multiple years without changing the database:

```powershell
& $py scripts\export_viewer_data.py --years 2026
& $py scripts\export_viewer_data.py --years 2025 2026
```

Print database summary:

```powershell
& $py scripts\db_summary.py
```

Open:

```text
C:\workspace\1_article\web\index.html
```

The viewer is designed to work when opened directly with `file://` in Edge. It loads `web/journals-data.js` instead of relying only on `fetch("journals.json")`, because local JSON fetches can be blocked by browser file-security rules.
