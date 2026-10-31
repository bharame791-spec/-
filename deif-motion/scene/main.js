/* محمد الضيف | رجل الظل — collage motion graphic, one shot per voice-over line.
   window.seek(t) renders the frame at time t (seconds); render.mjs drives it frame by frame. */
const W = 1080, H = 1920, FPS = 25, DURATION = 85;
const A = '../assets/', CLIPS = '../build/clips/';
const stage = document.getElementById('stage');

/* ================= helpers ================= */
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, p) => a + (b - a) * p;
const E = {
  lin: p => p,
  out: p => 1 - Math.pow(1 - p, 3),
  out5: p => 1 - Math.pow(1 - p, 5),
  in: p => p * p * p,
  io: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
  expo: p => p === 0 ? 0 : p === 1 ? 1 : p < .5 ? Math.pow(2, 20 * p - 10) / 2 : (2 - Math.pow(2, -20 * p + 10)) / 2,
  back: p => { const c = 1.7; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); },
};
const pr = (t, a, b, e = E.out) => e(clamp((t - a) / (b - a)));
function kf(t, keys, e = E.io) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) {
    const [t0, v0] = keys[i - 1], [t1, v1] = keys[i];
    return lerp(v0, v1, e((t - t0) / (t1 - t0)));
  }
  return keys[keys.length - 1][1];
}
function rand(seed) {
  let a = seed >>> 0;
  return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
function el(parent, cls = '', css = {}, html = '') {
  const d = document.createElement('div');
  if (cls) d.className = cls;
  Object.assign(d.style, { position: 'absolute' }, css);
  if (html) d.innerHTML = html;
  parent.appendChild(d);
  return d;
}
function img(parent, src, css = {}) {
  const i = document.createElement('img');
  i.src = src;
  Object.assign(i.style, { position: 'absolute', display: 'block' }, css);
  parent.appendChild(i);
  return i;
}
function tf(node, { x = 0, y = 0, s = 1, r = 0, o = 1, sx, sy } = {}) {
  const sc = sx !== undefined ? `scale(${sx},${sy})` : `scale(${s})`;
  node.style.transform = `translate(${x}px,${y}px) rotate(${r}deg) ${sc}`;
  node.style.opacity = o;
  node.style.visibility = o <= 0.001 ? 'hidden' : 'visible';
}
function tornPoly(seed, jag = 1.6, steps = 26) {
  const R = rand(seed), pts = [], j = () => R() * jag;
  for (let i = 0; i <= steps; i++) pts.push([i / steps * 100, j()]);
  for (let i = 0; i <= steps; i++) pts.push([100 - j(), i / steps * 100]);
  for (let i = steps; i >= 0; i--) pts.push([i / steps * 100, 100 - j()]);
  for (let i = steps; i >= 0; i--) pts.push([j(), i / steps * 100]);
  return `polygon(${pts.map(p => `${p[0].toFixed(2)}% ${p[1].toFixed(2)}%`).join(',')})`;
}

/* go(): entrance (spring), idle float, optional exit — one call per element per frame.
   from/to: {x,y,s,r}; idle: float amplitude multiplier */
function go(node, t, { t0 = 0, dur = .6, from = {}, to = {}, ease = E.back, idle = 1, seed = 1, t1 = null, out = {}, outDur = .35, fade = .25, snd = null }) {
  if (snd && t >= t0) sfxOnce(node, 'go', snd, t0);
  const p = pr(t, t0, t0 + dur, ease);
  const v = k => lerp(from[k] ?? to[k] ?? (k === 's' ? 1 : 0), to[k] ?? (k === 's' ? 1 : 0), p);
  let x = v('x'), y = v('y'), s = v('s'), r = v('r');
  let o = t < t0 ? 0 : clamp((t - t0) / (dur * fade + .001));
  if (idle) {
    x += Math.sin(t * .9 + seed * 2.1) * 5 * idle;
    y += Math.cos(t * .75 + seed * 1.3) * 8 * idle;
    r += Math.sin(t * .55 + seed) * .7 * idle;
  }
  if (t1 !== null && t > t1) {
    const q = pr(t, t1, t1 + outDur, E.in);
    x += (out.x || 0) * q; y += (out.y || 0) * q; s *= lerp(1, out.s ?? 1, q); r += (out.r || 0) * q;
    if (out.fade !== false) o *= 1 - q;
  }
  tf(node, { x, y, s, r, o });
}
// right-to-left wipe reveal (Arabic reading direction)
function wipe(node, t, t0, dur = .6) {
  const p = pr(t, t0, t0 + dur, E.io);
  node.style.clipPath = `inset(-20% 0 -20% ${((1 - p) * 100).toFixed(2)}%)`;
}
function text(parent, html, css = {}, cls = 'title rtl') { return el(parent, cls, css, html); }
function tape(parent, html, size, css = {}, kind = '', seed = 5) {
  const n = el(parent, 'tape ' + kind, Object.assign({ fontSize: size + 'px' }, css), html);
  n.style.clipPath = tornPoly(seed, 2.4);
  return n;
}
function stampEl(parent, html, size, css = {}, light = false) {
  return el(parent, 'stamp' + (light ? ' light' : ''), Object.assign({ fontSize: size + 'px' }, css), html);
}
function slam(node, t, t0, { r = -6, x = 0, y = 0, from = 2.3 } = {}) {
  if (t >= t0) sfxOnce(node, 'slam', 'thud', t0 + .2);
  const p = pr(t, t0, t0 + .22, E.in), st = pr(t, t0 + .22, t0 + .55, E.out);
  tf(node, { x, y, r, s: t < t0 ? from : lerp(from, 1, p) * (1 + .05 * Math.sin(st * Math.PI)), o: t < t0 ? 0 : clamp(p * 3) });
}
function cloud(parent, k, css) { return img(parent, `${A}scraps_${k}.png`, Object.assign({ width: '620px' }, css)); }
function smoke(parent, k, css) { return img(parent, `${A}smoke_${k}.png`, Object.assign({ width: '700px', mixBlendMode: 'multiply' }, css)); }
function circle(parent, d, color, css = {}) { return el(parent, '', Object.assign({ width: d + 'px', height: d + 'px', borderRadius: '50%', background: color }, css)); }
function newsClip(parent, { head = '', meta = ['', ''], cols = 2, w = 420, h = 360, size = 44, seed = 3, redact = [] }, css = {}) {
  const n = el(parent, 'news', Object.assign({ width: w + 'px', height: h + 'px', boxSizing: 'border-box' }, css));
  n.style.clipPath = tornPoly(seed, 2.2);
  el(n, 'meta', { position: 'relative' }, `<span>${meta[0]}</span><span>${meta[1]}</span>`);
  if (head) el(n, '', { position: 'relative', fontFamily: 'Cairo', fontWeight: 900, fontSize: size + 'px', lineHeight: 1.15, marginBottom: '12px' }, head);
  const c = el(n, 'cols', { position: 'relative', gridTemplateColumns: `repeat(${cols},1fr)`, height: `calc(100% - ${head ? size * 1.3 + 70 : 60}px)` });
  for (let i = 0; i < cols; i++) el(c, '', { position: 'relative' }, '<i></i>');
  redact.forEach(([x, y, rw, rh]) => el(n, 'redact', { left: x + '%', top: y + '%', width: rw + '%', height: rh + 'px' }));
  return n;
}

/* sound effects: each entry {k: kind, t: seconds, g: gain}; read by render.mjs */
const SFX = [];
const sfx = (k, t, g = 1) => SFX.push({ k, t: +t.toFixed(3), g });
const sfxOnce = (node, key, k, t, g) => { node._sfx = node._sfx || new Set(); if (!node._sfx.has(key)) { node._sfx.add(key); sfx(k, t, g); } };

/* media frames: 'stamp' (perforated), 'polaroid', 'torn', 'circle'. src: clip name or image path */
const pending = [];
function frame(parent, css, { kind = 'stamp', clip = null, frames = 1, src = null, speed = 1, start = 0, freezeAt = null, seed = 1, red = false, fit = 'cover', pos = '50% 50%' } = {}) {
  const wrap = el(parent, 'pwrap', css);
  let inner;
  if (kind === 'stamp') inner = el(wrap, 'pstamp' + (red ? ' red' : ''), { position: 'relative' });
  else if (kind === 'polaroid') inner = el(wrap, 'polaroid', { position: 'relative' });
  else if (kind === 'circle') inner = el(wrap, '', { position: 'relative', width: '100%', height: '100%', borderRadius: '50%', overflow: 'hidden' });
  else { inner = el(wrap, 'clip', { position: 'relative', width: '100%', height: '100%', boxSizing: 'border-box' }); inner.style.clipPath = tornPoly(seed, 1.2); }
  const media = el(inner, 'media', { position: 'relative' });
  const im = img(media, clip ? `${CLIPS}${clip}/0001.jpg` : src, { objectPosition: pos, objectFit: fit });
  let cur = 1;
  return {
    wrap, im,
    update(t) {
      if (!clip) return;
      let lt = t - start;
      if (freezeAt !== null) lt = Math.min(lt, freezeAt - start);
      const f = clamp(Math.floor(Math.max(0, lt) * FPS * speed) + 1, 1, frames);
      if (f !== cur) { cur = f; im.src = `${CLIPS}${clip}/${String(f).padStart(4, '0')}.jpg`; pending.push(im.decode().catch(() => { })); }
      const fz = freezeAt !== null ? pr(t, freezeAt, freezeAt + .4) : 0;
      im.style.filter = `contrast(${1.15 + fz * .25}) sepia(${fz * .3})`;
    }
  };
}
function flash(parent) { return el(parent, '', { inset: 0, background: '#fff', mixBlendMode: 'screen', zIndex: 20 }); }
const flashAt = (node, t, times) => { times.forEach(t0 => { if (t >= t0) sfxOnce(node, t0, 'shutter', t0); }); const v = Math.max(0, ...times.map(t0 => t >= t0 ? 1 - pr(t, t0, t0 + .28, E.out) : 0)); node.style.opacity = v * .85; };

/* ================= cue points: start of each VO line (seconds), from word timestamps in sources/voiceover_words.json ================= */
const C = [0, 1.26, 3.62, 5.54, 6.66, 8.60, 10.48, 13.54, 15.70, 17.32, 19.50, 22.14, 26.18, 27.70, 29.70, 31.52, 34.32,
  39.30, 41.20, 43.22, 45.70, 47.66, 50.64, 53.14, 54.42, 56.60, 58.84, 63.50, 67.28, 69.88, 71.70, 77.20];

/* ================= shot system ================= */
const shots = [];
const world = el(stage, '', { inset: 0 });
// enter: how the camera arrives — L/R/U/D whip pans, Z push-through, F fade
function shot(i, bg, enter, build, { push = .045 } = {}) {
  const t0 = C[i], t1 = i + 1 < C.length ? C[i + 1] : DURATION;
  const root = el(world, 'scene bg-' + bg, { inset: 0 });
  const cam = el(root, 'cam');
  const s = { i, t0, t1, root, cam, enter, push };
  s.update = build(cam, t0, t1, s);
  if (i > 0 && 'LRUDZ'.includes(enter)) sfx(enter === 'Z' ? 'swell' : 'whoosh', t0 - .08);
  shots.push(s);
}
const TR = .5; // transition length

/* ---------- 1. لعقودٍ طويلة ---------- */
shot(0, 'dark', 'F', (cam, t0, t1) => {
  const R0 = rand(11), rows = [];
  for (let i = 0; i < 26; i++) {
    const txt = Array.from({ length: 7 }, () => ['1965', '1989', '1996', '2002', '2014', '2024', '31.34°N', '34.30°E', 'NO.' + Math.floor(R0() * 900 + 100)][Math.floor(R0() * 9)]).join('   ·   ');
    rows.push(el(cam, 'mono', { left: '-60px', top: (i * 76) + 'px', fontSize: '24px', whiteSpace: 'nowrap', color: '#3b3732' }, txt));
  }
  const bars = Array.from({ length: 16 }, () => el(cam, '', { left: 0, width: W + 'px', background: '#d8d2c6' }));
  sfx('static', 0, .7);
  const t1a = text(cam, 'لعقودٍ', { left: 0, right: 0, top: '700px', textAlign: 'center', fontSize: '230px' });
  const t1b = text(cam, 'طويلة', { left: 0, right: 0, top: '930px', textAlign: 'center', fontSize: '230px', color: '#a52222' });
  return (t) => {
    const R = rand(Math.round(t * FPS) * 7 + 3);
    rows.forEach((r, i) => tf(r, { x: (i % 2 ? -1 : 1) * t * 40 - (i % 2 ? 0 : 160), o: .9 }));
    bars.forEach(b => { b.style.top = (R() * H) + 'px'; b.style.height = (2 + R() * 34) + 'px'; b.style.opacity = (t < .5 ? 1 : .25) * R() * .55; });
    go(t1a, t, { t0: .15, from: { s: 1.4 }, ease: E.out5, idle: .5, seed: 1 }); wipe(t1a, t, .15, .45);
    go(t1b, t, { t0: .45, from: { s: 1.4 }, ease: E.out5, idle: .5, seed: 2 }); wipe(t1b, t, .45, .45);
  };
});

/* ---------- 2. كان اسمه يتردّد في نشرات الأخبار ---------- */
shot(1, 'dark', 'U', (cam, t0) => {
  const n1 = newsClip(cam, { head: 'المطلوب الأول', meta: ['أرشيف', '—'], w: 560, h: 470, size: 72, seed: 21 }, { left: '60px', top: '330px' });
  const n2 = newsClip(cam, { head: 'اسمٌ في كل نشرة', meta: ['أخبار', '—'], w: 500, h: 400, size: 54, seed: 22, cols: 3 }, { left: '500px', top: '760px' });
  const n3 = newsClip(cam, { head: 'من هو؟', meta: ['ملف', '???'], w: 440, h: 380, size: 70, seed: 23, redact: [[10, 62, 70, 26]] }, { left: '90px', top: '1150px' });
  const tick = el(cam, '', { left: 0, top: '1640px', width: W + 'px', height: '96px', background: 'var(--red)', overflow: 'hidden' });
  const ttxt = el(tick, 'rtl', { top: '6px', right: 0, whiteSpace: 'nowrap', fontFamily: 'Cairo', fontWeight: 900, fontSize: '56px', color: '#f2ede3' }, 'عاجل  ●  عاجل  ●  عاجل  ●  عاجل  ●  عاجل  ●  عاجل  ●  عاجل  ●  عاجل');
  const lab = el(tick, '', { left: 0, top: 0, height: '96px', width: '230px', background: '#121110', color: '#f2ede3', fontFamily: 'Cairo', fontWeight: 900, fontSize: '50px', textAlign: 'center', lineHeight: '92px' }, 'أخبار');
  return (t) => {
    go(n1, t, { snd: 'paper', t0: t0 + .1, from: { x: -700, r: -25 }, to: { r: -5 }, seed: 3, dur: .55 });
    go(n2, t, { snd: 'paper', t0: t0 + .45, from: { x: 700, r: 25 }, to: { r: 4 }, seed: 4, dur: .55 });
    go(n3, t, { snd: 'paper', t0: t0 + .8, from: { y: 700, r: -10 }, to: { r: -3 }, seed: 5, dur: .55 });
    go(tick, t, { t0: t0 + .2, from: { x: W }, ease: E.out5, idle: 0 });
    tf(ttxt, { x: (t - t0) * 260 - 900 }); tf(lab, {});
  };
});

/* ---------- 3. بينما بقي وجهه مجهولًا ---------- */
shot(2, 'dark', 'Z', (cam, t0) => {
  const q = text(cam, '؟', { left: 0, right: 0, top: '220px', textAlign: 'center', fontSize: '1100px', color: '#3a1414', lineHeight: 1 });
  const f = frame(cam, { left: '190px', top: '470px', width: '700px', height: '760px' }, { kind: 'polaroid', src: A + 'silhouette_bw.jpg' });
  const bar = el(cam, '', { left: '250px', top: '640px', width: '580px', height: '110px', background: '#0c0b0a', transformOrigin: 'right center' });
  const lab = text(cam, 'وجهٌ مجهول', { left: 0, right: 0, top: '1330px', textAlign: 'center', fontSize: '130px' });
  const c = cloud(cam, 1, { left: '230px', top: '1100px' });
  return (t) => {
    go(q, t, { t0: t0, from: { s: 1.3 }, ease: E.out5, idle: .5, seed: 7 });
    go(f.wrap, t, { t0: t0 + .15, from: { s: .6, r: 12 }, to: { r: -3 }, seed: 8 });
    go(bar, t, { t0: t0 + .55, from: {}, idle: 0 }); bar.style.transform += ` rotate(-3deg) scaleX(${pr(t, t0 + .55, t0 + .8, E.out)})`;
    go(lab, t, { t0: t0 + .7, from: { y: 40 }, ease: E.out, idle: .4 }); wipe(lab, t, t0 + .7, .5);
    go(c, t, { t0: t0 + .3, from: { y: 60, s: .7 }, idle: 1.5, seed: 9 });
  };
});

/* ---------- 4. صورٌ قليلة ---------- */
shot(3, 'paper', 'L', (cam, t0) => {
  const fl = flash(cam);
  const pics = [
    frame(cam, { left: '90px', top: '420px', width: '470px', height: '560px' }, { kind: 'polaroid', src: A + 'portrait_main_bw.png', fit: 'contain' }),
    frame(cam, { left: '520px', top: '560px', width: '470px', height: '560px' }, { kind: 'polaroid', src: A + 'portrait_interview_bw.png', fit: 'contain' }),
    frame(cam, { left: '300px', top: '880px', width: '470px', height: '560px' }, { kind: 'polaroid', src: A + 'portrait_tree_bw.png', fit: 'contain' }),
  ];
  pics.forEach(p => { p.im.style.background = '#cfc8ba'; });
  const lab = text(cam, 'صورٌ قليلة', { left: 0, right: 0, top: '190px', textAlign: 'center', fontSize: '130px', color: 'var(--ink)' });
  const rs = [-8, 7, -2];
  return (t) => {
    pics.forEach((p, i) => go(p.wrap, t, { t0: t0 + .05 + i * .28, from: { y: -900, r: rs[i] * 4 }, to: { r: rs[i] }, dur: .5, seed: 10 + i }));
    flashAt(fl, t, [t0 + .3, t0 + .58, t0 + .86]);
    go(lab, t, { t0: t0 + .1, from: { y: 30 }, ease: E.out, idle: .3 }); wipe(lab, t, t0 + .1, .4);
  };
});

/* ---------- 5. وصوتٌ من خلف الظل (title) ---------- */
shot(4, 'dark', 'R', (cam, t0) => {
  const ring = circle(cam, 820, 'var(--red)', { left: '130px', top: '300px' });
  const sil = frame(cam, { left: '240px', top: '380px', width: '600px', height: '600px' }, { kind: 'circle', src: A + 'silhouette_bw.jpg' });
  const wave = el(cam, '', { left: '120px', top: '1060px', width: '840px', height: '150px', display: 'flex', alignItems: 'center', gap: '7px' });
  const bars = Array.from({ length: 44 }, () => el(wave, 'wbar', { position: 'relative', background: '#f2ede3' }));
  sfx('boom', t0 + .35);
  const name = text(cam, 'محمد الضيف', { left: 0, right: 0, top: '1250px', textAlign: 'center', fontSize: '210px' });
  const sub = tape(cam, 'رجل الظل', 84, { left: '330px', top: '1520px' }, 'red', 41);
  return (t) => {
    go(ring, t, { t0: t0, from: { s: 0 }, dur: .6, idle: .3, seed: 1 });
    go(sil.wrap, t, { t0: t0 + .1, from: { s: .5 }, dur: .6, idle: .6, seed: 2 });
    const amp = pr(t, t0 + .2, t0 + .5);
    const R = rand(Math.round(t * FPS));
    bars.forEach((b, i) => { const v = Math.abs(Math.sin(t * 10 + i * .6) * Math.sin(t * 3.3 + i * 1.7)) * .8 + R() * .2; b.style.height = (8 + v * 140 * amp) + 'px'; });
    go(name, t, { t0: t0 + .35, from: { s: 1.5 }, ease: E.out5, dur: .45, idle: .4 }); wipe(name, t, t0 + .35, .5);
    go(sub, t, { t0: t0 + .9, from: { x: 300, r: 8 }, to: { r: -3 }, seed: 3 });
  };
});

/* ---------- 6. وُلد محمد دياب إبراهيم المصري ---------- */
shot(5, 'paper', 'U', (cam, t0) => {
  const card = el(cam, 'news', { left: '90px', top: '520px', width: '900px', height: '600px', boxSizing: 'border-box', padding: '40px 50px' });
  card.style.clipPath = tornPoly(53, 1.2);
  el(card, 'meta', { position: 'relative', fontSize: '28px' }, '<span>بطاقة تعريف · أرشيف</span><span>رقم 1965/08</span>');
  const photo = frame(card, { left: '40px', top: '120px', width: '250px', height: '330px' }, { kind: 'stamp', src: A + 'portrait_main_bw.png', fit: 'cover', pos: '50% 20%' });
  const lines = ['الاسم: محمد دياب إبراهيم المصري', 'الشهرة: محمد الضيف', 'مكان الولادة: خان يونس'];
  const ls = lines.map((l, i) => el(card, 'info', { right: '50px', top: (150 + i * 95) + 'px', fontSize: '34px', whiteSpace: 'nowrap' }, l));
  const clipEl = el(cam, '', { left: '760px', top: '470px', width: '40px', height: '130px', border: '8px solid #7a7570', borderRadius: '22px' });
  const big = text(cam, 'وُلد', { right: '260px', top: '200px', fontSize: '210px', color: 'var(--ink)' });
  const st = stampEl(cam, 'أرشيف', 90, { left: '120px', top: '1180px' });
  return (t) => {
    go(card, t, { snd: 'paper', t0: t0 + .05, from: { y: 600, r: 8 }, to: { r: -2 }, seed: 4 });
    go(photo.wrap, t, { t0: t0 + .4, from: { s: 0, r: -20 }, to: { r: -4 }, idle: 0 });
    ls.forEach((l, i) => wipe(l, t, t0 + .45 + i * .35, .5));
    go(clipEl, t, { t0: t0 + .4, from: { y: -200 }, to: { r: 8 }, seed: 5 });
    go(big, t, { t0: t0, from: { x: 120 }, ease: E.out5, idle: .4 }); wipe(big, t, t0, .45);
    slam(st, t, t0 + 1.5, { r: -10 });
  };
});

/* ---------- 7. عام 1965 ---------- */
shot(6, 'paper', 'L', (cam, t0) => {
  const ring = circle(cam, 760, 'var(--red)', { left: '160px', top: '420px' });
  const alley = frame(cam, { left: '230px', top: '490px', width: '620px', height: '620px' }, { kind: 'circle', clip: 'alley', frames: 100, start: t0, speed: .8 });
  const year = text(cam, 'عام', { right: '290px', top: '150px', fontSize: '150px', color: 'var(--ink)' });
  // odometer digits
  const od = el(cam, '', { left: '140px', top: '1180px', width: '800px', height: '300px', display: 'flex', direction: 'ltr', justifyContent: 'center', gap: '6px' });
  const digits = '1965'.split('').map((d, i) => {
    const win = el(od, '', { position: 'relative', width: '190px', height: '300px', overflow: 'hidden' });
    const col = el(win, '', { left: 0, top: 0, width: '190px', fontFamily: 'Cairo', fontWeight: 900, fontSize: '280px', lineHeight: '300px', color: 'var(--ink)', textAlign: 'center' }, Array.from({ length: 30 }, (_, k) => (k % 10)).join('<br>'));
    return { col, target: 20 + Number(d), i };
  });
  for (let k = 0; k < 14; k++) sfx('tick', t0 + .2 + k * .065, .5);
  const c = cloud(cam, 0, { left: '230px', top: '980px' });
  const st = stampEl(cam, 'عام الميلاد', 70, { left: '90px', top: '1520px' });
  return (t) => {
    go(ring, t, { t0: t0, from: { s: 0 }, idle: .3 });
    go(alley.wrap, t, { t0: t0 + .1, from: { s: .4 }, idle: .5, seed: 2 }); alley.update(t);
    go(year, t, { t0: t0 + .1, from: { y: -40 }, ease: E.out, idle: .3 }); wipe(year, t, t0 + .1, .4);
    digits.forEach(({ col, target, i }) => { const p = pr(t, t0 + .2, t0 + 1.1 + i * .25, E.out5); col.style.transform = `translateY(${-p * target * 300}px)`; });
    go(c, t, { t0: t0 + .2, from: { y: 80, s: .6 }, idle: 1.4, seed: 3 });
    slam(st, t, t0 + 1.7, { r: -6 });
  };
});

/* ---------- 8. في مخيم خان يونس للاجئين ---------- */
shot(7, 'paper', 'U', (cam, t0) => {
  const f1 = frame(cam, { left: '80px', top: '360px', width: '700px', height: '560px' }, { kind: 'stamp', clip: 'camp', frames: 175, start: t0, speed: .9 });
  const f2 = frame(cam, { left: '470px', top: '860px', width: '520px', height: '440px' }, { kind: 'stamp', red: true, clip: 'camp', frames: 175, start: t0 - 3, speed: .7 });
  const lab = tape(cam, 'مخيم خان يونس للاجئين', 66, { right: '80px', top: '1420px' }, 'ink', 52);
  const c = cloud(cam, 2, { left: '-60px', top: '1050px' });
  const pin = text(cam, '●', { left: '660px', top: '250px', fontSize: '60px', color: 'var(--red2)' });
  return (t) => {
    go(f1.wrap, t, { t0: t0, from: { x: -600, r: -20 }, to: { r: -4 }, seed: 1 }); f1.update(t);
    go(f2.wrap, t, { t0: t0 + .3, from: { x: 600, r: 20 }, to: { r: 5 }, seed: 2 }); f2.update(t);
    go(lab, t, { t0: t0 + .7, from: { y: 120 }, to: { r: -2 }, seed: 3 });
    go(c, t, { t0: t0 + .4, from: { x: -200 }, idle: 1.5, seed: 4 });
    go(pin, t, { t0: t0 + .5, from: { s: 0 }, idle: 0 });
  };
});

/* ---------- 9. جنوبي قطاع غزة (map) ---------- */
shot(8, 'paper', 'Z', (cam, t0) => {
  const mapWrap = el(cam, '', { left: '190px', top: '330px', width: '700px', height: '1200px' });
  mapWrap.innerHTML = `<svg width="700" height="1200" viewBox="0 0 700 1200" style="overflow:visible">
    <path class="mo" fill="#cfc6b4" stroke="#1a1816" stroke-width="3.5" stroke-linejoin="round"/>
    <path class="mg" fill="#8e1b1b" stroke="#1a1816" stroke-width="2"/>
    <circle class="kr" r="9" fill="none" stroke="#8e1b1b" stroke-width="3"/>
    <circle class="ky" r="9" fill="#f2ede3" stroke="#8e1b1b" stroke-width="4"/></svg>`;
  const lab = tape(cam, 'جنوبي قطاع غزة', 70, { left: '90px', top: '1500px' }, 'red', 61);
  const lab2 = tape(cam, 'خان يونس', 48, { left: '560px', top: '880px' }, 'ink', 62);
  let mo, mg, ky, kr, len;
  return (t) => {
    if (!mo) {
      const d = window.MAP; [mo, mg, ky, kr] = ['.mo', '.mg', '.ky', '.kr'].map(q => mapWrap.querySelector(q));
      mo.setAttribute('d', d.outline); mg.setAttribute('d', d.gaza);
      [ky, kr].forEach(c => { c.setAttribute('cx', d.khanYunis[0]); c.setAttribute('cy', d.khanYunis[1]); });
      len = mo.getTotalLength(); mo.style.strokeDasharray = len;
      mapWrap.style.transformOrigin = `${d.gazaCenter[0]}px ${d.gazaCenter[1]}px`;
    }
    mo.style.strokeDashoffset = len * (1 - pr(t, t0, t0 + .7, E.io));
    mo.style.fillOpacity = pr(t, t0 + .4, t0 + .8);
    mg.style.opacity = pr(t, t0 + .6, t0 + .8);
    const z = kf(t, [[t0 + .7, 1], [t0 + 1.4, 1.9]], E.expo);
    tf(mapWrap, { s: z, x: kf(t, [[t0 + .7, 0], [t0 + 1.4, 160]], E.expo), y: kf(t, [[t0 + .7, 0], [t0 + 1.4, -40]], E.expo) });
    mo.style.strokeWidth = 3.5 / z; mg.style.strokeWidth = 2 / z;
    const pulse = (((t - t0) % .9) + .9) % .9 / .9;
    ky.setAttribute('r', 14 / z); ky.style.opacity = pr(t, t0 + 1.2, t0 + 1.3);
    kr.setAttribute('r', (14 + pulse * 40) / z); kr.style.opacity = t > t0 + 1.2 ? 1 - pulse : 0;
    go(lab, t, { t0: t0 + .3, from: { x: -400 }, to: { r: -2 }, seed: 2 });
    go(lab2, t, { t0: t0 + 1.25, from: { s: 0 }, to: { r: 3 }, seed: 3 });
  };
}, { push: .02 });

/* ---------- 10. درس العلوم في الجامعة الإسلامية ---------- */
shot(9, 'paper', 'R', (cam, t0) => {
  const f = frame(cam, { left: '70px', top: '420px', width: '940px', height: '720px' }, { kind: 'stamp', clip: 'university', frames: 200, start: t0, speed: .9 });
  const lab = tape(cam, 'الجامعة الإسلامية — غزة', 64, { right: '70px', top: '1210px' }, 'red', 63);
  const sci = text(cam, 'درس العلوم', { right: '270px', top: '190px', fontSize: '140px', color: 'var(--ink)' });
  const c = cloud(cam, 1, { left: '520px', top: '1020px' });
  return (t) => {
    go(f.wrap, t, { t0: t0, from: { s: .7, r: 10 }, to: { r: -2 }, seed: 1 }); f.update(t);
    go(lab, t, { t0: t0 + .5, from: { x: 400 }, to: { r: -2 }, seed: 2 });
    go(sci, t, { t0: t0 + .1, from: { y: -30 }, ease: E.out, idle: .4 }); wipe(sci, t, t0 + .1, .5);
    go(c, t, { t0: t0 + .3, from: { x: 300 }, idle: 1.5, seed: 3 });
  };
});

/* ---------- 11. وانضم إلى حركة حماس في سنواتها الأولى ---------- */
shot(10, 'old', 'U', (cam, t0) => {
  const n = newsClip(cam, { head: 'الانتفاضة الأولى', meta: ['ديسمبر 1987', 'غزة'], w: 760, h: 560, size: 96, seed: 64, cols: 3 }, { left: '160px', top: '380px' });
  const f = frame(cam, { left: '80px', top: '980px', width: '520px', height: '420px' }, { kind: 'stamp', clip: 'street', frames: 75, start: t0, speed: .8 });
  const st = stampEl(cam, '1987', 140, { left: '600px', top: '1080px' });
  const lab = tape(cam, 'حماس · السنوات الأولى', 60, { right: '80px', top: '1480px' }, 'ink', 65);
  return (t) => {
    go(n, t, { snd: 'paper', t0: t0, from: { y: -700, r: -14 }, to: { r: -3 }, seed: 1 });
    go(f.wrap, t, { t0: t0 + .35, from: { x: -600, r: -15 }, to: { r: 4 }, seed: 2 }); f.update(t);
    slam(st, t, t0 + .9, { r: 8 });
    go(lab, t, { t0: t0 + 1.2, from: { x: 400 }, to: { r: -2 }, seed: 3 });
  };
});

/* ---------- 12. واعتقلته إسرائيل عام 1989 ---------- */
shot(11, 'dark', 'L', (cam, t0, t1) => {
  const f = frame(cam, { left: '90px', top: '440px', width: '900px', height: '760px' }, { kind: 'stamp', clip: 'arrest89', frames: 125, start: t0, freezeAt: t0 + 2.6 });
  const barsBox = el(cam, '', { left: '110px', top: '460px', width: '860px', height: '720px', overflow: 'hidden' });
  const bars = Array.from({ length: 7 }, (_, i) => el(barsBox, '', { left: (40 + i * 125) + 'px', top: 0, width: '22px', height: '720px', background: 'linear-gradient(90deg,#111,#555 40%,#111)' }));
  const lab = text(cam, 'الاعتقال الأول', { right: '260px', top: '200px', fontSize: '140px' });
  sfx('clank', t0 + 1.0);
  const st = stampEl(cam, '1989', 190, { left: '330px', top: '1300px' }, true);
  return (t) => {
    go(f.wrap, t, { t0: t0, from: { s: .75, r: -8 }, to: { r: -1.5 }, seed: 1 }); f.update(t);
    bars.forEach((b, i) => tf(b, { y: -760 * (1 - pr(t, t0 + .9 + i * .06, t0 + 1.3 + i * .06, E.back)) }));
    go(lab, t, { t0: t0 + .15, from: { x: 150 }, ease: E.out5, idle: .4 }); wipe(lab, t, t0 + .15, .5);
    slam(st, t, t0 + 1.55, { r: -8 });
  };
});

/* ---------- 13. عام 2002 ---------- */
shot(12, 'dark', 'Z', (cam, t0) => {
  const ring = circle(cam, 900, 'var(--red)', { left: '90px', top: '500px' });
  const n = el(cam, '', { left: 0, right: 0, top: '650px', textAlign: 'center', fontFamily: 'Cairo', fontWeight: 900, fontSize: '400px', lineHeight: 1, color: '#f2ede3' }, '2002');
  const ghost = el(cam, '', { left: 0, right: 0, top: '120px', textAlign: 'center', fontFamily: 'Cairo', fontWeight: 900, fontSize: '400px', lineHeight: 1, color: 'transparent', WebkitTextStroke: '3px #5a2222' }, '2002');
  const lab = text(cam, 'عام', { left: 0, right: 0, top: '1450px', textAlign: 'center', fontSize: '120px' });
  return (t) => {
    go(ring, t, { t0: t0, from: { s: 0 }, dur: .5, idle: .3 });
    go(n, t, { t0: t0 + .15, from: { s: 2.4 }, ease: E.out5, dur: .4, idle: .4 });
    go(ghost, t, { t0: t0 + .3, from: { y: 80 }, ease: E.out, idle: .3, seed: 3 });
    go(lab, t, { t0: t0 + .2, from: { y: 40 }, ease: E.out, idle: .3 });
  };
});

/* ---------- 14. تولّى قيادة كتائب القسام ---------- */
shot(13, 'dark', 'U', (cam, t0) => {
  const ring = circle(cam, 820, 'var(--red)', { left: '130px', top: '420px' });
  const p = img(cam, A + 'portrait_main_ht.png', { left: '170px', top: '360px', width: '740px' });
  const c1 = cloud(cam, 0, { left: '-80px', top: '1000px', width: '760px' });
  const c2 = cloud(cam, 2, { left: '420px', top: '1040px', width: '700px' });
  const lab = tape(cam, 'قيادة كتائب القسام', 76, { right: '80px', top: '1420px' }, 'red', 71);
  return (t) => {
    go(ring, t, { t0: t0, from: { s: 0 }, idle: .3 });
    go(p, t, { t0: t0 + .1, from: { y: 300, s: .8 }, dur: .6, idle: .6, seed: 2 });
    go(c1, t, { t0: t0 + .2, from: { x: -300 }, idle: 1.6, seed: 3 });
    go(c2, t, { t0: t0 + .25, from: { x: 300 }, idle: 1.6, seed: 4 });
    go(lab, t, { t0: t0 + .6, from: { x: 400, r: 6 }, to: { r: -2 }, seed: 5 });
  };
});

/* ---------- 15. الجناح العسكري لحماس ---------- */
shot(14, 'paper', 'L', (cam, t0) => {
  const b1 = el(cam, 'tape ink', { left: '340px', top: '380px', fontSize: '90px', width: '400px', textAlign: 'center', boxSizing: 'border-box' }, 'حماس');
  const svg = el(cam, '', { left: 0, top: 0, width: W + 'px', height: H + 'px' });
  svg.innerHTML = `<svg width="${W}" height="${H}" style="overflow:visible"><path class="ln" d="M540 540 L540 880" stroke="#1a1816" stroke-width="8" fill="none" stroke-dasharray="12 12"/>
    <path class="mk" d="M250 1000 C 180 1150, 420 1260, 640 1210 C 900 1160, 900 960, 640 930 C 450 905, 260 950, 240 1060" stroke="#a52222" stroke-width="10" fill="none" stroke-linecap="round"/></svg>`;
  const b2 = el(cam, 'tape red', { left: '230px', top: '960px', fontSize: '84px', width: '620px', textAlign: 'center', boxSizing: 'border-box' }, 'الجناح العسكري');
  const sub = el(cam, 'info', { left: 0, right: 0, top: '1320px', textAlign: 'center', fontSize: '46px', color: '#3a3530' }, 'كتائب عز الدين القسام');
  const sticker = img(cam, A + 'portrait_main_ht.png', { left: '700px', top: '1380px', width: '300px' });
  let ln, mk, L1, L2;
  return (t) => {
    if (!ln) { ln = svg.querySelector('.ln'); mk = svg.querySelector('.mk'); L2 = mk.getTotalLength(); mk.style.strokeDasharray = L2; }
    go(b1, t, { t0: t0, from: { y: -300 }, to: { r: -2 }, seed: 1 });
    ln.style.opacity = pr(t, t0 + .3, t0 + .6); ln.style.transform = `scaleY(${pr(t, t0 + .3, t0 + .7)})`; ln.style.transformOrigin = '540px 540px';
    go(b2, t, { t0: t0 + .55, from: { s: 0 }, to: { r: 1.5 }, seed: 2 });
    mk.style.strokeDashoffset = L2 * (1 - pr(t, t0 + .9, t0 + 1.4, E.io));
    go(sub, t, { t0: t0 + 1.0, from: { y: 20 }, ease: E.out, idle: .3 }); wipe(sub, t, t0 + 1.0, .5);
    go(sticker, t, { t0: t0 + 1.2, from: { s: 0, r: 30 }, to: { r: 8 }, seed: 3 });
  };
});

/* ---------- 16. وارتبط اسمه قبل ذلك بسلسلة تفجيرات ---------- */
shot(15, 'old', 'U', (cam, t0) => {
  const n1 = newsClip(cam, { head: 'سلسلة تفجيرات', meta: ['عاجل', '1996'], w: 820, h: 520, size: 110, seed: 72, cols: 3 }, { left: '130px', top: '330px' });
  const n2 = newsClip(cam, { head: 'هجمات على حافلات', meta: ['القدس', '—'], w: 560, h: 380, size: 64, seed: 73 }, { left: '60px', top: '960px' });
  const f = frame(cam, { left: '560px', top: '1230px', width: '460px', height: '380px' }, { kind: 'stamp', clip: 'checkpoint', frames: 110, start: t0, freezeAt: t0 + 2.2 });
  const fl = flash(cam);
  return (t) => {
    go(n1, t, { t0: t0, from: { s: 2, r: 12 }, to: { r: -3 }, ease: E.out5, dur: .35, seed: 1 });
    go(n2, t, { t0: t0 + .45, from: { s: 2, r: -12 }, to: { r: 4 }, ease: E.out5, dur: .35, seed: 2 });
    go(f.wrap, t, { t0: t0 + .9, from: { x: 600 }, to: { r: -3 }, seed: 3 }); f.update(t);
    flashAt(fl, t, [t0 + .35, t0 + .8]);
  };
});

/* ---------- 17. استهدفت حافلات في إسرائيل عام 1996 ---------- */
shot(16, 'old', 'R', (cam, t0, t1) => {
  const strip = el(cam, '', { left: 0, top: '300px', width: '2400px', height: '1300px' });  // camera pans across this strip
  const n = newsClip(strip, { head: 'تفجيرات تستهدف حافلات', meta: ['فبراير – مارس 1996', 'إسرائيل'], w: 900, h: 640, size: 92, seed: 81, cols: 3 }, { left: '90px', top: '60px' });
  const places = ['القدس', 'عسقلان', 'تل أبيب'];
  const ps = places.map((p, i) => tape(strip, p, 70, { left: (1140 + i * 330) + 'px', top: (180 + (i % 2) * 160) + 'px' }, i === 1 ? 'red' : 'ink', 82 + i));
  const st = stampEl(strip, '1996', 210, { left: '1250px', top: '640px' });
  const date = el(strip, 'info', { left: '1160px', top: '1000px', fontSize: '50px', color: '#3a3530' }, 'فبراير – مارس');
  return (t) => {
    const pan = kf(t, [[t0 + 1.4, 0], [t0 + 2.4, -1180]], E.expo);
    tf(strip, { x: pan });
    go(n, t, { snd: 'paper', t0: t0, from: { y: 600, r: 8 }, to: { r: -2 }, seed: 1 });
    ps.forEach((p, i) => go(p, t, { t0: t0 + 2.3 + i * .25, from: { s: 0, r: 20 }, to: { r: [-3, 4, -2][i] }, seed: 2 + i }));
    slam(st, t, t0 + 2.45, { r: -7 });
    go(date, t, { t0: t0 + 2.9, from: { y: 20 }, ease: E.out, idle: .3 }); wipe(date, t, t0 + 2.9, .5);
  };
}, { push: .02 });

/* ---------- 18. لم يظهر علنًا تقريبًا ---------- */
shot(17, 'dark', 'Z', (cam, t0) => {
  const fl = flash(cam);
  const fs = [[110, 380, -6], [560, 520, 5], [300, 960, -2]].map(([x, y, r], i) => {
    const f = el(cam, 'polaroid', { left: x + 'px', top: y + 'px', width: '420px', height: '500px' });
    const m = el(f, '', { position: 'relative', width: '100%', height: '100%', background: '#2a2826', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Lalezar', fontSize: '260px', color: '#5e5a54' }, '؟');
    return { f, r };
  });
  const lab = text(cam, 'لم يظهر علنًا', { left: 0, right: 0, top: '1540px', textAlign: 'center', fontSize: '140px' });
  return (t) => {
    fs.forEach(({ f, r }, i) => go(f, t, { t0: t0 + i * .25, from: { s: 1.6, r: r * 3 }, to: { r }, ease: E.out5, dur: .35, seed: i }));
    flashAt(fl, t, [t0 + .05, t0 + .3, t0 + .55, t0 + 1.2]);
    go(lab, t, { t0: t0 + .6, from: { y: 40 }, ease: E.out, idle: .3 }); wipe(lab, t, t0 + .6, .5);
  };
});

/* ---------- 19. واكتفى بتسجيلات صوتية ---------- */
shot(18, 'dark', 'L', (cam, t0) => {
  const box = el(cam, '', { left: '90px', top: '500px', width: '900px', height: '560px', border: '4px solid #f2ede3', boxSizing: 'border-box' });
  const rec = el(box, '', { left: '40px', top: '30px', fontFamily: 'Cairo', fontWeight: 900, fontSize: '46px', color: '#f2ede3', direction: 'ltr' }, '<span class="dot" style="color:#d12f2f">●</span> REC');
  const tc = el(box, '', { right: '40px', top: '30px', fontFamily: 'Plex', fontSize: '42px', color: '#f2ede3', direction: 'ltr' }, '00:00:00');
  const wave = el(box, '', { left: '50px', top: '170px', width: '800px', height: '300px', display: 'flex', alignItems: 'center', gap: '6px' });
  const bars = Array.from({ length: 48 }, (_, i) => el(wave, 'wbar', { position: 'relative', background: i % 7 === 0 ? '#c23030' : '#f2ede3' }));
  const lab = text(cam, 'تسجيلات صوتية', { left: 0, right: 0, top: '320px', textAlign: 'center', fontSize: '120px' });
  const sub = tape(cam, 'صوتٌ بلا صورة', 64, { left: '330px', top: '1150px' }, 'red', 91);
  const dot = rec.querySelector('.dot');
  return (t) => {
    go(box, t, { t0: t0, from: { s: .6 }, seed: 1, idle: .4 });
    const R = rand(Math.round(t * FPS) + 1);
    const amp = pr(t, t0 + .2, t0 + .5);
    bars.forEach((b, i) => { const v = Math.abs(Math.sin(t * 11 + i * .5) * Math.sin(t * 2.7 + i * 1.3)) * .85 + R() * .15; b.style.height = (8 + v * 280 * amp) + 'px'; });
    dot.style.opacity = Math.floor((t - t0) * 2.5) % 2 ? .2 : 1;
    const s = Math.floor((t - t0) * 25); tc.textContent = `00:00:${String(Math.floor(s / 25)).padStart(2, '0')}:${String(s % 25).padStart(2, '0')}`;
    go(lab, t, { t0: t0 + .1, from: { y: -40 }, ease: E.out, idle: .3 }); wipe(lab, t, t0 + .1, .5);
    go(sub, t, { t0: t0 + .7, from: { x: -400 }, to: { r: -2 }, seed: 2 });
  };
});

/* ---------- 20. فصار غيابه جزءًا من صورته ---------- */
shot(19, 'dark', 'U', (cam, t0) => {
  const ring = el(cam, '', { left: '140px', top: '380px', width: '800px', height: '800px', borderRadius: '50%', border: '6px solid #8e1b1b', boxSizing: 'border-box' });
  const p = img(cam, A + 'portrait_main_bw.png', { left: '210px', top: '420px', width: '660px' });
  const silBox = el(cam, '', { left: '190px', top: '430px', width: '700px', height: '700px', borderRadius: '50%', overflow: 'hidden' });
  img(silBox, A + 'silhouette_bw.jpg', { left: 0, top: 0, width: '100%', height: '100%', objectFit: 'cover' });
  const l1 = text(cam, 'غيابه', { left: 0, right: 0, top: '1250px', textAlign: 'center', fontSize: '150px', color: '#a52222' });
  const l2 = text(cam, 'جزءٌ من صورته', { left: 0, right: 0, top: '1420px', textAlign: 'center', fontSize: '120px' });
  return (t) => {
    go(ring, t, { t0: t0, from: { s: .3 }, idle: .3 });
    const x = pr(t, t0 + .5, t0 + 1.6, E.io);
    go(p, t, { t0: t0, from: { s: .8 }, idle: .4, seed: 2 }); p.style.opacity *= 1 - x;
    p.style.webkitMaskImage = `radial-gradient(circle at 50% 40%, #000 ${Math.max(0, 60 - x * 60)}%, transparent ${Math.max(5, 75 - x * 70)}%)`;
    go(silBox, t, { t0: t0 + .5, from: { s: 1.1 }, ease: E.out, idle: .4, seed: 3 }); silBox.style.opacity = x;
    go(l1, t, { t0: t0 + .7, from: { y: 30 }, ease: E.out, idle: .3 }); wipe(l1, t, t0 + .7, .4);
    go(l2, t, { t0: t0 + 1.0, from: { y: 30 }, ease: E.out, idle: .3 }); wipe(l2, t, t0 + 1.0, .5);
  };
});

/* ---------- 21. على مدى أكثر من عشرين عامًا (timeline) ---------- */
shot(20, 'paper', 'L', (cam, t0) => {
  const lane = el(cam, '', { left: 0, top: '820px', width: '3000px', height: '400px' });
  const years = [2001, 2002, 2003, 2006, 2014, 2024];
  const span = y => ({ 2001: 200, 2002: 540, 2003: 880, 2006: 1260, 2014: 1720, 2024: 2240 })[y];
  const line = el(lane, '', { left: '100px', top: '190px', width: '2900px', height: '8px', background: '#1a1816', transformOrigin: 'left center' });
  const ticks = years.map((y, i) => {
    const g = el(lane, '', { left: span(y) + 'px', top: '120px' });
    el(g, '', { left: '-14px', top: '56px', width: '36px', height: '36px', borderRadius: '50%', background: i === 5 ? '#1a1816' : 'var(--red2)', border: '6px solid #e8e2d5' });
    el(g, '', { left: '-80px', top: (i % 2 ? 130 : -90) + 'px', width: '200px', textAlign: 'center', fontFamily: 'Cairo', fontWeight: 900, fontSize: '68px', color: 'var(--ink)' }, String(y));
    return g;
  });
  const big = text(cam, 'أكثر من', { right: '260px', top: '240px', fontSize: '120px', color: 'var(--ink)' });
  const num = el(cam, '', { right: '90px', top: '380px', fontFamily: 'Cairo', fontWeight: 900, fontSize: '260px', lineHeight: 1, color: 'var(--red2)' }, '20');
  const unit = text(cam, 'عامًا', { left: '120px', top: '440px', fontSize: '150px', color: 'var(--ink)' });
  return (t) => {
    tf(line, { sx: pr(t, t0, t0 + 1.8, E.io), sy: 1 });
    tf(lane, { x: kf(t, [[t0 + .2, 80], [t0 + 1.9, -1340]], E.io) });
    ticks.forEach((g, i) => go(g, t, { t0: t0 + [0, .15, .3, .7, 1.1, 1.5][i], from: { s: 0 }, idle: 0 }));
    go(big, t, { t0: t0, from: { y: -30 }, ease: E.out, idle: .3 }); wipe(big, t, t0, .4);
    go(num, t, { t0: t0 + .2, from: { s: 1.8 }, ease: E.out5, idle: .3 }); num.textContent = String(Math.round(pr(t, t0 + .2, t0 + 1.2) * 20));
    go(unit, t, { t0: t0 + .4, from: { x: -60 }, ease: E.out, idle: .3 });
  };
}, { push: .02 });

/* ---------- 22. نجا من عدة محاولات اغتيال إسرائيلية ---------- */
shot(21, 'dark', 'U', (cam, t0, t1) => {
  const bg = frame(cam, { left: '-40px', top: '200px', width: '1160px', height: '900px' }, { kind: 'torn', clip: 'armor', frames: 125, start: t0, seed: 101 });
  bg.wrap.style.filter = 'brightness(.35) blur(2px)';
  const head = text(cam, 'محاولات اغتيال', { left: 0, right: 0, top: '330px', textAlign: 'center', fontSize: '130px' });
  const years = ['2001', '2002', '2003', '2006', '2014'];
  const cards = years.map((y, i) => {
    const c = el(cam, 'acard', { left: '230px', top: (720 + i * 26) + 'px' });
    el(c, 'y', { position: 'relative' }, y);
    el(c, 'l', { position: 'relative' }, 'محاولة اغتيال');
    const s = stampEl(c, 'نجا', 110, { left: '40px', top: '60px' });
    return { c, s };
  });
  const count = el(cam, '', { left: '90px', top: '1500px', fontFamily: 'Cairo', fontWeight: 900, fontSize: '140px', color: '#f2ede3', direction: 'ltr' }, '');
  const beats = years.map((_, i) => t0 + .25 + i * .5);
  return (t) => {
    bg.update(t); go(bg.wrap, t, { t0: t0, from: { s: 1.15 }, ease: E.out, idle: 0 });
    go(head, t, { t0: t0, from: { y: -60 }, ease: E.out5, idle: .3 }); wipe(head, t, t0, .45);
    const R = rand(Math.round(t * FPS) + 3);
    cards.forEach(({ c, s }, i) => {
      const rr = [-6, 5, -3, 7, -2][i];
      go(c, t, { snd: 'paper', t0: beats[i], from: { y: -1300, r: rr * 4 }, to: { r: rr, x: (i % 2 ? 40 : -40) }, ease: E.out5, dur: .32, idle: .4, seed: i });
      slam(s, t, beats[i] + .22, { r: -12, from: 2.6 });
    });
    const n = beats.filter(b => t >= b).length;
    count.textContent = n ? '×' + n : ''; go(count, t, { t0: beats[0], from: { s: 0 }, idle: 0 });
    cam.style.translate = beats.some(b => t >= b + .3 && t < b + .4) ? `${(R() - .5) * 22}px ${(R() - .5) * 22}px` : '0 0';
  };
}, { push: .02 });

/* ---------- 23. وأُصيب في بعضها إصابات بالغة ---------- */
shot(22, 'paper', 'R', (cam, t0) => {
  // the portrait photo rips in two along a jagged line
  const R0 = rand(5), pts = [];
  for (let k = 0; k <= 16; k++) pts.push([48 + (R0() - .5) * 10 + (k / 16 - .5) * 12, k / 16 * 100]);
  const left = 'polygon(0 0,' + pts.map(p => `${p[0]}% ${p[1]}%`).join(',') + ',0 100%)';
  const right = 'polygon(100% 0,' + pts.map(p => `${p[0]}% ${p[1]}%`).join(',') + ',100% 100%)';
  const halves = [left, right].map(cp => {
    const h = el(cam, 'pwrap', { left: '190px', top: '440px', width: '700px', height: '820px' });
    const pol = el(h, 'polaroid', { position: 'relative' });
    const m = el(pol, 'media', { position: 'relative', background: '#cfc8ba' });
    img(m, A + 'portrait_interview_bw.png', { inset: 0, width: '100%', height: '100%', objectFit: 'contain', objectPosition: '50% 80%' });
    pol.style.clipPath = cp;
    return h;
  });
  sfx('rip', t0 + .6);
  const lab = tape(cam, 'إصابات بالغة', 90, { left: '270px', top: '1380px' }, 'red', 111);
  const head = text(cam, 'أُصيب', { right: '270px', top: '200px', fontSize: '170px', color: 'var(--ink)' });
  return (t) => {
    const sp = pr(t, t0 + .6, t0 + .95, E.out5);
    go(halves[0], t, { t0: t0, from: { y: 500, r: 10 }, to: { r: -2 }, seed: 1, idle: .5 }); halves[0].style.translate = `${-sp * 60}px ${sp * 20}px`; halves[0].style.rotate = `${-sp * 5}deg`;
    go(halves[1], t, { t0: t0, from: { y: 500, r: 10 }, to: { r: -2 }, seed: 1, idle: .5 }); halves[1].style.translate = `${sp * 60}px ${-sp * 10}px`; halves[1].style.rotate = `${sp * 4}deg`;
    go(lab, t, { t0: t0 + .8, from: { s: 0, r: 15 }, to: { r: -4 }, seed: 2 });
    go(head, t, { t0: t0 + .1, from: { y: -40 }, ease: E.out, idle: .3 }); wipe(head, t, t0 + .1, .4);
  };
});

/* ---------- 24. ومع كل محاولة (fast montage) ---------- */
shot(23, 'dark', 'Z', (cam, t0, t1) => {
  const years = ['2001', '2002', '2003', '2006', '2014'];
  const items = years.map((y, i) => el(cam, '', { left: 0, right: 0, top: '700px', textAlign: 'center', fontFamily: 'Cairo', fontWeight: 900, fontSize: '360px', color: i % 2 ? 'var(--red2)' : '#f2ede3', lineHeight: 1 }, y));
  const lab = text(cam, 'ومع كل محاولة', { left: 0, right: 0, top: '1250px', textAlign: 'center', fontSize: '110px' });
  return (t) => {
    const k = Math.min(years.length - 1, Math.floor((t - t0) / ((t1 - t0) / years.length)));
    items.forEach((n, i) => tf(n, { s: i === k ? 1 + (t - t0) * .15 : 1, o: i === k ? 1 : 0 }));
    go(lab, t, { t0: t0 + .1, from: { y: 30 }, ease: E.out, idle: .3 }); wipe(lab, t, t0 + .1, .4);
  };
}, { push: .08 });

/* ---------- 25. كان يعود إلى الظل من جديد ---------- */
shot(24, 'dark', 'F', (cam, t0, t1) => {
  const p = img(cam, A + 'portrait_main_bw.png', { left: '240px', top: '420px', width: '600px' });
  const dark = el(cam, '', { inset: 0, background: 'radial-gradient(circle at 50% 38%, transparent 0, transparent 18%, #0d0c0b 42%)' });
  const lab = text(cam, 'يعود إلى الظل', { left: 0, right: 0, top: '1300px', textAlign: 'center', fontSize: '150px' });
  return (t) => {
    go(p, t, { t0: t0, from: { s: 1.1 }, ease: E.out, idle: .4 });
    p.style.filter = `brightness(${lerp(1, .12, pr(t, t0 + .3, t1, E.io))})`;
    dark.style.opacity = pr(t, t0, t0 + .8);
    go(lab, t, { t0: t0 + .2, from: { y: 30 }, ease: E.out, idle: .3 }); wipe(lab, t, t0 + .2, .6);
  };
});

/* calendar page used by the July / January shots */
function calendar(cam, t0, month, day, year, seed) {
  const back = el(cam, 'cal', { left: '260px', top: '560px' }, `<div class="top">${month}</div><div class="day">${day - 1}</div><div class="yr">${year}</div>`);
  const page = el(cam, 'cal', { left: '260px', top: '560px', transformOrigin: '50% 0' }, `<div class="top">${month}</div><div class="day">${day}</div><div class="yr">${year}</div>`);
  page.querySelector('.day').textContent = day;
  const prev = el(cam, 'cal', { left: '260px', top: '560px', transformOrigin: '50% 0' }, `<div class="top">${month}</div><div class="day">${day - 1}</div><div class="yr">${year}</div>`);
  back.style.visibility = 'hidden';
  sfx('paper', t0); sfx('rip', t0 + .7);
  return (t) => {
    go(page, t, { t0: t0, from: { y: -1300 }, ease: E.out5, dur: .45, idle: .3, seed });
    go(prev, t, { t0: t0, from: { y: -1300 }, ease: E.out5, dur: .45, idle: .3, seed });
    const tear = pr(t, t0 + .7, t0 + 1.3, E.in);
    prev.style.transform += ` translate(${tear * 260}px,${tear * 1300}px) rotate(${tear * 35}deg)`;
    prev.style.opacity = t < t0 ? 0 : 1 - pr(t, t0 + 1.1, t0 + 1.3);
  };
}

/* ---------- 26. في يوليو 2024 ---------- */
shot(25, 'paper', 'U', (cam, t0) => {
  const cal = calendar(cam, t0, 'يوليو', 13, 2024, 3);
  const lab = text(cam, 'في يوليو', { right: '270px', top: '220px', fontSize: '150px', color: 'var(--ink)' });
  const c = cloud(cam, 1, { left: '220px', top: '1080px' });
  return (t) => {
    cal(t);
    go(lab, t, { t0: t0, from: { y: -30 }, ease: E.out, idle: .3 }); wipe(lab, t, t0, .45);
    go(c, t, { t0: t0 + .3, from: { y: 80 }, idle: 1.5, seed: 4 });
  };
});

/* ---------- 27. أعلنت إسرائيل أنها قتلته في غارة على المواصي ---------- */
shot(26, 'old', 'L', (cam, t0) => {
  const f = frame(cam, { left: '70px', top: '420px', width: '940px', height: '760px' }, { kind: 'stamp', clip: 'ruins', frames: 57, start: t0 + .1, speed: .6, freezeAt: t0 + 3.6 });
  const lab = tape(cam, 'غارة على المواصي', 76, { right: '70px', top: '1240px' }, 'red', 121);
  const lab2 = tape(cam, 'خان يونس', 54, { left: '90px', top: '1370px' }, 'ink', 122);
  const c1 = smoke(cam, 0, { left: '-120px', top: '180px', width: '760px' });
  const c2 = smoke(cam, 1, { left: '480px', top: '120px', width: '720px' });
  const head = text(cam, 'إعلان إسرائيلي', { right: '260px', top: '210px', fontSize: '112px', color: 'var(--ink)' });
  return (t) => {
    go(f.wrap, t, { t0: t0, from: { s: .7, r: -10 }, to: { r: -2 }, seed: 1 }); f.update(t);
    go(c1, t, { t0: t0 + .2, from: { x: -400 }, idle: 1.8, seed: 2 });
    go(c2, t, { t0: t0 + .3, from: { x: 400 }, idle: 1.8, seed: 3 });
    go(lab, t, { t0: t0 + 2.9, from: { x: 400 }, to: { r: -2 }, seed: 4, snd: 'paper' });
    go(lab2, t, { t0: t0 + 3.85, from: { s: 0 }, to: { r: 3 }, seed: 5 });
    go(head, t, { t0: t0 + .1, from: { y: -30 }, ease: E.out, idle: .3 }); wipe(head, t, t0 + .1, .5);
  };
});

/* ---------- 28. خلال الحرب التي أعقبت هجوم السابع من أكتوبر ---------- */
shot(27, 'old', 'U', (cam, t0) => {
  const n = newsClip(cam, { head: 'الحرب في غزة', meta: ['2023 – 2025', ''], w: 860, h: 640, size: 120, seed: 131, cols: 3 }, { left: '110px', top: '480px' });
  const span = el(cam, '', { left: '150px', top: '1250px', width: '780px', height: '150px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', direction: 'ltr', fontFamily: 'Cairo', fontWeight: 900, fontSize: '96px', color: 'var(--ink)' }, '<span>2023</span><span style="flex:1;height:8px;background:#a52222;margin:0 30px"></span><span>2025</span>');
  const cs = [0, 1, 0].map((k, j) => smoke(cam, k, { left: (j * 340 - 140) + 'px', top: (900 + (j % 2) * 120) + 'px', width: '640px' }));
  return (t) => {
    go(n, t, { snd: 'paper', t0: t0, from: { y: -800, r: -12 }, to: { r: -2 }, seed: 1 });
    go(span, t, { t0: t0 + .5, from: { s: .3 }, idle: .3, seed: 2 });
    cs.forEach((c, i) => go(c, t, { t0: t0 + .2 + i * .2, from: { y: 260, s: .8 }, to: { y: -(t - t0) * 60 }, ease: E.out, dur: 1.2, idle: 2, seed: 3 + i }));
  };
});

/* ---------- 29. وفي يناير 2025 ---------- */
shot(28, 'paper', 'R', (cam, t0) => {
  const cal = calendar(cam, t0, 'يناير', 30, 2025, 6);
  const lab = text(cam, 'وفي يناير', { right: '270px', top: '220px', fontSize: '150px', color: 'var(--ink)' });
  return (t) => { cal(t); go(lab, t, { t0: t0, from: { y: -30 }, ease: E.out, idle: .3 }); wipe(lab, t, t0, .45); };
});

/* ---------- 30. أكّدت حماس مقتله ---------- */
shot(29, 'old', 'U', (cam, t0, t1) => {
  const card = el(cam, 'news', { left: '120px', top: '640px', width: '840px', height: '480px', boxSizing: 'border-box', padding: '40px 50px' });
  card.style.clipPath = tornPoly(141, 1.3);
  el(card, 'meta', { position: 'relative', fontSize: '28px' }, '<span>بيان</span><span>30 يناير 2025</span>');
  const msg = el(card, 'info', { position: 'relative', fontSize: '100px', fontWeight: 600, lineHeight: 1.6 }, '');
  const full = 'حماس تؤكد مقتله';
  for (let k = 0; k < full.length; k++) sfx('type', t0 + .25 + (t1 - .45 - t0) * k / full.length, .6);
  const st = stampEl(cam, 'بيان رسمي', 86, { left: '150px', top: '1200px' }, true);
  const br = img(cam, A + 'brush.png', { left: '100px', top: '760px', width: '880px', opacity: .0 });
  card.parentNode.insertBefore(br, card);
  return (t) => {
    go(card, t, { snd: 'paper', t0: t0, from: { y: 600, r: 6 }, to: { r: -1.5 }, ease: E.out5, dur: .4, seed: 1 });
    const n = Math.floor(pr(t, t0 + .25, t1 - .2, E.lin) * full.length);
    msg.textContent = full.slice(0, n) + (Math.floor(t * 4) % 2 ? '|' : ' ');
    slam(st, t, t0 + .5, { r: -8 });
    go(br, t, { t0: t0 + .15, from: { sx: 0 }, idle: 0 }); br.style.transform = `scaleX(${pr(t, t0 + .15, t0 + .5, E.io)}) rotate(-2deg)`; br.style.transformOrigin = 'right center';
  };
});

/* ---------- 31. end card ---------- */
shot(30, 'dark', 'F', (cam, t0, t1) => {
  sfx('boom', t0 + .1, .8);
  const name = text(cam, 'محمد الضيف', { left: 0, right: 0, top: '820px', textAlign: 'center', fontSize: '190px' });
  const line = el(cam, '', { left: '390px', top: '1030px', width: '300px', height: '6px', background: 'var(--red)' });
  const dates = el(cam, '', { left: 0, right: 0, top: '1070px', textAlign: 'center', fontFamily: 'Cairo', fontSize: '60px', color: '#a49e93', letterSpacing: '6px' }, '1965 – 2024');
  const black = el(cam, '', { inset: '-200px', background: '#000' });
  return (t) => {
    go(name, t, { t0: t0 + .1, from: { y: 30 }, ease: E.out, dur: .9, idle: .2 }); wipe(name, t, t0 + .1, .9);
    tf(line, { sx: pr(t, t0 + .6, t0 + 1.4, E.io), sy: 1 });
    go(dates, t, { t0: t0 + 1.0, from: { y: 20 }, ease: E.out, dur: .8, idle: .2 });
    tf(black, { o: pr(t, t1 - 1.6, t1 - .3, E.io) });
  };
}, { push: .03 });

/* ---------- 32. outro: the channel logo animates in the centre ---------- */
shot(31, 'paper', 'F', (cam, t0, t1) => {
  sfx('swell', t0 + .1, .7);
  const logo = img(cam, A + 'logo/c_000.png', { left: '310px', top: '500px', width: '460px' });
  const black = el(cam, '', { inset: '-200px', background: '#000' });
  let cur = -1;
  return (t) => {
    const f = Math.min(166, Math.max(0, Math.floor((t - t0 - .3) * FPS)));
    if (f !== cur) { cur = f; logo.src = `${A}logo/c_${String(f).padStart(3, '0')}.png`; pending.push(logo.decode().catch(() => { })); }
    tf(logo, { s: kf(t, [[t0, .96], [t1, 1.02]], E.lin) });
    tf(black, { o: pr(t, t1 - .5, t1, E.io) });
  };
}, { push: 0 });

/* ================= global layers ================= */
// foreground bokeh / dust drifting in parallax with camera moves
const bokLayer = el(stage, '', { inset: 0, zIndex: 40, pointerEvents: 'none' });
const BR = rand(777);
const boks = Array.from({ length: 18 }, (_, i) => {
  const big = i < 4, d = big ? 50 + BR() * 70 : 5 + BR() * 9;
  const n = el(bokLayer, 'bok', { width: d + 'px', height: d + 'px', background: big ? (i % 2 ? 'rgba(165,34,34,.32)' : 'rgba(232,226,213,.3)') : 'rgba(242,237,227,.55)', filter: `blur(${big ? 10 + BR() * 8 : 1}px)` });
  return { n, x: BR() * W, y: BR() * H, depth: big ? 1.4 + BR() : .4 + BR() * .5, sp: .5 + BR(), ph: BR() * 6 };
});
// channel logo, top corner for the whole video: plays its reveal animation (GIF frames at 25 fps) then holds.
// navy on paper shots, white on dark shots
const LOGO_FRAMES = 167, LOGO_CSS = { right: '44px', top: '44px', width: '150px', zIndex: 60 };
const logoC = img(stage, A + 'logo/c_000.png', LOGO_CSS), logoW = img(stage, A + 'logo/w_000.png', LOGO_CSS);
const grain = img(stage, A + 'grain_0.png', { left: 0, top: 0, width: W + 'px', height: H + 'px', mixBlendMode: 'overlay', zIndex: 50 });
el(stage, 'overlay', { background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,.45) 100%)', zIndex: 51 });
const mbx = document.getElementById('mbxg'), mby = document.getElementById('mbyg');

const DIRS = { L: [1, 0], R: [-1, 0], U: [0, 1], D: [0, -1] };
function transP(s, t) { return s.i === 0 ? 1 : pr(t, s.t0, s.t0 + TR, E.expo); }

window.seek = async (t) => {
  pending.length = 0;
  const cur = shots.findIndex(s => t >= s.t0 && t < s.t1);
  const i = cur < 0 ? shots.length - 1 : cur;
  const s = shots[i], prev = shots[i - 1];
  const p = transP(s, t);
  const v = s.i === 0 ? 0 : (transP(s, t + .02) - transP(s, t - .02)) / .04; // transition speed
  let camX = 0, camY = 0;
  shots.forEach(sh => { sh.root.style.display = 'none'; });
  const place = (sh, x, y, sc, o, blurAxis) => {
    sh.root.style.display = 'block';
    sh.root.style.transform = `translate(${x}px,${y}px) scale(${sc})`;
    sh.root.style.opacity = o;
    sh.root.style.filter = blurAxis ? `url(#mb${blurAxis})` : '';
    const lt = (t - sh.t0) / Math.max(.1, sh.t1 - sh.t0);
    sh.cam.style.transform = `scale(${1 + sh.push * clamp(lt, 0, 1.3)})`;
    sh.cam.style.translate = '0 0';
    sh.update(t, sh);
  };
  const blur = Math.min(60, v * 9);
  if (p < 1 && prev) {
    const e = s.enter;
    if (DIRS[e]) {
      const [dx, dy] = DIRS[e], ax = dx ? 'x' : 'y';
      place(prev, -dx * W * p, -dy * H * p, 1, 1, ax);
      place(s, dx * W * (1 - p), dy * H * (1 - p), 1, 1, ax);
      (ax === 'x' ? mbx : mby).setAttribute('stdDeviation', ax === 'x' ? `${blur} 0` : `0 ${blur}`);
      camX = -dx * p; camY = -dy * p;
    } else if (e === 'Z') {
      place(prev, 0, 0, 1 + p * 2.2, 1 - p, null);
      place(s, 0, 0, lerp(.55, 1, p), clamp(p * 1.6), null);
    } else {
      const q = pr(t, s.t0, s.t0 + .7, E.io);
      place(prev, 0, 0, 1, 1, null); place(s, 0, 0, 1, q, null);
    }
  } else place(s, 0, 0, 1, 1, null);
  if (!(p < 1 && DIRS[s.enter])) { mbx.setAttribute('stdDeviation', '0 0'); mby.setAttribute('stdDeviation', '0 0'); }

  // bokeh: slow drift + extra slide with the camera pan
  const done = shots.slice(1, i + (p >= 1 ? 1 : 0)).reduce((a, sh) => { const d = DIRS[sh.enter]; if (d) { a[0] -= d[0]; a[1] -= d[1]; } return a; }, [0, 0]);
  const gx = (done[0] + camX) * 420, gy = (done[1] + camY) * 420;
  boks.forEach(b => {
    const x = ((b.x + gx * b.depth + Math.sin(t * .3 * b.sp + b.ph) * 40) % (W + 200) + W + 200) % (W + 200) - 100;
    const y = ((b.y + gy * b.depth - t * 18 * b.sp) % (H + 200) + H + 200) % (H + 200) - 100;
    b.n.style.transform = `translate(${x}px,${y}px)`;
  });
  grain.src = `${A}grain_${Math.floor(t * FPS) % 6}.png`;
  const lf = String(Math.min(LOGO_FRAMES - 1, Math.floor(t * FPS))).padStart(3, '0');
  logoC.src = `${A}logo/c_${lf}.png`; logoW.src = `${A}logo/w_${lf}.png`;
  pending.push(logoC.decode().catch(() => { }), logoW.decode().catch(() => { }));
  const isDark = sh => sh.root.classList.contains('bg-dark') ? 1 : 0;
  const dark = p < 1 && prev ? lerp(isDark(prev), isDark(s), p) : isDark(s);
  const hide = 1 - pr(t, C[31] - 1.4, C[31] - .8);
  logoW.style.opacity = dark * hide; logoC.style.opacity = (1 - dark) * hide;
  pending.push(grain.decode().catch(() => { }));
  await Promise.all(pending);
};

window.ready = (async () => {
  window.MAP = await (await fetch(A + 'map.json')).json();
  await document.fonts.ready;
  await Promise.all([...document.images].map(i => i.decode().catch(() => { })));
  window.DURATION = DURATION; window.FPS = FPS; window.SFX = SFX;
  return true;
})();
