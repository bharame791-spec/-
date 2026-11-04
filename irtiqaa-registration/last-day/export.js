// Exports the "last day to register" post (1080×1350) and story (1080×1920) as PNG.
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  for (const [q, h, out] of [['', 1350, 'irtiqaa-last-day-post.png'], ['?story=1', 1920, 'irtiqaa-last-day-story.png']]) {
    const p = await b.newPage({ viewport: { width: 1080, height: h } });
    await p.goto('file://' + path.resolve(__dirname, 'post.html') + q);
    await p.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
    await p.screenshot({ path: path.join(__dirname, out), clip: { x: 0, y: 0, width: 1080, height: h } });
    await p.close();
  }
  await b.close();
})();
