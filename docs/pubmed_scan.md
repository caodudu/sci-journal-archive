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
- Current runner now supports retry/backoff, progress log, and a status JSON file.

## Command

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_pubmed_background.ps1 -Email test@example.com
```

Replace `test@example.com` with a real email in future runs if desired; NCBI recommends identifying API traffic.

## Logs

```text
logs\pubmed_collect_2025_biomed.log
logs\pubmed_collect_2025_biomed.err.log
logs\pubmed_collect_2025_biomed.progress.log
logs\pubmed_collect_2025_biomed.status.json
```

`progress.log` appends one line per journal-year with completed/total, percent, elapsed time, ETA, ok/skipped/failed counts, current journal, year, and count/error.

`status.json` is overwritten with the latest machine-readable status, for example:

```json
{
  "status": "ok",
  "current_journal": "Nature",
  "current_year": 2025,
  "completed": 12,
  "total": 29490,
  "percent": 0.04,
  "elapsed": "00:03:10",
  "eta": "129:38:42",
  "ok": 10,
  "skipped": 1,
  "failed": 1
}
```

## Check Later

Do not monitor continuously. When asked later, use:

```powershell
Get-Process python -ErrorAction SilentlyContinue |
  Select-Object ProcessName,Id,StartTime,Path

powershell -ExecutionPolicy Bypass -File .\run_python.ps1 scripts\db_summary.py

Get-Item logs\pubmed_collect_2025_biomed.log, logs\pubmed_collect_2025_biomed.err.log |
  Select-Object Name,Length,LastWriteTime

Get-Content -Tail 20 logs\pubmed_collect_2025_biomed.progress.log

Get-Content -Raw logs\pubmed_collect_2025_biomed.status.json
```
