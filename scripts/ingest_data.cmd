@echo off
REM Build or update the FAISS vector index from local data and optional URLs.
REM Usage examples:
REM   scripts\ingest_data.cmd
REM   scripts\ingest_data.cmd https://www.uncg.edu/ https://reg.uncg.edu/

set URLS=%*

echo [SpartyWiz] Ingesting documents...
set "PYTHONPATH=%CD%"
if "%USER_AGENT%"=="" (
    set "USER_AGENT=SpartyWiz/1.0 (UNCG AI Innovation; https://www.uncg.edu)"
)
if "%URLS%"=="" (
    python scripts\ingest.py --paths data
) else (
    python scripts\ingest.py --paths data --urls %URLS%
)

echo [SpartyWiz] Ingestion complete.
