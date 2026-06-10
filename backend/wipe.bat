@echo off
rem Wipe the college (keeps your API key + budget). Double-click or run: wipe.bat
cd /d "%~dp0"
call ".venv\Scripts\activate.bat"
python wipe.py
pause
