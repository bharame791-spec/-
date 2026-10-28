// Renders the logofolio boards: fits every .logo group into its cell, saves PNG + a fitted SVG.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, 'out3');
const fontsCss = fs.readFileSync(path.join(__dirname, 'fonts', 'fonts.css'), 'utf8')
  .replace(/url\(([^)]+\.ttf)\)/g, (m, f) => `url(file://${path.join(__dirname, 'fonts', f)})`);
(async () => {
  const browser = await chromium.launch();
  for (const f of fs.readdirSync(dir).filter(f => /^logofolio-\w+\.svg$/.test(f))) {
    const svg = fs.readFileSync(path.join(dir, f), 'utf8');
    const [, w, h] = svg.match(/viewBox="0 0 (\d+) (\d+)"/);
    const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 2 });
    const html = path.join(dir, '_tmp.html');
    fs.writeFileSync(html, `<!doctype html><meta charset="utf-8"><style>${fontsCss}body{margin:0}</style>${svg}`);
    await page.goto('file://' + html);
    await page.evaluate(() => document.fonts.ready);
    const fitted = await page.evaluate(() => {
      for (const g of document.querySelectorAll('g.logo')) {
        const b = g.getBBox(), d = g.dataset;
        const k = Math.min(d.w / b.width, d.h / b.height);
        const tx = d.x - (b.x + b.width / 2) * k, ty = d.y - (b.y + b.height / 2) * k;
        g.setAttribute('transform', `translate(${tx.toFixed(2)} ${ty.toFixed(2)}) scale(${k.toFixed(4)})`);
      }
      return document.querySelector('svg').outerHTML;
    });
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(dir, f.replace('.svg', '.png')) });
    fs.writeFileSync(path.join(dir, f.replace('.svg', '-fitted.svg')), fitted);
    fs.unlinkSync(html);
    await page.close();
  }
  await browser.close();
})();
