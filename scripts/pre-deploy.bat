@echo off
REM Pre-deployment validation script for Aether-Thread (Windows)
REM Usage: scripts\pre-deploy.bat
REM This script validates code before committing/pushing to CI/CD

setlocal enabledelayedexpansion

REM Configuration
set PYTHON_VERSION=3.11
set SOURCE_DIR=src
set MAX_THREADS=32

echo.
echo ╔════════════════════════════════════════════╗
echo ║   Pre-Deployment Validation ^(Aether^)      ║
echo ╚════════════════════════════════════════════╝
echo.

REM Check if aether is installed
echo 1^) Checking Aether installation...
python -c "import aether" >nul 2>&1
if errorlevel 1 (
    echo ^! Aether not found. Installing...
    pip install aether-thread
)
echo [OK] Aether found
echo.

REM Check Python version
echo 2^) Checking Python version...
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set CURRENT_PYTHON=%%i
echo Python version: %CURRENT_PYTHON%
echo [OK] Python ready
echo.

REM Run standard thread-safety audit
echo 3^) Running thread-safety audit...
aether check %SOURCE_DIR% --verbose
if errorlevel 1 (
    echo [ERROR] Thread-safety issues found!
    exit /b 1
)
echo [OK] No standard thread-safety issues
echo.

REM Run free-threaded specific checks
echo 4^) Running free-threaded Python checks...
aether check %SOURCE_DIR% --free-threaded --verbose
if errorlevel 1 (
    echo [ERROR] Free-threading issues found!
    exit /b 1
)
echo [OK] No free-threading issues
echo.

REM Check environment
echo 5^) Checking environment compatibility...
aether status
echo [OK] Environment checked
echo.

REM Final summary
echo ═════════════════════════════════════════════
echo [OK] All pre-deployment checks passed!
echo ═════════════════════════════════════════════
echo.
echo ^> Summary:
echo   [OK] Standard thread-safety audit
echo   [OK] Free-threaded Python checks
echo   [OK] Environment compatibility
echo.
echo ^> You're ready to:
echo   1. git commit
echo   2. git push ^(triggers CI/CD^)
echo   3. Create pull request
echo.
pause
