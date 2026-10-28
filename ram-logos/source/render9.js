// High-resolution export of the final RAM lockups, rendered in horizontal tiles and stitched.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, 'out9');
const jobs = [
  ['ram-logo-light.svg', 1024, 1536], ['ram-logo-transparent.svg', 1024, 1536], ['ram-logo-dark.svg', 1024, 1536],
  ['ram-mark-transparent.svg', 1024, 1024], ['ram-mark-white.svg', 1024, 1024],
];
const S = 4, TILE = 256;
(async () => {
  const browser = await chromium.launch();
  for (const [f, w, h] of jobs) {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: S });
    const svg = fs.readFileSync(path.join(dir, f), 'utf8');
    await page.setContent(`<!doctype html><style>html,body{margin:0;background:transparent}svg{display:block}</style>${svg}`);
    for (let y = 0, i = 0; y < h; y += TILE, i++) {
      await page.screenshot({ path: path.join(dir, `_tile-${i}.png`), omitBackground: true,
                              clip: { x: 0, y, width: w, height: Math.min(TILE, h - y) } });
    }
    await page.close();
    fs.writeFileSync(path.join(dir, `_job.txt`), `${f.replace('.svg', '.png')} ${Math.ceil(h / TILE)}`);
    require('child_process').execFileSync('python3', [path.join(__dirname, 'stitch9.py')]);
  }
  await browser.close();
})();
