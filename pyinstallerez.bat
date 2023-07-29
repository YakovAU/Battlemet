@echo off
setlocal enabledelayedexpansion

REM Ask for the Python script filename
set /p script_name=Enter the Python script filename (including the file extension): 

REM Ask if the executable should have a console or not
set /p has_console=Do you want the executable to have a console? (yes/no): 

REM Validate the input for the console option
if /i "!has_console!"=="yes" (
    set console_option=--console
) else if /i "!has_console!"=="no" (
    set console_option=--noconsole
) else (
    echo Invalid option for console. Please enter "yes" or "no".
    exit /b
)

REM Run PyInstaller to package the script into an executable
pyinstaller %console_option% --onefile %script_name%

echo.
echo Packaging complete. Press any key to exit.
pause > nul
