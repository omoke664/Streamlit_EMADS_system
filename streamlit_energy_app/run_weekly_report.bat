@echo off
REM Activate your virtual environment
call "C:\Users\omoke\OneDrive\Documents\Studies\Project\streamlit_energy_app\.venv\Scripts\activate.bat"

REM Change to the project directory
cd /d "C:\Users\omoke\OneDrive\Documents\Studies\Project\streamlit_energy_app"

REM Run the weekly_report script
python weekly_report.py

REM Optionally log output
echo %DATE% %TIME% — Weekly report run >> weekly_report.log
