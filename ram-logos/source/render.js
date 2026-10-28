const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, 'out');
const fontsCss = fs.readFileSync(path.join(__dirname, 'fonts', 'fonts.css'), 'utf8')
  .replace(/url\(([^)]+\.ttf)\)/g, (m, f) => `url(file://${path.join(__dirname, 'fonts', f)})`);
const only = process.argv[2];
(async () => {
  const browser = await chromium.launch();
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.svg') && (!only || f.includes(only)))) {
    const svg = fs.readFileSync(path.join(dir, f), 'utf8');
    const [, w, h] = svg.match(/viewBox="0 0 (\d+) (\d+)"/);
    const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 2 });
    const html = path.join(dir, f.replace('.svg', '.html'));
    fs.writeFileSync(html, `<!doctype html><meta charset="utf-8"><style>${fontsCss}body{margin:0}</style>${svg}`);
    await page.goto('file://' + html);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(dir, f.replace('.svg', '.png')) });
    fs.unlinkSync(html);
    await page.close();
  }
  await browser.close();
})();
