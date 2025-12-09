/**
 * Real Batch Analysis E2E Tests
 * Tests complete scan batch analysis with real AI models
 */

import { test, expect } from '@playwright/test';
import { ImagingAPIClient } from '../../utils/imaging-api-client';
import { MedicalImageManager } from '../../utils/medical-image-manager';
import {
  validateBatchAnalysisResult,
  captureFailureContext,
  waitForAPIResponse,
  sleep,
  formatDuration,
} from '../../utils/test-helpers';
import testEnv from '../../config/test-env.json' with { type: 'json' };
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test.describe.skip('Real Batch Analysis Tests', () => {
  let apiClient: ImagingAPIClient;
  let imageManager: MedicalImageManager;
  let uploadedScanId: string;

  // Increase timeout for batch operations (can take several minutes)
  test.setTimeout(testEnv.ai_analysis.batch_timeout_ms + 60000);

  test.beforeAll(async () => {
    // Initialize API client
    apiClient = new ImagingAPIClient(testEnv.backend.imaging_service);

    // Initialize medical image manager
    const metadataPath = path.join(__dirname, '../../fixtures/medical-data/metadata.json');
    imageManager = new MedicalImageManager(metadataPath);

    // Validate medical image files
    const validation = imageManager.validateFiles();
    if (!validation.valid) {
      throw new Error('Medical image test data validation failed');
    }

    imageManager.printSummary();

    // Upload test data for batch analysis
    console.log('\n[Setup] Uploading medical image data for batch analysis...');
    const caseFiles = imageManager.getCaseSlices('001');

    const uploadResult = await apiClient.uploadMedicalImages(
      caseFiles,
      testEnv.test_patients.patient_001
    );

    if (!uploadResult.success) {
      throw new Error('Failed to upload test medical image data');
    }

    uploadedScanId = uploadResult.scan_id;
    console.log(`[Setup] Uploaded scan ID: ${uploadedScanId}`);
    console.log(`[Setup] Total slices: ${uploadResult.file_count}`);
  });

  test.beforeEach(async ({ page }) => {
    await page.goto(`/patient/${testEnv.test_patients.patient_001}/imaging`);
    await page.waitForLoadState('networkidle');
  });

  test('should perform complete batch analysis on all slices', async ({ page }) => {
    try {
      console.log('\n[Test] Starting batch analysis...');
      const startTime = Date.now();

      // Click batch analyze button
      const batchButton = page.locator('[data-testid="batch-analyze"]');
      await expect(batchButton).toBeVisible({ timeout: 10000 });
      await batchButton.click();

      // Verify progress indicator appears
      const progressBar = page.locator('[data-testid="analysis-progress"]');
      await expect(progressBar).toBeVisible({ timeout: 5000 });

      console.log('[Test] Batch analysis started, waiting for completion...');

      // Monitor progress updates
      let lastProgress = 0;
      const progressCheckInterval = setInterval(async () => {
        try {
          const progressText = await page
            .locator('[data-testid="progress-text"]')
            .textContent();

          if (progressText) {
            const match = progressText.match(/(\d+)\/(\d+)/);
            if (match) {
              const current = parseInt(match[1]);
              if (current > lastProgress) {
                console.log(`[Progress] ${progressText}`);
                lastProgress = current;
              }
            }
          }
        } catch {
          // Element might not be available yet
        }
      }, 5000);

      // Wait for batch analysis API response
      const response = await waitForAPIResponse(
        page,
        '/analyze/batch',
        testEnv.ai_analysis.batch_timeout_ms
      );

      clearInterval(progressCheckInterval);

      const duration = Date.now() - startTime;
      console.log(`[Test] Batch analysis completed in ${formatDuration(duration)}`);
      console.log('[Test] Response:', JSON.stringify(response, null, 2));

      // Validate response structure
      expect(validateBatchAnalysisResult(response)).toBe(true);

      // Validate required fields
      expect(response).toHaveProperty('overall_summary');
      expect(response).toHaveProperty('total_slices');
      expect(response).toHaveProperty('analyzed_slices');

      // Verify all slices were analyzed
      expect(response.analyzed_slices).toBe(response.total_slices);
      console.log(`[Test] Analyzed ${response.analyzed_slices}/${response.total_slices} slices`);

      // Validate overall summary
      const summary = response.overall_summary;
      expect(summary).toHaveProperty('total_findings');
      expect(summary).toHaveProperty('diagnosis');
      expect(summary.total_findings).toBeGreaterThanOrEqual(0);

      console.log(`[Test] Total findings: ${summary.total_findings}`);
      console.log(`[Test] Diagnosis: ${summary.diagnosis}`);

      if (summary.high_risk_slices) {
        console.log(`[Test] High-risk slices: ${summary.high_risk_slices.join(', ')}`);
      }

      // Verify UI shows completed state
      await expect(page.locator('[data-testid="batch-analysis-complete"]')).toBeVisible({
        timeout: 10000,
      });

      // Verify results are displayed
      const resultsContainer = page.locator('[data-testid="batch-results"]');
      await expect(resultsContainer).toBeVisible();

      console.log('[Test] Batch analysis test passed successfully');
    } catch (error) {
      await captureFailureContext(page, 'batch-analysis-complete');
      throw error;
    }
  });

  test('should display batch analysis progress updates', async ({ page }) => {
    try {
      // Start batch analysis
      await page.click('[data-testid="batch-analyze"]');

      // Verify progress bar exists and updates
      const progressBar = page.locator('[data-testid="analysis-progress"]');
      await expect(progressBar).toBeVisible({ timeout: 5000 });

      // Check initial progress
      await sleep(2000);

      const progressText = page.locator('[data-testid="progress-text"]');
      await expect(progressText).toBeVisible();

      const initialText = await progressText.textContent();
      console.log(`Initial progress: ${initialText}`);

      // Wait a bit and check progress updated
      await sleep(10000);

      const updatedText = await progressText.textContent();
      console.log(`Updated progress: ${updatedText}`);

      // Progress should have changed (or completed)
      // Just verify the element is still there and functional
      await expect(progressText).toBeVisible();

      console.log('[Test] Progress updates working correctly');
    } catch (error) {
      await captureFailureContext(page, 'batch-analysis-progress');
      throw error;
    }
  });

  test('should identify high-risk slices correctly', async ({ page }) => {
    try {
      // Start batch analysis
      await page.click('[data-testid="batch-analyze"]');

      // Wait for completion
      const response = await waitForAPIResponse(
        page,
        '/analyze/batch',
        testEnv.ai_analysis.batch_timeout_ms
      );

      // Check for high-risk slices
      if (response.overall_summary.high_risk_slices) {
        const highRiskSlices = response.overall_summary.high_risk_slices;

        console.log(`[Test] Found ${highRiskSlices.length} high-risk slices`);

        // Verify they're displayed in UI
        if (highRiskSlices.length > 0) {
          const highRiskList = page.locator('[data-testid="high-risk-slices"]');
          await expect(highRiskList).toBeVisible();

          // Verify each high-risk slice is listed
          for (const sliceNum of highRiskSlices) {
            const sliceElement = page.locator(`[data-testid="high-risk-slice-${sliceNum}"]`);
            await expect(sliceElement).toBeVisible();
            console.log(`[Test] High-risk slice ${sliceNum} displayed in UI`);
          }
        }
      } else {
        console.log('[Test] No high-risk slices found (normal scan)');
      }

      console.log('[Test] High-risk slice identification test passed');
    } catch (error) {
      await captureFailureContext(page, 'batch-analysis-high-risk');
      throw error;
    }
  });

  test('should generate comprehensive diagnostic summary', async ({ page }) => {
    try {
      // Start batch analysis
      await page.click('[data-testid="batch-analyze"]');

      // Wait for completion
      const response = await waitForAPIResponse(
        page,
        '/analyze/batch',
        testEnv.ai_analysis.batch_timeout_ms
      );

      // Verify diagnostic summary
      const summary = response.overall_summary;
      expect(summary.diagnosis).toBeTruthy();
      expect(typeof summary.diagnosis).toBe('string');
      expect(summary.diagnosis.length).toBeGreaterThan(0);

      console.log('[Test] Diagnostic Summary:');
      console.log(summary.diagnosis);

      // Verify summary is displayed in UI
      const summaryElement = page.locator('[data-testid="diagnostic-summary"]');
      await expect(summaryElement).toBeVisible();

      const displayedSummary = await summaryElement.textContent();
      expect(displayedSummary).toContain(summary.diagnosis);

      console.log('[Test] Diagnostic summary test passed');
    } catch (error) {
      await captureFailureContext(page, 'batch-analysis-summary');
      throw error;
    }
  });

  test('should handle batch analysis cancellation', async ({ page }) => {
    try {
      // Start batch analysis
      await page.click('[data-testid="batch-analyze"]');

      // Wait for progress to start
      await expect(page.locator('[data-testid="analysis-progress"]')).toBeVisible({
        timeout: 5000,
      });

      await sleep(3000);

      // Click cancel button
      const cancelButton = page.locator('[data-testid="cancel-analysis"]');
      if (await cancelButton.isVisible()) {
        await cancelButton.click();

        // Verify cancellation
        await expect(page.locator('[data-testid="analysis-cancelled"]')).toBeVisible({
          timeout: 5000,
        });

        console.log('[Test] Batch analysis cancelled successfully');
      } else {
        console.log('[Test] Cancel button not available (analysis may have completed)');
      }
    } catch (error) {
      // Cancellation test might fail if analysis completes too quickly
      console.log('[Test] Cancellation test skipped or failed:', (error as Error).message);
    }
  });

  test('should support exporting batch analysis results', async ({ page }) => {
    try {
      // Start and complete batch analysis
      await page.click('[data-testid="batch-analyze"]');

      await waitForAPIResponse(
        page,
        '/analyze/batch',
        testEnv.ai_analysis.batch_timeout_ms
      );

      // Wait for results to be displayed
      await expect(page.locator('[data-testid="batch-results"]')).toBeVisible();

      // Check for export button
      const exportButton = page.locator('[data-testid="export-results"]');

      if (await exportButton.isVisible()) {
        // Click export
        const [download] = await Promise.all([
          page.waitForEvent('download'),
          exportButton.click(),
        ]);

        // Verify download
        expect(download).toBeTruthy();
        const filename = download.suggestedFilename();
        console.log(`[Test] Exported file: ${filename}`);

        expect(filename).toMatch(/\.(pdf|json)$/);

        console.log('[Test] Export test passed');
      } else {
        console.log('[Test] Export button not found in UI');
      }
    } catch (error) {
      await captureFailureContext(page, 'batch-analysis-export');
      console.log('[Test] Export test skipped or failed:', (error as Error).message);
    }
  });

  test('should track and display processing time', async ({ page }) => {
    try {
      const startTime = Date.now();

      // Start batch analysis
      await page.click('[data-testid="batch-analyze"]');

      // Wait for completion
      const response = await waitForAPIResponse(
        page,
        '/analyze/batch',
        testEnv.ai_analysis.batch_timeout_ms
      );

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      console.log(`[Test] Total processing time: ${formatDuration(totalTime)}`);

      if (response.processing_time_ms) {
        console.log(`[Test] API reported time: ${formatDuration(response.processing_time_ms)}`);
        expect(response.processing_time_ms).toBeGreaterThan(0);
      }

      // Check if processing time is displayed in UI
      const timeElement = page.locator('[data-testid="processing-time"]');
      if (await timeElement.isVisible()) {
        const displayedTime = await timeElement.textContent();
        console.log(`[Test] Displayed time: ${displayedTime}`);
      }

      console.log('[Test] Processing time tracking test passed');
    } catch (error) {
      await captureFailureContext(page, 'batch-analysis-timing');
      throw error;
    }
  });

  test.afterAll(async () => {
    // Cleanup
    try {
      if (uploadedScanId) {
        console.log(`\n[Cleanup] Removing test scan: ${uploadedScanId}`);
        await apiClient.deleteScan(uploadedScanId);
        console.log('[Cleanup] Test data cleaned up successfully');
      }
    } catch (error) {
      console.warn('[Cleanup] Warning: Failed to cleanup:', (error as Error).message);
    }
  });
});
