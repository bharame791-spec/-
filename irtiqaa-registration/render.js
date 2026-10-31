// Usage:
//   node render.js stills <outDir> 3.5 8 12 ...      -> PNG stills at given seconds
//   node render.js frames <outDir> <fps> <from> <to>  -> JPEG frame sequence
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [mode, out, ...rest] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  await page.goto('file://' + path.resolve(__dirname, 'index.html'));
  await page.waitForFunction(() => window.READY === true, null, { timeout: 90000 });
  const clip = { x: 0, y: 0, width: 1080, height: 1920 };
  if (mode === 'stills') {
    for (const s of rest) {
      await page.evaluate(t => render(t), +s);
      await page.screenshot({ path: `${out}/still_${String(s).replace('.', '_')}.png`, clip });
    }
  } else {
    const [fps, from, to] = rest.map(Number);
    for (let f = Math.round(from * fps); f < Math.round(to * fps); f++) {
      await page.evaluate(t => render(t), f / fps);
      await page.screenshot({ path: `${out}/f${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 90, clip });
    }
  }
  await browser.close();
})();
