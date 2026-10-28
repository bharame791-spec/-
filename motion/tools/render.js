// Renders motion/index.html frame-by-frame to PNGs, then encodes with ffmpeg.
// usage: node tools/render.js <outDir> [fps] [onlyTimes,comma,separated]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const out = process.argv[2];
  const fps = +(process.argv[3] || 30);
  const only = process.argv[4] ? process.argv[4].split(',').map(Number) : null;
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.resolve(__dirname, '../index.html') + '?render');
  await page.evaluate(() => document.fonts.ready);
  const dur = await page.evaluate(() => window.DUR);
  const times = only || Array.from({ length: Math.round(dur * fps) }, (_, i) => i / fps);
  for (let i = 0; i < times.length; i++) {
    await page.evaluate(t => window.render(t), times[i]);
    const name = only ? `t_${times[i]}.png` : `f_${String(i).padStart(5, '0')}.png`;
    await page.screenshot({ path: path.join(out, name) });
    if (i % 60 === 0) console.log(`frame ${i}/${times.length}`);
  }
  await browser.close();
})();
