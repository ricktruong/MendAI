# Complete Real E2E Testing Implementation Checklist

## IMPORTANT: Project Context

**When implementing:**
- Start with clean original MendAI project
- Claude will create all test files from scratch
- Follow the structure defined in this checklist

---

## Project Objective

Implement complete real end-to-end testing including:
- Real medical image file upload
- Real backend processing
- Real AI model analysis (MONAI/PyTorch)
- Complete Slice Analysis and Batch Analysis testing
- Production environment validation

---

## Test Folder Organization

**IMPORTANT: All test-related files must be organized in a dedicated test folder structure:**

```
frontend/
├── tests/                           # Dedicated test folder (all tests here)
│   ├── e2e/                         # E2E test suite
│   │   ├── specs/                   # Test specifications
│   │   │   └── real-api/            # Real API tests
│   │   ├── fixtures/                # Test data
│   │   │   └── medical-data/        # Medical image test data
│   │   ├── config/                  # Test configuration
│   │   ├── utils/                   # Test utilities
│   │   └── mocks/                   # API mocks (for mock tests)
│   │
│   ├── CTImageTest/                 # CT Image test data folder
│   │   ├── case-001/
│   │   └── case-002/
│   │
│   └── test-results/                # Test execution results
│       ├── screenshots/
│       ├── failures/
│       └── reports/
│
├── src/                             # Application source code
├── playwright.config.ts             # Playwright configuration
└── package.json
```

---

## Phase 1: Data Preparation

### Task 1.1: Create DICOM Test Data Directory Structure

**What Claude needs to do:**
- [ ] Create `frontend/tests/e2e/fixtures/medical-data/` directory structure from scratch
- [ ] Create `frontend/tests/CTImageTest/` directory for CT image test data
- [ ] Create README with instructions for placing your 2 medical image files
- [ ] Create `.gitkeep` files for empty directories
- [ ] Create template for metadata.json

**User will provide:**
- 2 medical image files (will be uploaded to the created directories)

**Expected output:**
```
frontend/tests/
├── e2e/
│   └── fixtures/
│       └── medical-data/
│           ├── README.md                # Instructions for placing medical image files
│           ├── case-001/                # Directory for first medical image file
│           │   └── .gitkeep
│           ├── case-002/                # Directory for second medical image file
│           │   └── .gitkeep
│           └── metadata-template.json   # Template (will be populated after upload)
│
└── CTImageTest/                         # CT Image test data
    ├── case-001/                        # Link or copy of Medical image case 1
    │   └── .gitkeep
    └── case-002/                        # Link or copy of Medical image case 2
        └── .gitkeep
```

**README.md content:**
```markdown
# Medical Imaging Test Data

## Directory Structure

Place your medical image files in the following directories:
- `case-001/`: First Medical image case (CT scan or X-ray)
- `case-002/`: Second Medical image case

## After Placing Files

Run the validation script to generate metadata:
```bash
npm run validate-images
```

This will create `metadata.json` with information about your medical image files.
```

---

### Task 1.2: Create Medical Image File Validation Tool

**What Claude needs to do:**
- [ ] Create `frontend/tests/e2e/fixtures/validate-images.js` from scratch
- [ ] Implement medical image file scanning and validation
- [ ] Generate metadata.json automatically
- [ ] Add validation script to package.json

**Expected code structure:**
```javascript
// frontend/tests/e2e/fixtures/validate-images.js
// Dependencies: medical-image-parser or dcmjs (will be installed)

const fs = require('fs');
const path = require('path');

class DicomValidator {
  constructor(dataDir) {
    this.dataDir = dataDir;
  }

  // Scan all medical image files
  scanDicomFiles() { }

  // Validate medical image format
  validateFile(filePath) { }

  // Extract metadata
  extractMetadata(filePath) { }

  // Generate metadata.json
  generateMetadataReport() { }
}

// Main execution
const validator = new DicomValidator('./tests/e2e/fixtures/medical-data');
validator.generateMetadataReport();
```

**Package.json addition:**
```json
{
  "scripts": {
    "validate-images": "node tests/e2e/fixtures/validate-images.js"
  },
  "devDependencies": {
    "medical-image-parser": "^1.8.x"
  }
}
```

**Expected metadata.json output:**
```json
{
  "generated_at": "2025-11-25T10:00:00Z",
  "cases": [
    {
      "case_id": "001",
      "directory": "case-001",
      "file_count": 24,
      "files": ["slice-001.dcm", "slice-002.dcm", "..."],
      "metadata": {
        "patient_id": "extracted-from-dicom",
        "modality": "CT",
        "body_part": "CHEST",
        "slice_thickness": "5mm"
      }
    },
    {
      "case_id": "002",
      "directory": "case-002",
      "file_count": 18,
      "files": ["..."],
      "metadata": { }
    }
  ]
}
```

---

### Task 1.3: Create Test Environment Configuration

**What Claude needs to do:**
- [ ] Create `e2e/config/` directory
- [ ] Create `test-env.json` configuration file
- [ ] Create `test-env.d.ts` TypeScript definitions

**Expected files:**

`e2e/config/test-env.json`:
```json
{
  "backend": {
    "base_url": "http://localhost:8000",
    "imaging_service": "http://localhost:8002",
    "timeout_ms": 300000
  },
  "ai_analysis": {
    "slice_timeout_ms": 60000,
    "batch_timeout_ms": 600000,
    "max_retries": 3,
    "retry_delay_ms": 5000
  },
  "test_data": {
    "medical_image_dir": "./e2e/fixtures/medical-data",
    "metadata_file": "./e2e/fixtures/medical-data/metadata.json"
  },
  "screenshots": {
    "enabled": true,
    "directory": "./e2e/test-results/screenshots"
  }
}
```

`e2e/config/test-env.d.ts`:
```typescript
export interface TestEnvironment {
  backend: {
    base_url: string;
    imaging_service: string;
    timeout_ms: number;
  };
  ai_analysis: {
    slice_timeout_ms: number;
    batch_timeout_ms: number;
    max_retries: number;
    retry_delay_ms: number;
  };
  test_data: {
    medical_image_dir: string;
    metadata_file: string;
  };
  screenshots: {
    enabled: boolean;
    directory: string;
  };
}
```

---

## Phase 2: Backend Verification and Configuration

### Task 2.1: Backend Health Check Script

**What Claude needs to do:**
- [ ] Create `scripts/verify-backend.bat` (Windows)
- [ ] Create `scripts/verify-backend.sh` (Linux/Mac - optional)
- [ ] Check all Docker services
- [ ] Verify API endpoints
- [ ] Check AI model status

**Expected script (verify-backend.bat):**
```batch
@echo off
echo Verifying backend services...
echo.

REM Check Docker is running
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running
    exit /b 1
)

REM Check containers
echo Checking Docker containers...
docker-compose ps | findstr "Up"

REM Check port availability
echo.
echo Checking API endpoints...

REM Engine Service
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Engine Service (8000): Not responding
) else (
    echo [OK] Engine Service (8000): Running
)

REM Patient Data Service
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Patient Data Service (8001): Not responding
) else (
    echo [OK] Patient Data Service (8001): Running
)

REM Medical Imaging Service
curl -s http://localhost:8002/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Medical Imaging Service (8002): Not responding
) else (
    echo [OK] Medical Imaging Service (8002): Running
)

REM Biomedical LLM Service
curl -s http://localhost:8003/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Biomedical LLM Service (8003): Not responding
) else (
    echo [OK] Biomedical LLM Service (8003): Running
)

echo.
echo Verification complete.
```

---

### Task 2.2: Database Seed Script (Optional)

**What Claude needs to do:**
- [ ] Create `scripts/seed-test-data.sql`
- [ ] Create execution wrapper `scripts/seed-database.bat`
- [ ] Add test patient records
- [ ] Add cleanup queries

**Expected SQL (seed-test-data.sql):**
```sql
-- Clean existing test data
DELETE FROM medical_images WHERE patient_id LIKE 'E2E-TEST-%';
DELETE FROM patients WHERE id LIKE 'E2E-TEST-%';

-- Create test patients
INSERT INTO patients (id, name, age, gender, created_at) VALUES
  ('E2E-TEST-001', 'Test Patient Case 001', 55, 'M', CURRENT_TIMESTAMP),
  ('E2E-TEST-002', 'Test Patient Case 002', 62, 'F', CURRENT_TIMESTAMP);

-- Verify
SELECT id, name, age FROM patients WHERE id LIKE 'E2E-TEST-%';
```

**Execution script (seed-database.bat):**
```batch
@echo off
docker exec -i mendai-database-1 psql -U postgres -d mendai < scripts/seed-test-data.sql
```

---

## Phase 3: Test Code Implementation

### Task 3.1: Real Upload Test

**What Claude needs to do:**
- [ ] Create directory `e2e/specs/real-api/`
- [ ] Create `dicom-upload-real.spec.ts` from scratch
- [ ] Implement all upload test cases
- [ ] Add proper error handling and cleanup

**File structure:**
```typescript
// e2e/specs/real-api/dicom-upload-real.spec.ts

import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import testEnv from '../../config/test-env.json';

test.describe('Real Medical Image Upload Tests', () => {
  const metadata = JSON.parse(
    fs.readFileSync(testEnv.test_data.metadata_file, 'utf-8')
  );

  test.beforeEach(async ({ page }) => {
    // No API mocks - testing real backend
    await page.goto('/patient/E2E-TEST-001/imaging');
  });

  test('should upload single medical image file successfully', async ({ page }) => {
    // Implementation
  });

  test('should upload multiple medical image files (batch)', async ({ page }) => {
    // Implementation
  });

  // Additional test cases...
});
```

**Test cases to implement:**
1. Upload single DICOM slice and verify backend storage
2. Batch upload complete CT scan (all slices from case-001)
3. Verify upload progress display
4. Verify duplicate upload detection
5. Verify upload failure handling and retry
6. Verify large file upload handling

---

### Task 3.2: Real Slice Analysis Test

**What Claude needs to do:**
- [ ] Create `slice-analysis-real.spec.ts` from scratch
- [ ] Implement AI analysis tests with real backend
- [ ] Add wait mechanisms for AI processing
- [ ] Verify result structure and content

**File structure:**
```typescript
// e2e/specs/real-api/slice-analysis-real.spec.ts

import { test, expect } from '@playwright/test';
import { ImagingAPIClient } from '../../utils/imaging-api-client';
import testEnv from '../../config/test-env.json';

test.describe('Real Slice Analysis Tests', () => {
  let apiClient: ImagingAPIClient;

  test.beforeAll(() => {
    apiClient = new ImagingAPIClient(testEnv.backend.imaging_service);
  });

  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/E2E-TEST-001/imaging');
  });

  test('should analyze normal slice with real AI', async ({ page }) => {
    // Select slice
    await page.locator('[data-testid="slice-selector"]').fill('5');

    // Trigger analysis
    await page.click('[data-testid="analyze-slice"]');

    // Wait for real AI processing (may take 30-60 seconds)
    const response = await page.waitForResponse(
      res => res.url().includes('/analyze/slice') && res.ok(),
      { timeout: testEnv.ai_analysis.slice_timeout_ms }
    );

    // Verify response
    const result = await response.json();
    expect(result).toHaveProperty('findings');
    expect(result).toHaveProperty('ai_confidence');
  });

  // Additional test cases...
});
```

**Test cases to implement:**
1. Analyze normal slice (expect low/no findings)
2. Analyze slice with abnormalities (verify detection)
3. Compare results from consecutive slices
4. Verify AI confidence score range (0-1)
5. Verify lesion coordinates and dimensions
6. Test analysis timeout handling
7. Verify progress updates during analysis

---

### Task 3.3: Real Batch Analysis Test

**What Claude needs to do:**
- [ ] Create `batch-analysis-real.spec.ts` from scratch
- [ ] Implement batch processing tests
- [ ] Handle long-running operations (5-10 minutes)
- [ ] Verify comprehensive reports

**File structure:**
```typescript
// e2e/specs/real-api/batch-analysis-real.spec.ts

import { test, expect } from '@playwright/test';
import testEnv from '../../config/test-env.json';

test.describe('Real Batch Analysis Tests', () => {
  // Increase timeout for batch operations
  test.setTimeout(testEnv.ai_analysis.batch_timeout_ms);

  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/E2E-TEST-001/imaging');
  });

  test('should batch analyze complete CT scan', async ({ page }) => {
    // Trigger batch analysis
    await page.click('[data-testid="batch-analyze"]');

    // Monitor progress
    const progressBar = page.locator('[data-testid="analysis-progress"]');
    await expect(progressBar).toBeVisible({ timeout: 5000 });

    // Wait for completion (real AI processing all slices)
    await page.waitForResponse(
      res => res.url().includes('/analyze/batch') && res.ok(),
      { timeout: testEnv.ai_analysis.batch_timeout_ms }
    );

    // Verify results
    const results = page.locator('[data-testid="batch-results"]');
    await expect(results).toBeVisible({ timeout: 30000 });
  });

  // Additional test cases...
});
```

**Test cases to implement:**
1. Batch analyze complete case (all slices)
2. Verify overall analysis summary
3. Verify high-risk slice identification
4. Verify diagnostic recommendations
5. Test analysis cancellation
6. Test progress tracking (X/Y slices completed)
7. Verify result export (PDF/JSON)
8. Test concurrent batch analysis

---

### Task 3.4: Analysis Result Validation Test

**What Claude needs to do:**
- [ ] Create `analysis-validation.spec.ts`
- [ ] Implement result quality checks
- [ ] Compare against expected baselines
- [ ] Test reproducibility

**Test cases:**
1. Validate AI accuracy on known cases
2. Test result reproducibility (same slice analyzed twice)
3. Verify confidence score correlation
4. Test edge case handling

---

### Task 3.5: UI Interaction Test

**What Claude needs to do:**
- [ ] Create `imaging-ui-real.spec.ts`
- [ ] Test result display and interaction
- [ ] Verify image annotations
- [ ] Test navigation features

**Test cases:**
1. Verify analysis result list display
2. Verify lesion annotations on images
3. Test clicking lesions for details
4. Test slice navigation/slider
5. Test zoom and pan functions
6. Verify window/level adjustments
7. Test annotated image export

---

### Task 3.6: Report Generation Test

**What Claude needs to do:**
- [ ] Create `report-generation-real.spec.ts`
- [ ] Test PDF report generation (English only)
- [ ] Test JSON data export
- [ ] Verify report completeness

**Test cases:**
1. Generate slice analysis report
2. Generate batch analysis report (complete case)
3. Verify PDF contains all required sections (English)
4. Verify JSON export structure
5. Test report download
6. Verify English language in all report content

**Important: All report content must be in English**

---

### Task 3.7: Performance Test

**What Claude needs to do:**
- [ ] Create `performance-test.spec.ts`
- [ ] Measure analysis times
- [ ] Test concurrent operations
- [ ] Monitor resource usage

**Test cases:**
1. Measure single slice analysis time
2. Measure batch analysis total time
3. Test concurrent analysis (3 cases)
4. Monitor memory usage
5. Verify queue management
6. Test large case processing (100+ slices)

---

## Phase 4: Utilities and Infrastructure

### Task 4.1: Medical Image Manager Utility

**What Claude needs to do:**
- [ ] Create `e2e/utils/medical-image-manager.ts` from scratch
- [ ] Implement medical image file management
- [ ] Provide convenient test data access

**Expected implementation:**
```typescript
// e2e/utils/medical-image-manager.ts

import fs from 'fs';
import path from 'path';

interface CaseMetadata {
  case_id: string;
  directory: string;
  file_count: number;
  files: string[];
  metadata: Record<string, any>;
}

export class MedicalImageManager {
  private metadataPath: string;
  private metadata: any;

  constructor(metadataPath: string) {
    this.metadataPath = metadataPath;
    this.loadMetadata();
  }

  private loadMetadata() {
    this.metadata = JSON.parse(fs.readFileSync(this.metadataPath, 'utf-8'));
  }

  getCaseSlices(caseId: string): string[] {
    const caseData = this.metadata.cases.find(c => c.case_id === caseId);
    if (!caseData) throw new Error(`Case ${caseId} not found`);

    return caseData.files.map(file =>
      path.join(caseData.directory, file)
    );
  }

  getCaseMetadata(caseId: string): CaseMetadata {
    const caseData = this.metadata.cases.find(c => c.case_id === caseId);
    if (!caseData) throw new Error(`Case ${caseId} not found`);
    return caseData;
  }

  getSliceByIndex(caseId: string, index: number): string {
    const slices = this.getCaseSlices(caseId);
    if (index < 0 || index >= slices.length) {
      throw new Error(`Invalid slice index ${index}`);
    }
    return slices[index];
  }

  async cleanup(): Promise<void> {
    // Cleanup uploaded test data from backend
  }
}
```

---

### Task 4.2: API Client Wrapper

**What Claude needs to do:**
- [ ] Create `e2e/utils/imaging-api-client.ts` from scratch
- [ ] Implement type-safe API calls
- [ ] Add retry logic and error handling

**Expected implementation:**
```typescript
// e2e/utils/imaging-api-client.ts

import axios, { AxiosInstance } from 'axios';

interface UploadResponse {
  success: boolean;
  scan_id: string;
  patient_id: string;
  file_count: number;
}

interface AnalysisResult {
  success: boolean;
  scan_id: string;
  slice_number?: number;
  findings: Array<{
    type: string;
    location: string;
    size_mm: number;
    confidence: number;
    coordinates: { x: number; y: number };
  }>;
  ai_confidence: number;
  summary: string;
}

interface BatchAnalysisResult {
  success: boolean;
  scan_id: string;
  total_slices: number;
  analyzed_slices: number;
  overall_summary: {
    total_findings: number;
    high_risk_slices: number[];
    diagnosis: string;
  };
}

export class ImagingAPIClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 300000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }

  async uploadMedicalImages(
    filePath: string,
    patientId: string
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));
    formData.append('patient_id', patientId);

    const response = await this.client.post('/api/v0/imaging/upload', formData);
    return response.data;
  }

  async analyzeSlice(
    scanId: string,
    sliceNumber: number
  ): Promise<AnalysisResult> {
    const response = await this.client.post(
      `/api/v0/imaging/analyze/slice/${scanId}`,
      { slice_number: sliceNumber }
    );
    return response.data;
  }

  async analyzeBatch(scanId: string): Promise<BatchAnalysisResult> {
    const response = await this.client.post(
      `/api/v0/imaging/analyze/batch/${scanId}`
    );
    return response.data;
  }

  async getAnalysisStatus(analysisId: string): Promise<any> {
    const response = await this.client.get(
      `/api/v0/imaging/analysis/${analysisId}/status`
    );
    return response.data;
  }

  async downloadReport(
    analysisId: string,
    format: 'pdf' | 'json'
  ): Promise<Buffer> {
    const response = await this.client.get(
      `/api/v0/imaging/analysis/${analysisId}/report`,
      {
        params: { format },
        responseType: 'arraybuffer'
      }
    );
    return Buffer.from(response.data);
  }

  async waitForAnalysisComplete(
    analysisId: string,
    timeout: number = 300000,
    pollInterval: number = 5000
  ): Promise<AnalysisResult> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const status = await this.getAnalysisStatus(analysisId);

      if (status.completed) {
        return status.result;
      }

      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new Error(`Analysis timeout after ${timeout}ms`);
  }
}
```

---

### Task 4.3: Test Helper Functions

**What Claude needs to do:**
- [ ] Extend `e2e/utils/test-helpers.ts`
- [ ] Add imaging-specific helpers
- [ ] Add wait and validation functions

**New functions to add:**
```typescript
// Additional functions for test-helpers.ts

export async function waitForAnalysisComplete(
  page: Page,
  timeout: number = 60000
): Promise<void> {
  await page.waitForSelector('[data-testid="analysis-complete"]', {
    timeout,
    state: 'visible'
  });
}

export function validateAnalysisResult(result: any): boolean {
  return (
    result.hasOwnProperty('findings') &&
    result.hasOwnProperty('ai_confidence') &&
    result.ai_confidence >= 0 &&
    result.ai_confidence <= 1
  );
}

export function compareAnalysisResults(
  result1: any,
  result2: any
): number {
  // Calculate similarity score (0-1)
  // Compare findings count, locations, confidence scores
  // Return similarity percentage
}

export async function captureFailureContext(
  page: Page,
  testName: string
): Promise<void> {
  const timestamp = new Date().toISOString().replace(/:/g, '-');
  const screenshotPath = `test-results/failures/${testName}-${timestamp}.png`;

  await page.screenshot({ path: screenshotPath, fullPage: true });

  const logs = await page.evaluate(() => {
    return (window as any).testLogs || [];
  });

  fs.writeFileSync(
    `test-results/failures/${testName}-${timestamp}-logs.json`,
    JSON.stringify(logs, null, 2)
  );
}

export async function cleanupTestData(patientId: string): Promise<void> {
  // API call to delete test data from backend
  // Or database cleanup
}
```

---

### Task 4.4: Test Logger

**What Claude needs to do:**
- [ ] Create `e2e/utils/test-logger.ts` from scratch
- [ ] Implement detailed logging
- [ ] Generate HTML reports

**Expected implementation:**
```typescript
// e2e/utils/test-logger.ts

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warn' | 'error';
  message: string;
  data?: any;
}

export class TestLogger {
  private logs: LogEntry[] = [];
  private startTime: number;

  constructor() {
    this.startTime = Date.now();
  }

  log(level: 'info' | 'warn' | 'error', message: string, data?: any) {
    this.logs.push({
      timestamp: new Date().toISOString(),
      level,
      message,
      data
    });
  }

  logAnalysisStart(caseId: string, sliceNumber?: number) {
    const msg = sliceNumber
      ? `Starting slice analysis: Case ${caseId}, Slice ${sliceNumber}`
      : `Starting batch analysis: Case ${caseId}`;
    this.log('info', msg);
  }

  logAnalysisResult(result: any) {
    this.log('info', 'Analysis completed', result);
  }

  logPerformanceMetric(metric: string, value: number) {
    this.log('info', `Performance: ${metric}`, { value, unit: 'ms' });
  }

  generateReport(): string {
    const duration = Date.now() - this.startTime;

    // Generate HTML report
    return `
      <html>
        <head><title>Test Execution Report</title></head>
        <body>
          <h1>E2E Test Report</h1>
          <p>Duration: ${duration}ms</p>
          <h2>Logs</h2>
          <pre>${JSON.stringify(this.logs, null, 2)}</pre>
        </body>
      </html>
    `;
  }

  saveToFile(filepath: string) {
    fs.writeFileSync(filepath, this.generateReport());
  }
}
```

---

## Phase 5: Test Execution and CI/CD

### Task 5.1: Test Execution Script

**What Claude needs to do:**
- [ ] Create `scripts/run-full-e2e.bat` from scratch
- [ ] Add environment validation
- [ ] Add service startup/verification
- [ ] Add test execution and reporting

**Expected script:**
```batch
@echo off
echo.
echo =========================================
echo   MendAI Full E2E Test Suite
echo =========================================
echo.

REM Step 1: Verify medical image data
echo [1/6] Verifying Medical image test data...
node frontend\e2e\fixtures\validate-images.js
if errorlevel 1 (
    echo ERROR: Medical image validation failed
    pause
    exit /b 1
)

REM Step 2: Start backend services
echo.
echo [2/6] Starting backend services...
cd backend
docker-compose up -d
cd ..

REM Step 3: Wait for services
echo.
echo [3/6] Waiting for services to be ready...
timeout /t 10 /nobreak
call scripts\verify-backend.bat
if errorlevel 1 (
    echo ERROR: Backend services not ready
    pause
    exit /b 1
)

REM Step 4: Run tests
echo.
echo [4/6] Running E2E tests...
cd frontend
npx playwright test real-api/ --reporter=html,json
set TEST_RESULT=%errorlevel%

REM Step 5: Generate report
echo.
echo [5/6] Generating test report...
node scripts\generate-report.js

REM Step 6: Cleanup (optional)
echo.
echo [6/6] Cleanup...
REM Uncomment to stop services after testing
REM cd backend
REM docker-compose down
REM cd ..

echo.
if %TEST_RESULT% equ 0 (
    echo =========================================
    echo   All tests passed!
    echo =========================================
) else (
    echo =========================================
    echo   Some tests failed. Check report.
    echo =========================================
)

pause
exit /b %TEST_RESULT%
```

---

### Task 5.2: CI/CD Configuration

**What Claude needs to do:**
- [ ] Create `.github/workflows/full-e2e.yml`
- [ ] Configure GitHub Actions
- [ ] Add medical image data caching
- [ ] Add result notifications

**Expected workflow:**
```yaml
name: Full E2E Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:     # Manual trigger
  pull_request:
    branches: [ main ]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 120

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Restore Medical image test data cache
        uses: actions/cache@v3
        with:
          path: frontend/e2e/fixtures/medical-data
          key: dicom-test-data-v1

      - name: Install dependencies
        run: |
          cd frontend
          npm install
          npx playwright install --with-deps chromium

      - name: Start backend services
        run: |
          cd backend
          docker-compose up -d
          sleep 30

      - name: Verify backend health
        run: ./scripts/verify-backend.sh

      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test real-api/

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: frontend/playwright-report/

      - name: Notify on failure
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'E2E Tests Failed',
              body: 'Full E2E test suite failed. Check the workflow run for details.'
            })
```

---

### Task 5.3: Report Template

**What Claude needs to do:**
- [ ] Create `scripts/generate-report.js`
- [ ] Generate HTML report from test results
- [ ] Include visualizations and statistics

**Expected script:**
```javascript
// scripts/generate-report.js

const fs = require('fs');
const path = require('path');

function generateReport() {
  // Read test results JSON
  const resultsPath = 'frontend/test-results.json';
  const results = JSON.parse(fs.readFileSync(resultsPath, 'utf-8'));

  // Calculate statistics
  const stats = {
    total: results.suites.length,
    passed: results.suites.filter(s => s.status === 'passed').length,
    failed: results.suites.filter(s => s.status === 'failed').length,
    duration: results.duration
  };

  // Generate HTML
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>MendAI E2E Test Report</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .passed { color: green; }
        .failed { color: red; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
      </style>
    </head>
    <body>
      <h1>MendAI Full E2E Test Report</h1>

      <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: ${stats.total}</p>
        <p class="passed">Passed: ${stats.passed}</p>
        <p class="failed">Failed: ${stats.failed}</p>
        <p>Duration: ${(stats.duration / 1000).toFixed(2)}s</p>
      </div>

      <h2>Test Results</h2>
      <table>
        <tr>
          <th>Test Suite</th>
          <th>Status</th>
          <th>Duration</th>
        </tr>
        ${results.suites.map(suite => `
          <tr>
            <td>${suite.title}</td>
            <td class="${suite.status}">${suite.status}</td>
            <td>${(suite.duration / 1000).toFixed(2)}s</td>
          </tr>
        `).join('')}
      </table>

      <p>Generated at: ${new Date().toISOString()}</p>
    </body>
    </html>
  `;

  // Save report
  fs.writeFileSync('test-report.html', html);
  console.log('Report generated: test-report.html');
}

generateReport();
```

---

## Phase 6: Documentation

### Task 6.1: Execution Guide

**What Claude needs to do:**
- [ ] Create `FULL_E2E_EXECUTION_GUIDE.md`
- [ ] Document setup process
- [ ] Document execution steps
- [ ] Add troubleshooting section

---

### Task 6.2: DICOM Data Guide

**What Claude needs to do:**
- [ ] Create `DICOM_TEST_DATA_GUIDE.md`
- [ ] Document data organization
- [ ] Document adding new cases
- [ ] Add privacy/compliance notes

---

### Task 6.3: AI Baseline Results

**What Claude needs to do:**
- [ ] Create `AI_BASELINE_RESULTS.md`
- [ ] Document expected AI results
- [ ] Record model versions
- [ ] Maintain regression baseline

---

## Implementation Priority

### First Session (Core Functionality)
1. Task 1.1 - DICOM directory structure
2. Task 1.2 - Medical image validation tool
3. Task 2.1 - Backend health check
4. Task 3.2 - Slice analysis tests
5. Task 3.3 - Batch analysis tests
6. Task 4.2 - API client wrapper
7. Task 5.1 - Execution script

### Second Session (Expansion)
8. Task 3.1 - Upload tests
9. Task 3.5 - UI interaction tests
10. Task 3.6 - Report generation tests
11. Task 4.1 - DICOM manager
12. Task 4.3 - Test helpers

### Third Session (Production Ready)
13. Task 3.4 - Result validation
14. Task 3.7 - Performance tests
15. Task 4.4 - Test logger
16. Task 5.2 - CI/CD
17. All documentation

---

## Summary

**Total Tasks:** 22
**Estimated Code:** ~4000 lines
**Estimated Sessions:** 7-10

**Key Points:**
- All files created from scratch in original MendAI project
- No dependencies on current "MendAI - testing" folder
- All code and documentation in English
- No emoji characters
- User provides 2 medical image files
- Communication with Claude in Chinese, but all outputs in English

---

## Next Session Template

**When ready, tell Claude:**

```
"开始实现完整的真实E2E测试。

请从以下任务开始：
- Task 1.1: 创建DICOM目录结构
- Task 1.2: 创建验证工具
- Task 3.2: 编写Slice Analysis真实测试

记住：
- 所有代码和文档用英文
- 不要使用emoji
- 我会把DICOM文件放到你创建的目录中"
```

---

**This checklist is now ready for implementation in your original MendAI project!**
