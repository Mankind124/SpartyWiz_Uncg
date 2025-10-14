@echo off
REM One-time setup: install Python dependencies in the currently active environment.
REM Assumes you already activated your conda env (e.g., "conda activate spartywiz-312").

echo [SpartyWiz] Installing Python dependencies...
set "PYTHONPATH=%CD%"
pip install --upgrade pip
pip install -r requirements.txt

echo [SpartyWiz] Optionally pre-download embedding model to reduce first-run latency
python scripts\warm_start.py

echo [SpartyWiz] Setup complete.
