@echo off
setlocal

where py >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python interpreter was not found on PATH.
        pause
        exit /b 1
    )
    set "PY_CMD=python"
) else (
    set "PY_CMD=py -3"
)

echo Checking for pygame...
%PY_CMD% -c "import pygame" 2>nul
if errorlevel 1 (
    echo Pygame not found. Installing dependencies...
    %PY_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Failed to install required Python packages.
        pause
        exit /b 1
    )
)

echo Checking for PyInstaller...
%PY_CMD% -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing PyInstaller...
    %PY_CMD% -m pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

echo Compiling Python modules...
%PY_CMD% -m py_compile main.py game_controller.py assets.py menus.py ui_components.py constants.py
if errorlevel 1 (
    echo.
    echo Compilation failed. Fix the errors and run this file again.
    pause
    exit /b 1
)

echo Checking for existing built project...
if exist "dist\Project C.exe" (
    echo Found existing dist\Project C.exe, deleting it...
    del /f /q "dist\Project C.exe"
)
if exist "Project C.spec" (
    echo Deleting old Project C.spec...
    del /f /q "Project C.spec"
)

echo Building executable...
%PY_CMD% -m PyInstaller --noconfirm --clean --onefile --windowed --name "Project C" --add-data "embed;embed" main.py
if errorlevel 1 (
    echo.
    echo PyInstaller failed to build the executable.
    pause
    exit /b 1
)

echo.
echo Build complete. Executable created at dist\"Project C".exe

endlocal
