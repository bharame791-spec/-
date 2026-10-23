// Renders the trailer page frame by frame (window.seek(t)) into an H.264 video with ffmpeg.
// Usage: node render_video.js page.html out.mp4 seconds [fps]
const path = require('path');
const { spawn } = require('child_process');

function loadPlaywright() {
  try { return require('playwright'); } catch (_) {}
  return require('/opt/node-tools/node_modules/playwright');
}

(async () => {
  const [input, output, seconds, fpsArg] = process.argv.slice(2);
  const fps = Number(fpsArg || 30);
  const frames = Math.round(Number(seconds) * fps);
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.resolve(input), { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  const ff = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps),
    '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', output],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const stage = await page.$('#stage');
  for (let f = 0; f < frames; f++) {
    await page.evaluate(([t, f]) => window.seek(t, f), [f / fps, f]);
    const buf = await stage.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % (fps * 5) === 0) process.stdout.write(`frame ${f}/${frames}\n`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
