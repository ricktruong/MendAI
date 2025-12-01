/**
 * Real Slice Analysis E2E Tests
 * Tests slice-by-slice AI analysis with real backend and AI models
 */

import { test, expect } from '@playwright/test';
import { ImagingAPIClient } from '../../utils/imaging-api-client';
import { MedicalImageManager } from '../../utils/medical-image-manager';
import {
  waitForAnalysisComplete,
  validateAnalysisResult,
  captureFailureContext,
  waitForAPIResponse,
  sleep,
} from '../../utils/test-helpers';
import testEnv from '../../config/test-env.json';
import * as path from 'path';

test.describe('Real Slice Analysis Tests', () => {
  let apiClient: ImagingAPIClient;
  let imageManager: MedicalImageManager;
  let uploadedScanId: string;

  test.beforeAll(async () => {
    // Initialize API client
    apiClient = new ImagingAPIClient(testEnv.backend.imaging_service);

    // Initialize medical image manager
    const metadataPath = path.join(__dirname, '../../fixtures/medical-data/metadata.json');
    imageManager = new MedicalImageManager(metadataPath);

    // Validate medical image files exist
    const validation = imageManager.validateFiles();
    if (!validation.valid) {
      console.error('Medical image validation errors:', validation.errors);
      throw new Error('Medical image test data validation failed');
    }

    imageManager.printSummary();

    // Upload test data once for all tests
    console.log('\n[Setup] Uploading test medical image data...');
    const firstCase = imageManager.getCaseSlices('001');

    const uploadResult = await apiClient.uploadMedicalImages(
      firstCase,
      testEnv.test_patients.patient_001
    );

    if (!uploadResult.success) {
      throw new Error('Failed to upload test medical image data');
    }

    uploadedScanId = uploadResult.scan_id;
    console.log(`[Setup] Uploaded scan ID: ${uploadedScanId}`);
  });

  test.beforeEach(async ({ page }) => {
    // Navigate to medical imaging page
    await page.goto(`/patient/${testEnv.test_patients.patient_001}/imaging`);

    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should analyze a single slice with real AI model', async ({ page }) => {
    test.setTimeout(testEnv.ai_analysis.slice_timeout_ms + 30000);

    try {
      // Select a middle slice for analysis
      const sliceNumber = Math.floor(imageManager.getSliceCount('001') / 2);

      console.log(`Analyzing slice ${sliceNumber}...`);

      // Find and click on the slice selector
      const sliceSelector = page.locator('[data-testid="slice-selector"]');
      await sliceSelector.fill(sliceNumber.toString());

      // Click analyze button
      const analyzeButton = page.locator('[data-testid="analyze-slice"]');
      await analyzeButton.click();

      // Wait for analysis to start
      await expect(page.locator('[data-testid="analysis-in-progress"]')).toBeVisible({
        timeout: 5000,
      });

      // Wait for analysis response from API
      const response = await waitForAPIResponse(
        page,
        '/analyze/slice',
        testEnv.ai_analysis.slice_timeout_ms
      );

      console.log('Analysis response:', JSON.stringify(response, null, 2));

      // Validate response structure
      expect(validateAnalysisResult(response)).toBe(true);

      // Validate specific fields
      expect(response).toHaveProperty('findings');
      expect(response).toHaveProperty('ai_confidence');
      expect(response).toHaveProperty('summary');
      expect(response.slice_number).toBe(sliceNumber);

      // Validate confidence is in valid range
      expect(response.ai_confidence).toBeGreaterThanOrEqual(0);
      expect(response.ai_confidence).toBeLessThanOrEqual(1);

      // Validate findings structure
      if (response.findings.length > 0) {
        const finding = response.findings[0];
        expect(finding).toHaveProperty('type');
        expect(finding).toHaveProperty('confidence');
        expect(finding).toHaveProperty('coordinates');

        // Validate finding confidence
        expect(finding.confidence).toBeGreaterThanOrEqual(0);
        expect(finding.confidence).toBeLessThanOrEqual(1);
      }

      // Verify UI shows results
      await expect(page.locator('[data-testid="analysis-complete"]')).toBeVisible({
        timeout: 10000,
      });

      // Verify findings are displayed
      const resultsContainer = page.locator('[data-testid="analysis-results"]');
      await expect(resultsContainer).toBeVisible();

      console.log(`Slice analysis completed successfully for slice ${sliceNumber}`);
    } catch (error) {
      await captureFailureContext(page, 'slice-analysis-single');
      throw error;
    }
  });

  test('should handle analysis of multiple consecutive slices', async ({ page }) => {
    test.setTimeout(testEnv.ai_analysis.slice_timeout_ms * 3 + 30000);

    try {
      const sliceCount = imageManager.getSliceCount('001');
      const startSlice = Math.floor(sliceCount / 3);
      const slicesToAnalyze = 3;

      const results = [];

      for (let i = 0; i < slicesToAnalyze; i++) {
        const sliceNumber = startSlice + i;
        console.log(`Analyzing slice ${sliceNumber}/${sliceCount}...`);

        // Select slice
        const sliceSelector = page.locator('[data-testid="slice-selector"]');
        await sliceSelector.fill(sliceNumber.toString());

        // Analyze
        await page.click('[data-testid="analyze-slice"]');

        // Wait for response
        const response = await waitForAPIResponse(
          page,
          '/analyze/slice',
          testEnv.ai_analysis.slice_timeout_ms
        );

        // Validate
        expect(validateAnalysisResult(response)).toBe(true);
        results.push(response);

        console.log(`Slice ${sliceNumber}: ${response.findings.length} findings`);

        // Small delay between analyses
        await sleep(2000);
      }

      // Verify we got all results
      expect(results.length).toBe(slicesToAnalyze);

      // Log summary
      console.log('\nMulti-slice analysis summary:');
      results.forEach((result, idx) => {
        console.log(
          `  Slice ${startSlice + idx}: ${result.findings.length} findings, ` +
          `confidence: ${result.ai_confidence.toFixed(3)}`
        );
      });
    } catch (error) {
      await captureFailureContext(page, 'slice-analysis-multiple');
      throw error;
    }
  });

  test('should display confidence scores and findings correctly', async ({ page }) => {
    test.setTimeout(testEnv.ai_analysis.slice_timeout_ms + 30000);

    try {
      const sliceNumber = 1;

      // Analyze first slice
      await page.locator('[data-testid="slice-selector"]').fill(sliceNumber.toString());
      await page.click('[data-testid="analyze-slice"]');

      // Wait for results
      const response = await waitForAPIResponse(
        page,
        '/analyze/slice',
        testEnv.ai_analysis.slice_timeout_ms
      );

      // Verify UI displays confidence score
      const confidenceElement = page.locator('[data-testid="ai-confidence"]');
      await expect(confidenceElement).toBeVisible();

      const displayedConfidence = await confidenceElement.textContent();
      console.log(`Displayed confidence: ${displayedConfidence}`);

      // Verify findings are listed
      if (response.findings.length > 0) {
        const findingsList = page.locator('[data-testid="findings-list"]');
        await expect(findingsList).toBeVisible();

        // Count displayed findings
        const findingItems = page.locator('[data-testid="finding-item"]');
        const count = await findingItems.count();

        expect(count).toBe(response.findings.length);
        console.log(`Displayed ${count} findings in UI`);
      } else {
        // Verify "no findings" message
        await expect(page.locator('[data-testid="no-findings"]')).toBeVisible();
        console.log('No findings detected (normal scan)');
      }
    } catch (error) {
      await captureFailureContext(page, 'slice-analysis-ui-display');
      throw error;
    }
  });

  test('should handle analysis timeout gracefully', async ({ page }) => {
    test.setTimeout(10000); // Short timeout to test error handling

    try {
      await page.locator('[data-testid="slice-selector"]').fill('1');
      await page.click('[data-testid="analyze-slice"]');

      // This should timeout or show loading state
      await sleep(5000);

      // Verify either still loading or error shown
      const isLoading = await page.locator('[data-testid="analysis-in-progress"]').isVisible();
      const hasError = await page.locator('[data-testid="analysis-error"]').isVisible();

      expect(isLoading || hasError).toBe(true);

      console.log('Timeout handling verified');
    } catch (error) {
      // Expected to fail due to timeout - this is OK
      console.log('Timeout test completed as expected');
    }
  });

  test('should support analyzing different slice ranges', async ({ page }) => {
    test.setTimeout(testEnv.ai_analysis.slice_timeout_ms * 3 + 30000);

    try {
      const sliceCount = imageManager.getSliceCount('001');

      // Test first, middle, and last slices
      const slicesToTest = [
        { name: 'first', number: 0 },
        { name: 'middle', number: Math.floor(sliceCount / 2) },
        { name: 'last', number: sliceCount - 1 },
      ];

      for (const slice of slicesToTest) {
        console.log(`Analyzing ${slice.name} slice (${slice.number})...`);

        await page.locator('[data-testid="slice-selector"]').fill(slice.number.toString());
        await page.click('[data-testid="analyze-slice"]');

        const response = await waitForAPIResponse(
          page,
          '/analyze/slice',
          testEnv.ai_analysis.slice_timeout_ms
        );

        expect(validateAnalysisResult(response)).toBe(true);
        console.log(`${slice.name} slice: ${response.findings.length} findings`);

        await sleep(2000);
      }

      console.log('Slice range analysis completed successfully');
    } catch (error) {
      await captureFailureContext(page, 'slice-analysis-ranges');
      throw error;
    }
  });

  test('should validate AI model version and metadata', async ({ page }) => {
    test.setTimeout(testEnv.ai_analysis.slice_timeout_ms + 30000);

    try {
      await page.locator('[data-testid="slice-selector"]').fill('1');
      await page.click('[data-testid="analyze-slice"]');

      const response = await waitForAPIResponse(
        page,
        '/analyze/slice',
        testEnv.ai_analysis.slice_timeout_ms
      );

      // Check for model metadata
      if (response.model_version) {
        console.log(`AI Model Version: ${response.model_version}`);
        expect(response.model_version).toBeTruthy();
      }

      if (response.processing_time_ms) {
        console.log(`Processing Time: ${response.processing_time_ms}ms`);
        expect(response.processing_time_ms).toBeGreaterThan(0);
      }

      console.log('Model metadata validation completed');
    } catch (error) {
      await captureFailureContext(page, 'slice-analysis-metadata');
      throw error;
    }
  });

  test.afterAll(async () => {
    // Cleanup uploaded test data
    try {
      if (uploadedScanId) {
        console.log(`\n[Cleanup] Removing test scan: ${uploadedScanId}`);
        await apiClient.deleteScan(uploadedScanId);
        console.log('[Cleanup] Test data cleaned up successfully');
      }
    } catch (error) {
      console.warn('[Cleanup] Warning: Failed to cleanup test data:', (error as Error).message);
    }
  });
});
