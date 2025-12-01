@echo off
echo.
echo =========================================
echo   MendAI Backend Health Check
echo =========================================
echo.

REM Check Docker is running
echo [1/5] Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running or not installed
    echo Please start Docker Desktop and try again
    exit /b 1
)
echo [OK] Docker is running

REM Check Docker Compose
echo.
echo [2/5] Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed
    exit /b 1
)
echo [OK] Docker Compose is installed

REM Check containers
echo.
echo [3/5] Checking Docker containers...
docker ps --format "table {{.Names}}\t{{.Status}}" | findstr "mendai"
if errorlevel 1 (
    echo [WARNING] No MendAI containers found running
    echo Run 'docker-compose up -d' in the backend directory
)

REM Check port availability
echo.
echo [4/5] Checking API endpoints...
echo.

REM Engine Service (Port 8000)
curl -s -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Engine Service (8000): Not responding
    set ENGINE_FAIL=1
) else (
    echo [OK] Engine Service (8000): Running
)

REM Patient Data Service (Port 8001)
curl -s -f http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Patient Data Service (8001): Not responding
    set PATIENT_FAIL=1
) else (
    echo [OK] Patient Data Service (8001): Running
)

REM Medical Imaging Service (Port 8002)
curl -s -f http://localhost:8002/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Medical Imaging Service (8002): Not responding
    set IMAGING_FAIL=1
) else (
    echo [OK] Medical Imaging Service (8002): Running
)

REM Biomedical LLM Service (Port 8003)
curl -s -f http://localhost:8003/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Biomedical LLM Service (8003): Not responding
    set LLM_FAIL=1
) else (
    echo [OK] Biomedical LLM Service (8003): Running
)

echo.
echo [5/5] Summary
echo.

REM Check if any service failed
if defined ENGINE_FAIL goto :failure
if defined PATIENT_FAIL goto :failure
if defined IMAGING_FAIL goto :failure
if defined LLM_FAIL goto :failure

echo =========================================
echo   All services are healthy!
echo =========================================
echo.
exit /b 0

:failure
echo =========================================
echo   Some services are not responding
echo =========================================
echo.
echo Please check:
echo 1. Docker containers are running: docker ps
echo 2. Check container logs: docker-compose logs
echo 3. Restart services: docker-compose restart
echo.
exit /b 1
