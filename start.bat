@echo off
title git-regret
color 0C

echo.
echo  ========================================
echo  git-regret - Secret Scanner Installation
echo  ========================================
echo.

:: Python kontrolu
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://python.org.
    pause
    exit /b 1
)

echo [OK] Python found.

:: git kontrolu
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git not found!
    echo Please install Git from https://git-scm.com.
    pause
    exit /b 1
)

echo [OK] Git found.

:: Kutuphaneleri kontrol et ve kur
echo.
echo [*] Checking dependencies......

python -c "import click" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing click...
    python -m pip install click -q
)

python -c "import git" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing gitpython...
    python -m pip install gitpython -q
)

python -c "import rich" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing rich...
    python -m pip install rich -q
)

python -c "import questionary" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing questionary...
    python -m pip install questionary -q
)

echo [OK] All dependencies installed.

:: Paketi kur
echo.
echo [*] Installing git-regret...
python -m pip install -e . -q

if %errorlevel% neq 0 (
    echo [ERROR] Installation failed!
    pause
    exit /b 1
)

echo [OK] Installation completed.
echo.
echo ========================================
echo.

:: TUI baslat
git-regret-ui

pause
