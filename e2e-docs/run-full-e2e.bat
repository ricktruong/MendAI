@echo off
echo.
echo =========================================
echo   MendAI Full E2E Test Suite
echo =========================================
echo.

set START_TIME=%time%

REM Step 1: Verify DICOM data
echo [1/6] Verifying DICOM test data...
cd frontend
call npm run validate-images
if errorlevel 1 (
    echo.
    echo ERROR: DICOM validation failed
    echo Please place your medical image files in:
    echo   frontend/tests/e2e/fixtures/medical-data/case-001/
    echo   frontend/tests/e2e/fixtures/medical-data/case-002/
    echo.
    pause
    exit /b 1
)
cd ..

REM Step 2: Check backend directory
echo.
echo [2/6] Checking backend services...
if not exist "backend" (
    echo ERROR: Backend directory not found
    echo Please ensure you are in the MendAI root directory
    pause
    exit /b 1
)

REM Step 3: Start backend services
echo.
echo [3/6] Starting backend services...
cd backend
docker-compose up -d
cd ..

REM Step 4: Wait for services to be ready
echo.
echo [4/6] Waiting for services to be ready...
echo This may take 30-60 seconds...
timeout /t 30 /nobreak > nul

call scripts\verify-backend.bat
if errorlevel 1 (
    echo.
    echo ERROR: Backend services not ready
    echo Please check Docker containers:
    echo   docker ps
    echo   docker-compose logs
    echo.
    pause
    exit /b 1
)

REM Step 5: Run E2E tests
echo.
echo [5/6] Running E2E tests...
echo This may take several minutes...
echo.

cd frontend

REM Install dependencies if needed
if not exist "node_modules\@playwright" (
    echo Installing test dependencies...
    call npm install
    call npx playwright install chromium
)

REM Run tests
call npx playwright test tests/e2e/specs/real-api/ --reporter=html,list

set TEST_RESULT=%errorlevel%

cd ..

REM Step 6: Generate report
echo.
echo [6/6] Test execution completed
echo.

if %TEST_RESULT% equ 0 (
    echo =========================================
    echo   All tests passed!
    echo =========================================
    echo.
    echo View detailed report:
    echo   cd frontend
    echo   npm run test:e2e:report
    echo.
) else (
    echo =========================================
    echo   Some tests failed
    echo =========================================
    echo.
    echo View detailed report:
    echo   cd frontend
    echo   npm run test:e2e:report
    echo.
    echo Check failure screenshots:
    echo   frontend\tests\test-results\failures\
    echo.
)

set END_TIME=%time%
echo Started:  %START_TIME%
echo Finished: %END_TIME%
echo.

REM Optional: Stop services
echo.
echo Press any key to stop backend services, or Ctrl+C to keep them running...
pause > nul

echo.
echo Stopping backend services...
cd backend
docker-compose down
cd ..

echo.
echo Done!
pause
exit /b %TEST_RESULT%
