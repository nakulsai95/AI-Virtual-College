@echo off
rem Boot the AULA backend + frontend (one server). Double-click or run: run.bat
rem Serves the app at http://localhost:8000
cd /d "%~dp0"

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install -q -r requirements.txt

echo.
echo AULA is starting at http://localhost:8000
echo.
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
