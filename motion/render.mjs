// Renders the film frame-by-frame with headless Chromium and encodes it with ffmpeg.
//   node render.mjs                      → output/coffee-identity.mp4 (30 fps)
//   node render.mjs --fps 60             → smoother master
//   node render.mjs --stills 3,12,40     → PNG stills for review
//   node render.mjs --audio vo.wav       → mux the voice-over into the video
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }

const here = dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, all) => {
  if (a.startsWith('--')) acc.push([a.slice(2), all[i + 1] && !all[i + 1].startsWith('--') ? all[i + 1] : true]);
  return acc;
}, []));
const fps = +(args.fps || 30);
const out = resolve(here, args.out || 'output/coffee-identity.mp4');
mkdirSync(resolve(here, 'output'), { recursive: true });

const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('pageerror', (e) => console.error('page error:', e.message));
await page.goto(pathToFileURL(resolve(here, 'index.html')).href + '?render');
await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });
const duration = await page.evaluate(() => window.FILM.DURATION);

async function frameAt(t) {
  await page.evaluate((tt) => window.__seek(tt), t);
  return page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1080, height: 1920 } });
}

if (args.stills) {
  const { writeFileSync } = await import('node:fs');
  for (const t of String(args.stills).split(',').map(Number)) {
    const file = resolve(here, `output/still-${t.toFixed(2)}.png`);
    writeFileSync(file, await frameAt(t));
    console.log(file);
  }
  await browser.close();
  process.exit(0);
}

const from = +(args.from || 0), to = +(args.to || duration);
const total = Math.round((to - from) * fps);
const ff = ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-'];
if (args.audio) ff.push('-i', resolve(String(args.audio)), '-c:a', 'aac', '-b:a', '192k', '-shortest');
ff.push('-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out);
const enc = spawn('ffmpeg', ff, { stdio: ['pipe', 'ignore', 'inherit'] });

const started = Date.now();
for (let i = 0; i < total; i++) {
  const buf = await frameAt(from + i / fps);
  if (!enc.stdin.write(buf)) await new Promise((r) => enc.stdin.once('drain', r));
  if (i % fps === 0) process.stdout.write(`\r${(from + i / fps).toFixed(1)}s / ${to}s  (${((Date.now() - started) / 1000).toFixed(0)}s elapsed)`);
}
enc.stdin.end();
await new Promise((r) => enc.on('close', r));
await browser.close();
console.log(`\n✓ ${out}`);
