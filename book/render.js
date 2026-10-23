// Renders an HTML file to PDF with Chromium (Playwright), honoring CSS @page sizes.
// Pages may set window.__bookReady = false while a script lays them out; rendering waits
// until it turns true. Usage: node render.js input.html output.pdf
const path = require('path');

function loadPlaywright() {
  try { return require('playwright'); } catch (_) {}
  return require('/opt/node-tools/node_modules/playwright');
}

(async () => {
  const [input, output] = process.argv.slice(2);
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.emulateMedia({ media: 'print' });  // lay out exactly as it will print
  await page.goto('file://' + path.resolve(input), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => window.__bookReady !== false, null, { timeout: 120000 });
  await page.pdf({ path: output, preferCSSPageSize: true, printBackground: true });
  await browser.close();
})();
