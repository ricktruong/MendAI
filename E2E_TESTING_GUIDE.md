# MendAI E2E Testing Guide

## Overview

This guide covers the complete end-to-end (E2E) testing setup for MendAI, including real medical image file uploads, AI-powered medical image analysis, and comprehensive test automation.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Setup Instructions](#setup-instructions)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## Prerequisites

### Required Software

1. **Node.js** (v18 or higher)
2. **Docker Desktop** (with Docker Compose)
3. **Git**
4. **Windows OS** (scripts are Windows-optimized, Linux/Mac scripts also provided)

### Required Test Data

- **2 medical image test cases** (CT scans or X-ray images)
- Each case can contain single or multiple medical image files (slices)
- Files must be in standard medical image format (.dcm)

**Important:** Use only anonymized or synthetic medical data for testing. Never use real patient data.

---

## Quick Start

### 1. Place Your Medical Image Files

Copy your medical image test files into these directories:

```
frontend/tests/e2e/fixtures/medical-data/
├── case-001/          # Place first Medical image case here
│   └── (your .dcm files)
└── case-002/          # Place second Medical image case here
    └── (your .dcm files)
```

### 2. Validate Medical Image Files

```bash
cd frontend
npm install
npm run validate-images
```

This will scan your medical image files and generate `metadata.json`.

### 3. Run Full E2E Test Suite

```bash
# From project root
scripts\run-full-e2e.bat
```

This script will:
- Validate Medical image test data
- Start backend services
- Verify all services are healthy
- Run all E2E tests
- Generate test reports

---

## Test Structure

```
frontend/tests/
├── e2e/
│   ├── fixtures/
│   │   ├── medical-data/          # Medical image test data
│   │   │   ├── case-001/
│   │   │   ├── case-002/
│   │   │   ├── metadata.json      # Auto-generated
│   │   │   └── README.md
│   │   └── validate-images.js      # Medical image validation tool
│   │
│   ├── specs/
│   │   └── real-api/              # Real API integration tests
│   │       ├── medical-image-upload-real.spec.ts
│   │       ├── slice-analysis-real.spec.ts
│   │       └── batch-analysis-real.spec.ts
│   │
│   ├── utils/
│   │   ├── imaging-api-client.ts  # API client wrapper
│   │   ├── medical-image-manager.ts       # medical image file manager
│   │   └── test-helpers.ts        # Test utilities
│   │
│   └── config/
│       ├── test-env.json          # Environment configuration
│       └── test-env.d.ts          # TypeScript definitions
│
├── CTImageTest/                   # Alternative test data location
└── test-results/                  # Test execution results
    ├── screenshots/
    ├── failures/
    └── reports/
```

---

## Setup Instructions

### Step 1: Install Dependencies

```bash
cd frontend
npm install
```

This will install:
- Playwright Test Framework
- Axios (for API calls)
- Form-data (for file uploads)
- TypeScript type definitions

### Step 2: Install Playwright Browsers

```bash
npx playwright install chromium
```

### Step 3: Configure Test Environment

Edit `frontend/tests/e2e/config/test-env.json` if needed:

```json
{
  "backend": {
    "base_url": "http://localhost:8000",
    "imaging_service": "http://localhost:8002",
    "timeout_ms": 300000
  },
  "ai_analysis": {
    "slice_timeout_ms": 60000,
    "batch_timeout_ms": 600000
  }
}
```

### Step 4: Prepare Medical Image Test Data

1. Place medical image files in `case-001/` and `case-002/` directories
2. Run validation: `npm run validate-images`
3. Verify `metadata.json` was created successfully

### Step 5: Start Backend Services

```bash
cd backend
docker-compose up -d
```

Verify services are running:

```bash
# From project root
scripts\verify-backend.bat
```

You should see:
- Engine Service (8000): Running
- Patient Data Service (8001): Running
- Medical Imaging Service (8002): Running
- Biomedical LLM Service (8003): Running

---

## Running Tests

### Run All Tests

```bash
cd frontend
npm run test:e2e
```

### Run Only Real API Tests

```bash
npm run test:e2e:real
```

### Run Specific Test File

```bash
npx playwright test tests/e2e/specs/real-api/slice-analysis-real.spec.ts
```

### Run Tests in UI Mode (Interactive)

```bash
npm run test:e2e:ui
```

### Run Tests in Debug Mode

```bash
npm run test:e2e:debug
```

### View Test Reports

```bash
npm run test:e2e:report
```

---

## Test Coverage

### 1. Medical Image Upload Tests (`medical-image-upload-real.spec.ts`)

Tests file upload functionality:
- Single medical image file upload
- Multiple file batch upload
- Upload progress tracking
- Duplicate file detection
- Upload failure handling
- File format validation
- Large file handling
- Scan information display

**Typical Duration:** 2-5 minutes

### 2. Slice Analysis Tests (`slice-analysis-real.spec.ts`)

Tests AI-powered single slice analysis:
- Single slice analysis with real AI model
- Multiple consecutive slice analysis
- Confidence score display
- Findings visualization
- Timeout handling
- Different slice ranges (first, middle, last)
- AI model version tracking

**Typical Duration:** 5-10 minutes

### 3. Batch Analysis Tests (`batch-analysis-real.spec.ts`)

Tests complete scan batch analysis:
- Full scan batch analysis (all slices)
- Progress updates during analysis
- High-risk slice identification
- Diagnostic summary generation
- Analysis cancellation
- Result export (PDF/JSON)
- Processing time tracking

**Typical Duration:** 10-20 minutes (depending on slice count)

---

## Test Execution Flow

```
1. Test Setup (beforeAll)
   ├── Initialize API client
   ├── Load medical image metadata
   ├── Validate test data
   └── Upload test scans

2. Test Execution (each test)
   ├── Navigate to imaging page
   ├── Perform test action
   ├── Wait for API response
   ├── Validate response data
   ├── Verify UI updates
   └── Capture failures (if any)

3. Test Cleanup (afterAll)
   └── Delete uploaded test scans
```

---

## Troubleshooting

### Problem: Medical image validation Fails

**Solution:**
```bash
# Check if medical image files exist
dir frontend\tests\e2e\fixtures\medical-data\case-001

# Re-run validation
cd frontend
npm run validate-images
```

### Problem: Backend Services Not Running

**Solution:**
```bash
# Check Docker is running
docker ps

# Restart services
cd backend
docker-compose restart

# Check logs
docker-compose logs
```

### Problem: Tests Timeout

**Possible Causes:**
1. AI model taking longer than expected
2. Backend services under load
3. Network issues

**Solutions:**
- Increase timeout in `test-env.json`
- Check Docker container resources
- Run fewer tests in parallel

### Problem: Port Already in Use

**Solution:**
```bash
# Find process using port 8002 (example)
netstat -ano | findstr :8002

# Kill process by PID
taskkill /PID <PID> /F
```

### Problem: Test Fails with "Element not found"

**Possible Causes:**
- UI elements have different `data-testid` attributes
- Page hasn't loaded completely

**Solutions:**
- Check element selectors match your actual UI
- Increase wait timeouts
- Add explicit waits before assertions

---

## Advanced Usage

### Running Tests with Custom Configuration

```bash
# Set custom base URL
npx playwright test --config=playwright.config.ts

# Run with specific timeout
npx playwright test --timeout=180000

# Run in headed mode (see browser)
npx playwright test --headed
```

### Parallel Test Execution

Edit `playwright.config.ts`:

```typescript
{
  workers: 2,  // Run 2 tests in parallel
  fullyParallel: true
}
```

**Warning:** Batch analysis tests should not run in parallel due to resource constraints.

### Custom Test Data

To add more test cases:

1. Create new directory: `frontend/tests/e2e/fixtures/medical-data/case-003/`
2. Add medical image files
3. Run `npm run validate-images`
4. Update tests to use new case

### CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - name: Install dependencies
        run: cd frontend && npm install
      - name: Start backend
        run: cd backend && docker-compose up -d
      - name: Run E2E tests
        run: cd frontend && npm run test:e2e:real
```

---

## Performance Benchmarks

Expected test execution times (approximate):

| Test Suite | Single Slice | 10 Slices | 50 Slices |
|------------|--------------|-----------|-----------|
| Upload | 5-10s | 30-60s | 2-5m |
| Slice Analysis | 30-60s | 5-10m | N/A |
| Batch Analysis | N/A | 5-10m | 20-40m |

**Note:** Times vary based on:
- Hardware specifications
- AI model complexity
- Network latency
- medical image file sizes

---

## Best Practices

### 1. Test Data Management

- Use anonymized/synthetic data only
- Keep test cases small (5-20 slices for quick tests)
- Maintain separate large dataset for stress testing
- Document expected results for each test case

### 2. Test Maintenance

- Run `validate-images` after updating test data
- Keep test selectors up-to-date with UI changes
- Review and update timeouts periodically
- Clean up test data after execution

### 3. Debugging Failed Tests

1. Check test failure screenshot in `test-results/failures/`
2. Review console logs in test output
3. Run test in debug mode: `npm run test:e2e:debug`
4. Use Playwright trace viewer for detailed analysis

### 4. Resource Management

- Monitor Docker container memory usage
- Clean up old test results periodically
- Limit parallel test execution for resource-intensive tests

---

## Environment Variables

You can override configuration via environment variables:

```bash
# Set custom API URL
set IMAGING_API_URL=http://localhost:9002

# Run tests
npm run test:e2e:real
```

Supported variables:
- `IMAGING_API_URL` - Imaging service URL
- `CI` - CI mode flag
- `DEBUG` - Enable debug logging

---

## Test Reports

After test execution, view reports:

### HTML Report (Recommended)

```bash
npm run test:e2e:report
```

Opens interactive HTML report with:
- Test results summary
- Screenshots and videos
- Execution timeline
- Failure details

### JSON Report

Located at: `frontend/tests/test-results/reports/results.json`

Can be parsed for:
- CI/CD pipeline integration
- Custom reporting
- Analytics

---

## Getting Help

### Common Issues

Check the [Troubleshooting](#troubleshooting) section first.

### Logs and Debugging

- Backend logs: `docker-compose logs`
- Test output: Console during test run
- Playwright trace: `npx playwright show-trace trace.zip`

### Documentation

- Playwright Docs: https://playwright.dev
- DICOM Standard: https://www.dicomstandard.org
- MendAI Documentation: See project README

---

## Summary

You now have a complete E2E testing framework for MendAI that:

- Tests real medical image file uploads
- Validates AI-powered medical image analysis
- Covers slice-by-slice and batch analysis workflows
- Provides comprehensive test reports
- Integrates with CI/CD pipelines

**Next Steps:**

1. Place your medical image test files
2. Run `npm run validate-images`
3. Execute `scripts\run-full-e2e.bat`
4. Review test reports
5. Integrate tests into your development workflow

Good luck with testing!
