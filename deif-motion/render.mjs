// Renders scene/index.html to video, frame by frame, and muxes the voice-over.
//   node render.mjs                      -> build/deif_shadow_man.mp4
//   node render.mjs --stills 5,15,30     -> build/stills/*.jpg (quick look at given seconds)
//   node render.mjs --from 20 --to 30    -> render a time range only (no audio)
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { spawn, execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2' };
const server = createServer(async (req, res) => {
  try {
    const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
    if (!p.startsWith(ROOT)) throw new Error('outside root');
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
    res.end(await readFile(p));
  } catch { res.writeHead(404); res.end(); }
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('pageerror', e => console.error('page error:', e.message));
await page.goto(`http://127.0.0.1:${port}/scene/index.html`);
await page.evaluate(() => window.ready);
const { FPS, DURATION } = await page.evaluate(() => ({ FPS: window.FPS, DURATION: window.DURATION }));
const stage = await page.$('#stage');

if (opt('--stills')) {
  await mkdir(path.join(ROOT, 'build/stills'), { recursive: true });
  for (const s of opt('--stills').split(',').map(Number)) {
    await page.evaluate(t => window.seek(t), s);
    await stage.screenshot({ path: path.join(ROOT, `build/stills/t${String(s).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 85 });
  }
} else {
  const from = Number(opt('--from', 0)), to = Number(opt('--to', DURATION));
  const full = from === 0 && to === DURATION;
  const out = path.join(ROOT, 'build', full ? 'video_only.mp4' : `range_${from}-${to}.mp4`);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n0 = Math.round(from * FPS), n1 = Math.round(to * FPS);
  for (let f = n0; f < n1; f++) {
    await page.evaluate(t => window.seek(t), f / FPS);
    const buf = await stage.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 125 === 0) console.log(`frame ${f}/${n1}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log('wrote', out);
  if (full) {
    // sound effects were logged while frames rendered; synthesize score + sfx and mix under the VO
    const sfx = await page.evaluate(() => window.SFX);
    await writeFile(path.join(ROOT, 'build/sfx.json'), JSON.stringify(sfx));
    execFileSync('python3', ['-I', path.join(ROOT, 'tools/make_audio.py'), path.join(ROOT, 'build/sfx.json'), path.join(ROOT, 'sources/voiceover.mp3'), String(DURATION), path.join(ROOT, 'build')], { stdio: 'inherit' });
    const final = path.join(ROOT, 'build/deif_shadow_man.mp4');
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', out, '-i', path.join(ROOT, 'build/mix.wav'), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', final], { stdio: 'inherit' });
    console.log('wrote', final);
  }
}
await browser.close();
server.close();
