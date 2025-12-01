# MendAI E2E Test Suite

## Quick Start

### 1. Add Medical Image Test Files

Place your medical image test files (NIfTI, DICOM) in:
- `e2e/fixtures/medical-data/case-001/`
- `e2e/fixtures/medical-data/case-002/`

### 2. Validate Test Data

```bash
npm run validate-images
```

### 3. Run Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run only real API tests
npm run test:e2e:real

# Run with UI
npm run test:e2e:ui

# View report
npm run test:e2e:report
```

## Test Suite Overview

### Slice Analysis Tests
- Single slice AI analysis
- Multiple slice analysis
- Confidence scoring
- Finding visualization

**Location:** `e2e/specs/real-api/slice-analysis-real.spec.ts`

### Batch Analysis Tests
- Complete scan analysis
- Progress monitoring
- High-risk slice identification
- Report generation

**Location:** `e2e/specs/real-api/batch-analysis-real.spec.ts`

## Directory Structure

```
tests/
├── e2e/
│   ├── fixtures/
│   │   └── medical-data/        # Place medical image files (NIfTI, DICOM) here
│   ├── specs/
│   │   └── real-api/            # Test specifications
│   ├── utils/                   # Test utilities
│   └── config/                  # Configuration
├── CTImageTest/                 # Alternative test data
└── test-results/                # Test outputs
```

## Configuration

Edit `e2e/config/test-env.json` to customize:
- Backend URLs
- Timeout settings
- Test patient IDs
- Screenshot options

## Utilities

### Medical Image Manager
Manages medical image test files (NIfTI, DICOM) and metadata.

```typescript
import { MedicalImageManager } from './utils/medical-image-manager';

const manager = new MedicalImageManager(metadataPath);
const slices = manager.getCaseSlices('001');
```

### API Client
Type-safe API wrapper for imaging service.

```typescript
import { ImagingAPIClient } from './utils/imaging-api-client';

const client = new ImagingAPIClient('http://localhost:8002');
const result = await client.analyzeSlice(scanId, sliceNumber);
```

### Test Helpers
Common test utilities and assertions.

```typescript
import { waitForAPIResponse, validateAnalysisResult } from './utils/test-helpers';
```

## Before Running Tests

1. Ensure Docker is running
2. Start backend services: `docker-compose up -d`
3. Verify services: Run `scripts/verify-backend.bat`
4. Install dependencies: `npm install`
5. Install Playwright: `npx playwright install chromium`

## Full Test Execution

From project root:

```bash
scripts\run-full-e2e.bat
```

This will:
1. Validate medical image data
2. Start backend services
3. Verify service health
4. Run all E2E tests
5. Generate reports

## Troubleshooting

### Medical Image Validation Fails
- Check files exist in `case-001/` and `case-002/`
- Ensure files are valid medical image format (NIfTI or DICOM)
- Re-run `npm run validate-images`

### Backend Not Running
```bash
docker ps                    # Check containers
docker-compose logs          # View logs
docker-compose restart       # Restart services
```

### Tests Timeout
- Increase timeout in `test-env.json`
- Check Docker container resources
- Ensure AI service is responding

## Documentation

For detailed documentation, see:
- `e2e-docs/E2E_TESTING_GUIDE.md` (project root)
- `e2e-docs/FULL_E2E_IMPLEMENTATION_CHECKLIST.md` (project root)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review test execution logs
3. Check Playwright documentation: https://playwright.dev

---

**Important:** Use only anonymized or synthetic medical data for testing. Never commit real patient data to version control.
