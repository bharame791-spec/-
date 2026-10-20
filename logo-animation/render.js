// Renders index.html frame-by-frame to an MP4 with the synthesized soundtrack.
// Usage: node render.js [out.mp4] [fps] [extra query, e.g. "theme=light&text=MY NAME"]
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

const out = path.resolve(process.argv[2] || 'logo-animation.mp4');
const fps = Number(process.argv[3] || 60);
const query = process.argv[4] ? '&' + process.argv[4] : '';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1080 } });
  await page.goto('file://' + path.join(__dirname, 'index.html') + '?render=1' + encodeURI(query));
  await page.evaluate(() => document.fonts.ready);

  const wav = out.replace(/\.mp4$/, '') + '.wav';
  fs.writeFileSync(wav, Buffer.from(await page.evaluate(() => window.renderAudioWav()), 'base64'));
  const duration = await page.evaluate(() => window.DURATION);

  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-i', '-', '-i', wav,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    '-c:a', 'aac', '-b:a', '256k', '-shortest', out], { stdio: ['pipe', 'inherit', 'inherit'] });

  const frames = Math.round(duration * fps);
  for (let i = 0; i <= frames; i++) {
    await page.evaluate(t => window.renderFrame(t), i / fps);
    const png = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('wrote', out, 'and', wav);
})();
