@echo off
REM Start the Streamlit app. Assumes env is activated and index is built.

echo [SpartyWiz] Launching Streamlit app...
set "PYTHONPATH=%CD%"
if "%USER_AGENT%"=="" (
	set "USER_AGENT=SpartyWiz/1.0 (UNCG AI Innovation; https://www.uncg.edu)"
)
streamlit run app.py
