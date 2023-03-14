@echo off

rem Check if Python is installed
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Installing requirements 
) else (
    echo python not installed...
    start "install python.bat"
)
py -m pip install --upgrade -r requirements.txt
python builder.py
