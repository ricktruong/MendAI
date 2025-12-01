/**
 * Test Helper Functions
 * Common utilities for E2E tests
 */

import { Page, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { SliceAnalysisResult, BatchAnalysisResult } from './imaging-api-client';

/**
 * Wait for analysis to complete in the UI
 */
export async function waitForAnalysisComplete(
  page: Page,
  timeout: number = 60000
): Promise<void> {
  await page.waitForSelector('[data-testid="analysis-complete"]', {
    timeout,
    state: 'visible',
  });
}

/**
 * Wait for element to be visible
 */
export async function waitForElement(
  page: Page,
  selector: string,
  timeout: number = 30000
): Promise<void> {
  await page.waitForSelector(selector, {
    timeout,
    state: 'visible',
  });
}

/**
 * Validate slice analysis result structure
 */
export function validateAnalysisResult(result: any): boolean {
  if (!result || typeof result !== 'object') {
    return false;
  }

  // Required fields
  if (!result.hasOwnProperty('findings')) return false;
  if (!result.hasOwnProperty('ai_confidence')) return false;

  // Validate confidence range
  if (
    typeof result.ai_confidence !== 'number' ||
    result.ai_confidence < 0 ||
    result.ai_confidence > 1
  ) {
    return false;
  }

  // Validate findings array
  if (!Array.isArray(result.findings)) {
    return false;
  }

  // Validate each finding
  for (const finding of result.findings) {
    if (!finding.type || !finding.confidence) {
      return false;
    }

    if (
      typeof finding.confidence !== 'number' ||
      finding.confidence < 0 ||
      finding.confidence > 1
    ) {
      return false;
    }
  }

  return true;
}

/**
 * Validate batch analysis result structure
 */
export function validateBatchAnalysisResult(result: any): boolean {
  if (!result || typeof result !== 'object') {
    return false;
  }

  // Required fields
  if (!result.hasOwnProperty('overall_summary')) return false;
  if (!result.hasOwnProperty('total_slices')) return false;
  if (!result.hasOwnProperty('analyzed_slices')) return false;

  // Validate overall summary
  const summary = result.overall_summary;
  if (!summary || typeof summary !== 'object') {
    return false;
  }

  if (
    !summary.hasOwnProperty('total_findings') ||
    !summary.hasOwnProperty('diagnosis')
  ) {
    return false;
  }

  return true;
}

/**
 * Compare two analysis results for similarity
 */
export function compareAnalysisResults(
  result1: SliceAnalysisResult,
  result2: SliceAnalysisResult
): { similarity: number; differences: string[] } {
  const differences: string[] = [];
  let similarityScore = 0;
  let totalChecks = 0;

  // Compare findings count
  totalChecks++;
  const findingsDiff = Math.abs(result1.findings.length - result2.findings.length);
  if (findingsDiff === 0) {
    similarityScore++;
  } else {
    differences.push(
      `Different findings count: ${result1.findings.length} vs ${result2.findings.length}`
    );
  }

  // Compare confidence scores
  totalChecks++;
  const confidenceDiff = Math.abs(result1.ai_confidence - result2.ai_confidence);
  if (confidenceDiff < 0.1) {
    similarityScore++;
  } else {
    differences.push(
      `Different confidence: ${result1.ai_confidence} vs ${result2.ai_confidence}`
    );
  }

  // Compare finding types
  const types1 = new Set(result1.findings.map((f) => f.type));
  const types2 = new Set(result2.findings.map((f) => f.type));
  const commonTypes = new Set([...types1].filter((t) => types2.has(t)));

  totalChecks++;
  if (commonTypes.size === types1.size && commonTypes.size === types2.size) {
    similarityScore++;
  } else {
    differences.push('Different finding types');
  }

  return {
    similarity: similarityScore / totalChecks,
    differences,
  };
}

/**
 * Capture failure context (screenshot + logs)
 */
export async function captureFailureContext(
  page: Page,
  testName: string,
  outputDir: string = './tests/test-results/failures'
): Promise<void> {
  const timestamp = new Date().toISOString().replace(/:/g, '-').replace(/\./g, '-');
  const sanitizedTestName = testName.replace(/[^a-zA-Z0-9]/g, '_');
  const baseFilename = `${sanitizedTestName}-${timestamp}`;

  // Ensure output directory exists
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Capture screenshot
  const screenshotPath = path.join(outputDir, `${baseFilename}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`Screenshot saved: ${screenshotPath}`);

  // Capture console logs
  const logs = await page.evaluate(() => {
    return (window as any).testLogs || [];
  });

  const logsPath = path.join(outputDir, `${baseFilename}-logs.json`);
  fs.writeFileSync(logsPath, JSON.stringify(logs, null, 2));
  console.log(`Logs saved: ${logsPath}`);

  // Capture page HTML
  const htmlPath = path.join(outputDir, `${baseFilename}.html`);
  const html = await page.content();
  fs.writeFileSync(htmlPath, html);
  console.log(`HTML saved: ${htmlPath}`);
}

/**
 * Wait for API response
 */
export async function waitForAPIResponse(
  page: Page,
  urlPattern: string | RegExp,
  timeout: number = 60000
): Promise<any> {
  const response = await page.waitForResponse(
    (res) => {
      const url = res.url();
      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern) && res.ok();
      } else {
        return urlPattern.test(url) && res.ok();
      }
    },
    { timeout }
  );

  return await response.json();
}

/**
 * Wait with custom condition
 */
export async function waitForCondition(
  condition: () => Promise<boolean> | boolean,
  options: {
    timeout?: number;
    interval?: number;
    errorMessage?: string;
  } = {}
): Promise<void> {
  const { timeout = 30000, interval = 1000, errorMessage = 'Condition not met' } = options;

  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    if (await condition()) {
      return;
    }
    await sleep(interval);
  }

  throw new Error(`${errorMessage} (timeout: ${timeout}ms)`);
}

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry an operation
 */
export async function retry<T>(
  operation: () => Promise<T>,
  options: {
    maxRetries?: number;
    delay?: number;
    onRetry?: (attempt: number, error: any) => void;
  } = {}
): Promise<T> {
  const { maxRetries = 3, delay = 1000, onRetry } = options;

  let lastError: any;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;

      if (attempt < maxRetries - 1) {
        if (onRetry) {
          onRetry(attempt + 1, error);
        }
        await sleep(delay);
      }
    }
  }

  throw lastError;
}

/**
 * Generate random test patient ID
 */
export function generateTestPatientId(): string {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 1000);
  return `E2E-TEST-${timestamp}-${random}`;
}

/**
 * Clean up test data via API
 */
export async function cleanupTestData(
  apiClient: any,
  scanId: string
): Promise<void> {
  try {
    await apiClient.deleteScan(scanId);
    console.log(`Cleaned up scan: ${scanId}`);
  } catch (error) {
    console.warn(`Failed to cleanup scan ${scanId}:`, (error as Error).message);
  }
}

/**
 * Format file size
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

/**
 * Format duration
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
  return `${(ms / 60000).toFixed(2)}m`;
}

/**
 * Assert element is visible
 */
export async function assertVisible(page: Page, selector: string): Promise<void> {
  await expect(page.locator(selector)).toBeVisible();
}

/**
 * Assert element contains text
 */
export async function assertText(
  page: Page,
  selector: string,
  text: string
): Promise<void> {
  await expect(page.locator(selector)).toContainText(text);
}

/**
 * Click and wait for navigation
 */
export async function clickAndNavigate(
  page: Page,
  selector: string
): Promise<void> {
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }),
    page.click(selector),
  ]);
}

/**
 * Upload file via file input
 */
export async function uploadFile(
  page: Page,
  inputSelector: string,
  filePath: string
): Promise<void> {
  const fileInput = await page.locator(inputSelector);
  await fileInput.setInputFiles(filePath);
}

/**
 * Upload multiple files
 */
export async function uploadFiles(
  page: Page,
  inputSelector: string,
  filePaths: string[]
): Promise<void> {
  const fileInput = await page.locator(inputSelector);
  await fileInput.setInputFiles(filePaths);
}
