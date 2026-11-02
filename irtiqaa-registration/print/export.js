// Exports the A5 poster: trim PDF, bleed PDF (3mm), and a 300dpi PNG.
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const file = 'file://' + path.resolve(__dirname, 'a5.html');
  for (const bleed of [0, 1]) {
    const p = await b.newPage();
    await p.goto(file + (bleed ? '?bleed=1' : ''));
    await p.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
    await p.pdf({ path: path.join(__dirname, bleed ? 'irtiqaa-A5-bleed3mm.pdf' : 'irtiqaa-A5.pdf'), preferCSSPageSize: true, printBackground: true });
    await p.close();
  }
  const mm = 96 / 25.4;
  const p = await b.newPage({ viewport: { width: Math.round(148 * mm), height: Math.round(210 * mm) }, deviceScaleFactor: 300 / 96 });
  await p.goto(file);
  await p.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
  await p.screenshot({ path: path.join(__dirname, 'irtiqaa-A5-300dpi.png'), clip: { x: 0, y: 0, width: 148 * mm, height: 210 * mm } });
  await b.close();
})();

// A4 = the same design scaled ×√2 (A-series sizes share proportions)
(async () => {
  const b = await chromium.launch();
  const file = 'file://' + path.resolve(__dirname, 'a5.html') + '?a4=1';
  const p = await b.newPage();
  await p.goto(file);
  await p.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
  await p.pdf({ path: path.join(__dirname, 'irtiqaa-A4.pdf'), preferCSSPageSize: true, printBackground: true });
  const mm = 96 / 25.4;
  const q = await b.newPage({ viewport: { width: Math.round(210 * mm), height: Math.round(297 * mm) }, deviceScaleFactor: 300 / 96 });
  await q.goto(file);
  await q.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
  await q.screenshot({ path: path.join(__dirname, 'irtiqaa-A4-300dpi.png'), clip: { x: 0, y: 0, width: 210 * mm, height: 297 * mm } });
  await b.close();
})();
