/**
 * UI Interaction E2E Tests
 * Tests user interface interactions and navigation
 */

import { test, expect } from '@playwright/test';

test.describe('Login and Authentication', () => {
  test.setTimeout(60000);

  test('should display login page', async ({ page }) => {
    console.log('[Test] Navigating to login page...');

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Take screenshot of login page
    await page.screenshot({ path: 'tests/test-results/screenshots/01-login-page.png', fullPage: true });

    console.log('[Test] Login page loaded and screenshot saved');
  });

  test('should have login form elements', async ({ page }) => {
    console.log('[Test] Checking login form elements...');

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const pageContent = await page.content();
    console.log('[Test] Page contains:', {
      hasLoginText: pageContent.toLowerCase().includes('login'),
      hasSignInText: pageContent.toLowerCase().includes('sign in'),
      hasInputFields: pageContent.includes('input'),
      hasButtons: pageContent.includes('button'),
    });

    // Check for input fields (email/username and password)
    const inputs = await page.locator('input').count();
    console.log('[Test] Found input fields:', inputs);

    expect(inputs).toBeGreaterThan(0);

    console.log('[Test] Login form elements verified');
  });

  test('should attempt test login', async ({ page }) => {
    console.log('[Test] Attempting test login...');

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for input fields
    const emailInput = page.locator('input[type="email"], input[type="text"], input[placeholder*="email" i], input[placeholder*="username" i]').first();
    const passwordInput = page.locator('input[type="password"]').first();

    const hasEmailInput = await emailInput.count() > 0;
    const hasPasswordInput = await passwordInput.count() > 0;

    console.log('[Test] Form inputs found:', { email: hasEmailInput, password: hasPasswordInput });

    if (hasEmailInput && hasPasswordInput) {
      // Try filling with test credentials
      await emailInput.fill('test@example.com');
      await passwordInput.fill('testpassword123');

      console.log('[Test] Test credentials entered');

      // Look for submit button
      const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first();

      if (await submitButton.count() > 0) {
        console.log('[Test] Submit button found, clicking...');
        await submitButton.click();

        // Wait a bit to see what happens
        await page.waitForTimeout(2000);

        // Take screenshot of result
        await page.screenshot({ path: 'tests/test-results/screenshots/02-after-login.png', fullPage: true });

        console.log('[Test] Login attempt completed, screenshot saved');
      } else {
        console.log('[Test] Submit button not found');
      }
    }
  });
});

test.describe('Patient List and Navigation', () => {
  test.setTimeout(60000);

  test('should navigate to patient list', async ({ page }) => {
    console.log('[Test] Navigating to patient list...');

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Try to navigate to patients page
    const patientsLink = page.locator('a[href*="patient"], button:has-text("Patient")').first();

    if (await patientsLink.count() > 0) {
      console.log('[Test] Found patients link, clicking...');
      await patientsLink.click();
      await page.waitForTimeout(2000);
    } else {
      // Try direct navigation
      console.log('[Test] Trying direct navigation to /patients...');
      await page.goto('/patients');
      await page.waitForTimeout(1000);
    }

    await page.screenshot({ path: 'tests/test-results/screenshots/03-patient-list.png', fullPage: true });

    console.log('[Test] Patient list page screenshot saved');
  });

  test('should check for patient cards or table', async ({ page }) => {
    console.log('[Test] Checking for patient data display...');

    await page.goto('/patients');
    await page.waitForLoadState('networkidle');

    const pageContent = await page.content();

    const hasPatientElements =
      pageContent.toLowerCase().includes('patient') ||
      pageContent.includes('table') ||
      pageContent.includes('card');

    console.log('[Test] Patient elements found:', hasPatientElements);

    // Check for common patient list elements
    const patientCards = await page.locator('[class*="patient"], [class*="card"]').count();
    const tableRows = await page.locator('table tr, tbody tr').count();

    console.log('[Test] UI elements:', {
      patientCards,
      tableRows,
    });

    console.log('[Test] Patient data display checked');
  });
});

test.describe('Dashboard Navigation', () => {
  test.setTimeout(60000);

  test('should access patient dashboard', async ({ page }) => {
    console.log('[Test] Accessing patient dashboard...');

    // Try different possible routes
    const possibleRoutes = [
      '/patient/test-patient/dashboard',
      '/patient/test-patient',
      '/dashboard',
    ];

    for (const route of possibleRoutes) {
      console.log(`[Test] Trying route: ${route}`);
      await page.goto(route);
      await page.waitForTimeout(1000);

      const url = page.url();
      console.log(`[Test] Current URL: ${url}`);

      if (!url.includes('login') && !url.includes('404')) {
        console.log('[Test] Successfully accessed dashboard route');
        await page.screenshot({
          path: `tests/test-results/screenshots/04-dashboard-${route.replace(/\//g, '-')}.png`,
          fullPage: true
        });
        break;
      }
    }
  });

  test('should check for dashboard tabs', async ({ page }) => {
    console.log('[Test] Checking for dashboard tabs...');

    await page.goto('/patient/test-patient/dashboard');
    await page.waitForLoadState('networkidle');

    const pageContent = await page.content();

    // Check for common tab names
    const tabs = {
      summary: pageContent.toLowerCase().includes('summary'),
      ctAnalysis: pageContent.toLowerCase().includes('ct') && pageContent.toLowerCase().includes('analysis'),
      aiResults: pageContent.toLowerCase().includes('ai') || pageContent.toLowerCase().includes('result'),
      chat: pageContent.toLowerCase().includes('chat'),
    };

    console.log('[Test] Dashboard tabs found:', tabs);

    // Count buttons that might be tabs
    const tabButtons = await page.locator('button[class*="tab"], button[role="tab"]').count();
    console.log('[Test] Tab buttons found:', tabButtons);

    await page.screenshot({ path: 'tests/test-results/screenshots/05-dashboard-tabs.png', fullPage: true });

    console.log('[Test] Dashboard tabs checked');
  });
});

test.describe('CT Analysis Tab Exploration', () => {
  test.setTimeout(90000);

  test('should explore CT Analysis tab', async ({ page }) => {
    console.log('[Test] Exploring CT Analysis tab...');

    await page.goto('/patient/test-patient/dashboard');
    await page.waitForLoadState('networkidle');

    // Try to find and click CT Analysis tab
    const ctTab = page.locator('button:has-text("CT Analysis"), button:has-text("CT"), [role="tab"]:has-text("CT")').first();

    if (await ctTab.count() > 0) {
      console.log('[Test] Found CT Analysis tab, clicking...');
      await ctTab.click();
      await page.waitForTimeout(1000);
    }

    await page.screenshot({ path: 'tests/test-results/screenshots/06-ct-analysis-tab.png', fullPage: true });

    // Look for CT-specific elements
    const pageContent = await page.content();

    const ctElements = {
      hasSliceControls: pageContent.toLowerCase().includes('slice'),
      hasImageViewer: pageContent.includes('img') || pageContent.includes('canvas'),
      hasAnalyzeButton: pageContent.toLowerCase().includes('analyze'),
      hasPlayControls: pageContent.includes('▶') || pageContent.includes('play'),
    };

    console.log('[Test] CT Analysis elements:', ctElements);

    // Check for specific CT controls
    const sliceControls = await page.locator('[class*="slice"], button:has-text("Slice")').count();
    const analyzeButtons = await page.locator('button:has-text("Analyze")').count();

    console.log('[Test] CT Analysis UI elements:', {
      sliceControls,
      analyzeButtons,
    });

    console.log('[Test] CT Analysis tab exploration complete');
  });

  test('should check for image loading area', async ({ page }) => {
    console.log('[Test] Checking for image loading area...');

    await page.goto('/patient/test-patient/dashboard');
    await page.waitForLoadState('networkidle');

    // Navigate to CT tab
    const ctTab = page.locator('button:has-text("CT Analysis"), button:has-text("CT")').first();
    if (await ctTab.count() > 0) {
      await ctTab.click();
      await page.waitForTimeout(1000);
    }

    // Look for image containers
    const images = await page.locator('img').count();
    const canvases = await page.locator('canvas').count();

    console.log('[Test] Image elements found:', { images, canvases });

    // Check for loading or empty states
    const pageContent = await page.content();
    const hasLoadingState =
      pageContent.toLowerCase().includes('loading') ||
      pageContent.toLowerCase().includes('no data') ||
      pageContent.toLowerCase().includes('upload');

    console.log('[Test] Loading/empty state:', hasLoadingState);

    await page.screenshot({ path: 'tests/test-results/screenshots/07-ct-image-area.png', fullPage: true });

    console.log('[Test] Image loading area checked');
  });
});

test.describe('UI Responsiveness', () => {
  test.setTimeout(60000);

  test('should test responsive design', async ({ page }) => {
    console.log('[Test] Testing responsive design...');

    const viewports = [
      { name: 'Desktop', width: 1920, height: 1080 },
      { name: 'Laptop', width: 1366, height: 768 },
      { name: 'Tablet', width: 768, height: 1024 },
      { name: 'Mobile', width: 375, height: 667 },
    ];

    for (const viewport of viewports) {
      console.log(`[Test] Testing ${viewport.name} (${viewport.width}x${viewport.height})...`);

      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      await page.screenshot({
        path: `tests/test-results/screenshots/08-responsive-${viewport.name.toLowerCase()}.png`,
        fullPage: true
      });

      console.log(`[Test] ${viewport.name} screenshot saved`);
    }

    console.log('[Test] Responsive design testing complete');
  });
});

test.describe('Accessibility Checks', () => {
  test.setTimeout(60000);

  test('should check for basic accessibility', async ({ page }) => {
    console.log('[Test] Checking basic accessibility...');

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for alt text on images
    const images = await page.locator('img').all();
    let imagesWithAlt = 0;
    let imagesWithoutAlt = 0;

    for (const img of images) {
      const alt = await img.getAttribute('alt');
      if (alt && alt.trim() !== '') {
        imagesWithAlt++;
      } else {
        imagesWithoutAlt++;
      }
    }

    console.log('[Test] Image accessibility:', {
      total: images.length,
      withAlt: imagesWithAlt,
      withoutAlt: imagesWithoutAlt,
    });

    // Check for form labels
    const inputs = await page.locator('input').all();
    let inputsWithLabels = 0;

    for (const input of inputs) {
      const id = await input.getAttribute('id');
      if (id) {
        const label = await page.locator(`label[for="${id}"]`).count();
        if (label > 0) {
          inputsWithLabels++;
        }
      }
    }

    console.log('[Test] Form accessibility:', {
      totalInputs: inputs.length,
      withLabels: inputsWithLabels,
    });

    // Check for heading hierarchy
    const h1Count = await page.locator('h1').count();
    const h2Count = await page.locator('h2').count();
    const h3Count = await page.locator('h3').count();

    console.log('[Test] Heading structure:', {
      h1: h1Count,
      h2: h2Count,
      h3: h3Count,
    });

    console.log('[Test] Basic accessibility checks complete');
  });
});

test.describe('Navigation Flow', () => {
  test.setTimeout(90000);

  test('should test complete navigation flow', async ({ page }) => {
    console.log('[Test] Testing complete navigation flow...');

    const steps = [
      { name: 'Homepage', url: '/' },
      { name: 'Patients', url: '/patients' },
      { name: 'Dashboard', url: '/patient/test-patient/dashboard' },
    ];

    for (const step of steps) {
      console.log(`[Test] Step: ${step.name}`);
      await page.goto(step.url);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      await page.screenshot({
        path: `tests/test-results/screenshots/09-flow-${step.name.toLowerCase()}.png`,
        fullPage: true
      });

      console.log(`[Test] ${step.name} step completed`);
    }

    console.log('[Test] Complete navigation flow tested');
  });
});
