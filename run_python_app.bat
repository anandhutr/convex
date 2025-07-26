@echo off
setlocal EnableDelayedExpansion

:: Configuration
set PYTHON_PATH=C:\Python39\python.exe
set APP_NAME=app.py
set APP_DIR=D:\convex_inventory
set APP_PATH=D:\convex_inventory
set LOG_FILE=D:\convex_inventory

:: Get the current PC's IPv4 address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set "IP=%%a"
    set "IP=!IP: =!"
    goto :found_ip
)
:found_ip
if not defined IP (
    echo Failed to retrieve IP address >> "%LOG_FILE%"
    exit /b 1
)

:: Log the IP address
echo Current PC IP: %IP% at %date% %time% >> "%LOG_FILE%"

:: Check if Python is installed
if not exist "%PYTHON_PATH%" (
    echo Python not found at %PYTHON_PATH% >> "%LOG_FILE%"
    exit /b 1
)

:: Check if the application file exists
if not exist "%APP_PATH%" (
    echo Application not found at %APP_PATH% >> "%LOG_FILE%"
    exit /b 1
)

:: Run the Python application
echo Starting app.py at %date% %time% >> "%LOG_FILE%"
"%PYTHON_PATH%" "%APP_PATH%" >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% neq 0 (
    echo Failed to run app.py. Error code: %ERRORLEVEL% >> "%LOG_FILE%"
    exit /b %ERRORLEVEL%
)

echo app.py executed successfully >> "%LOG_FILE%"
pause
endlocal