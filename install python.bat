@echo off

rem Use PowerShell to get the latest version of Python
for /f %%v in ('powershell.exe -Command "Invoke-WebRequest https://www.python.org/ftp/python/ -UseBasicParsing | Select-String -Pattern '3.10.[0-9]{1,2}' -AllMatches | Select-Object -ExpandProperty Matches | Select-Object -ExpandProperty Value | Sort-Object -Descending -Unique | Select-Object -First 1"') do set PYTHON_VERSION=%%v

rem Download and install Python using curl
curl -LO https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe
python-%PYTHON_VERSION%-amd64.exe /quiet /passive InstallAllUsers=1 PrependPath=1

rem Check if Python is now installed
DEL python-%PYTHON_VERSION%-amd64.exe
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python has been installed successfully.
    start "setup.bat"
) else (
    echo Failed to install Python.
)