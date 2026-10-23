// Optional browser QA: requires Playwright and its Chromium runtime.
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.BROWSER_CHANNEL ? { channel: process.env.BROWSER_CHANNEL } : {}) });
  const page = await browser.newPage({ viewport: { width: 1200, height: 1000 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(process.argv[2] || 'http://127.0.0.1:8768/review.html');
  await page.getByText('1 / 200', { exact: true }).waitFor();
  await page.locator('#left').fill('QA-only unsaved probe');
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await page.getByText('2 / 200', { exact: true }).waitFor();
  await page.getByRole('button', { name: 'Previous', exact: true }).click();
  if (await page.locator('#left').inputValue() !== 'QA-only unsaved probe') throw Error('Navigation lost annotation');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export all work', exact: true }).click();
  const download = await downloadPromise;
  if (download.suggestedFilename() !== 'boundary_review_progress.jsonl') throw Error('Export failed');
  await page.screenshot({ path: 'runs/review-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  if (overflow) throw Error('Mobile horizontal overflow');
  await page.screenshot({ path: 'runs/review-mobile.png', fullPage: true });
  if (errors.length) throw Error(errors.join('\n'));
  await browser.close();
  console.log('Desktop/mobile navigation, annotation retention, export and console checks passed.');
})().catch(error => { console.error(error); process.exit(1); });
