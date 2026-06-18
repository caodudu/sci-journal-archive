# PubMed Background Scan

Last updated: 2026-06-18

## Current Background Run

- Status: started, not monitored continuously.
- Started at: 2026-06-18 17:42 Asia/Shanghai.
- Process: `python.exe`
- PID observed once after startup: `13472`
- Scope: biomedical/cross-biology journals.
- Years: 2021, 2022, 2023, 2024, 2025.
- Sample size: 20 PubMed articles per journal per year.
- Delay: 0.5 seconds between requests.
- Resume behavior: `--skip-existing`, so reruns skip journal-year counts already present.
- Test run before background launch: 1 journal, 2025, 1 sampled article; succeeded.

## Command

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_pubmed_background.ps1 -Email test@example.com
```

Replace `test@example.com` with a real email in future runs if desired; NCBI recommends identifying API traffic.

## Logs

```text
logs\pubmed_collect_2025_biomed.log
logs\pubmed_collect_2025_biomed.err.log
```

## Check Later

Do not monitor continuously. When asked later, use:

```powershell
Get-Process python -ErrorAction SilentlyContinue |
  Select-Object ProcessName,Id,StartTime,Path

powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\db_summary.py

Get-Item logs\pubmed_collect_2025_biomed.log, logs\pubmed_collect_2025_biomed.err.log |
  Select-Object Name,Length,LastWriteTime
```
