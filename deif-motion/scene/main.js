/* محمد الضيف | رجل الظل — deterministic collage animation.
   window.seek(t) renders the frame at time t (seconds). render.mjs drives it frame by frame. */
const W = 1080, H = 1920, FPS = 25, DURATION = 76;
const A = '../assets/', CLIPS = '../build/clips/';
const stage = document.getElementById('stage');

/* ---------- helpers ---------- */
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const lerp = (a, b, p) => a + (b - a) * p;
const E = {
  lin: p => p,
  out: p => 1 - Math.pow(1 - p, 3),
  in: p => p * p * p,
  io: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
  back: p => { const c = 1.6; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); },
};
// progress of t inside [a,b], eased
const pr = (t, a, b, e = E.out) => e(clamp((t - a) / (b - a)));
// keyframes: [[t,v],...]
function kf(t, keys, e = E.io) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const [t0, v0] = keys[i - 1], [t1, v1] = keys[i];
      return lerp(v0, v1, e((t - t0) / (t1 - t0)));
    }
  }
  return keys[keys.length - 1][1];
}
function rand(seed) { // mulberry32
  let a = seed >>> 0;
  return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
function el(parent, cls = '', css = {}, html = '') {
  const d = document.createElement('div');
  if (cls) d.className = cls;
  Object.assign(d.style, css);
  if (html) d.innerHTML = html;
  parent.appendChild(d);
  return d;
}
function img(parent, src, css = {}, cls = '') {
  const i = document.createElement('img');
  i.src = src; if (cls) i.className = cls;
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
// torn-paper polygon in % (jagged on every side)
function tornPoly(seed, jag = 1.6, steps = 26) {
  const R = rand(seed), pts = [];
  const j = () => (R() * jag);
  for (let i = 0; i <= steps; i++) pts.push([i / steps * 100, j()]);
  for (let i = 0; i <= steps; i++) pts.push([100 - j(), i / steps * 100]);
  for (let i = steps; i >= 0; i--) pts.push([i / steps * 100, 100 - j()]);
  for (let i = steps; i >= 0; i--) pts.push([j(), i / steps * 100]);
  return `polygon(${pts.map(p => `${p[0].toFixed(2)}% ${p[1].toFixed(2)}%`).join(',')})`;
}
// tear reveal: everything above a jagged, slightly tilted line is visible
function tearReveal(p, seed, tilt = 120) {
  const R = rand(seed), N = 34, pts = [];
  const base = lerp(-tilt - 60, H + tilt + 60, p);
  pts.push([0, 0], [W, 0]);
  for (let i = N; i >= 0; i--) {
    const x = i / N * W;
    pts.push([x, base + (x / W - .5) * tilt * 2 + (R() - .5) * 46]);
  }
  return `polygon(${pts.map(q => `${q[0].toFixed(1)}px ${q[1].toFixed(1)}px`).join(',')})`;
}

/* ---------- reusable components ---------- */
const pending = [];
function clipPlayer(parent, name, frames, css, { seed = 1, speed = 1, start = 0, freezeAt = null, pad = 16, tilt = 0 } = {}) {
  const box = el(parent, 'abs clip', Object.assign({ padding: pad + 'px' }, css));
  box.style.clipPath = tornPoly(seed, 1.2);
  const im = img(box, `${CLIPS}${name}/0001.jpg`, { position: 'relative', width: '100%', height: '100%', objectFit: 'cover' });
  let cur = 1;
  return {
    box, im,
    update(t) { // t = global time
      let lt = t - start;
      if (freezeAt !== null) lt = Math.min(lt, freezeAt - start);
      const f = clamp(Math.floor(lt * FPS * speed) + 1, 1, frames);
      if (f !== cur) {
        cur = f; im.src = `${CLIPS}${name}/${String(f).padStart(4, '0')}.jpg`;
        pending.push(im.decode().catch(() => { }));
      }
      // freeze-frame turns into a printed photo: warmer, more contrast
      const fz = freezeAt !== null ? pr(t, freezeAt, freezeAt + .5) : 0;
      im.style.filter = `contrast(${1.15 + fz * .25}) brightness(${.98 + fz * .06}) sepia(${fz * .35})`;
    }
  };
}
function newsClip(parent, { head, meta = ['', ''], cols = 2, w = 420, h = 360, size = 44, seed = 3, redact = [] }, css = {}) {
  const n = el(parent, 'abs news', Object.assign({ width: w + 'px', height: h + 'px' }, css));
  n.style.clipPath = tornPoly(seed, 2.2);
  el(n, 'meta', {}, `<span>${meta[0]}</span><span>${meta[1]}</span>`);
  if (head) { const hh = document.createElement('h3'); hh.style.fontSize = size + 'px'; hh.innerHTML = head; n.appendChild(hh); }
  const c = el(n, 'cols', { gridTemplateColumns: `repeat(${cols},1fr)`, height: `calc(100% - ${head ? size * 1.3 + 70 : 60}px)` });
  for (let i = 0; i < cols; i++) el(c, '', {}, '<i></i>');
  redact.forEach(([x, y, rw, rh]) => el(n, 'abs redact', { left: x + '%', top: y + '%', width: rw + '%', height: rh + 'px' }));
  return n;
}
function stamp(parent, text, size, css = {}, cls = 'stamp') {
  return el(parent, 'abs ' + cls, Object.assign({ fontSize: size + 'px' }, css), text);
}
// slam-in animation: big -> normal with slight rotation, then settle
function slam(node, t, t0, { r = -6, x = 0, y = 0, from = 2.2 } = {}) {
  const p = pr(t, t0, t0 + .28, E.in);
  const settle = pr(t, t0 + .28, t0 + .6, E.out);
  const s = t < t0 ? from : lerp(from, 1, p) * (1 + .04 * Math.sin(settle * Math.PI));
  tf(node, { x, y, s, r, o: t < t0 ? 0 : clamp(p * 3) });
}
function words(parent, text, css = {}, cls = 'title rtl') {
  const wrap = el(parent, 'abs ' + cls, Object.assign({ display: 'flex', gap: '0.25em', flexDirection: 'row' }, css));
  const ws = text.split(' ').map(w => el(wrap, '', { display: 'inline-block' }, w));
  return { wrap, ws };
}

/* ---------- scenes ---------- */
const scenes = [];
function scene(start, end, cls, build, transIn = null) {
  const root = el(stage, 'scene ' + cls);
  const s = { start, end, root, transIn };
  s.update = build(root, s);
  scenes.push(s);
}
/* Cue points (seconds) aligned to sources/voiceover.mp3 — see tools/align_vo.py.
   Shift a value here to move every animation tied to that line of the VO. */
const C = {
  // 1 — الاسم بلا وجه
  news: 1.36, face: 3.67, few: 5.6, voice: 6.78,
  // 2 — البدايات
  s2: 8.45, born: 8.62, y65: 11.3, camp: 13.57, south: 15.73, uni: 17.35, joined: 19.51, arrest: 22.15, y89: 24.1,
  // 3 — من الظل
  s3: 26.0, y02: 26.2, lead: 27.66, wing: 29.73, buses: 31.6, y96: 36.4, hidden: 39.45, audio: 41.26, absent: 43.35,
  // 4 — المطاردة
  s4: 45.5, years: 45.72, attempts: 47.72, hurt: 50.66, each: 52.06, back: 53.19,
  // 5 — الإعلان
  s5: 54.35, jul: 54.6, mawasi: 56.59, war: 59.1, jan: 61.79, conf: 63.82,
  // 6 — رحل كما عاش
  s6: 64.9, lived: 64.9, faceless: 67.43, left: 70.08, name: 71.9, end: 76,
};

/* SCENE 1 — الاسم بلا وجه */
scene(0, C.s2 + .8, 'bg-dark', (root) => {
  const numsR = rand(11), rows = [];
  for (let i = 0; i < 24; i++) {
    const txt = Array.from({ length: 6 }, () => ['1965', '1989', '1996', '2002', '2014', '31.34°N', '34.30°E', '07:42', 'NO.' + Math.floor(numsR() * 900 + 100)][Math.floor(numsR() * 9)]).join('   ·   ');
    rows.push(el(root, 'abs mono', { left: '-40px', top: (i * 86) + 'px', fontSize: '26px', whiteSpace: 'nowrap', color: '#3b3732' }, txt));
  }
  const staticLayer = el(root, 'full');
  const bars = Array.from({ length: 14 }, () => el(staticLayer, 'abs', { left: 0, width: W + 'px', background: '#d8d2c6' }));

  const n1 = newsClip(root, { head: 'من هو؟', meta: ['أرشيف', '—'], w: 430, h: 420, size: 60, seed: 21, redact: [[8, 42, 70, 26], [20, 62, 60, 26]] }, { left: '40px', top: '140px' });
  const n2 = newsClip(root, { head: '<span class="redact" style="color:transparent">الاسم الكامل</span>', meta: ['ملف', '???'], w: 380, h: 330, size: 46, seed: 22, cols: 2, redact: [[10, 70, 50, 22]] }, { left: '650px', top: '220px' });
  const n3 = newsClip(root, { head: 'صورة نادرة', meta: ['—', '—'], w: 400, h: 300, size: 50, seed: 23, redact: [[30, 50, 60, 24]] }, { left: '60px', top: '1380px' });
  const n4 = newsClip(root, { head: '', meta: ['أرشيف', 'رقم 07'], w: 360, h: 380, seed: 24, cols: 2, redact: [[5, 30, 80, 30], [5, 55, 50, 30]] }, { left: '680px', top: '1330px' });

  const frame = el(root, 'abs clip', { left: '150px', top: '520px', width: '780px', height: '780px', padding: '18px' });
  frame.style.clipPath = tornPoly(31, 1.1);
  const sil = img(frame, A + 'silhouette_bw.jpg', { position: 'relative', width: '100%', height: '100%', objectFit: 'cover' });

  const redBar = el(root, 'abs', { left: '90px', top: '1225px', width: '900px', height: '150px', background: 'var(--red)', transformOrigin: 'right center' });
  const name = words(root, 'محمد الضيف', { right: '0', left: '0', top: '1180px', justifyContent: 'center', fontSize: '200px' });
  const sub = el(root, 'abs tape', { left: '330px', top: '1430px', fontSize: '74px' }, 'رجل الظل');
  sub.style.clipPath = tornPoly(41, 2.5);

  return (t) => {
    const fr = Math.round(t * FPS);
    rows.forEach((r, i) => tf(r, { x: ((i % 2 ? -1 : 1) * t * 14) - (i % 2 ? 0 : 120), y: -t * 6, o: kf(t, [[0, 0], [1.2, .9], [7.5, .9], [9, .5]]) }));
    const R = rand(fr * 7 + 3);
    const burst = t < 1.2 ? 1 : (Math.abs(t - C.few) < .12 || Math.abs(t - C.voice) < .08) ? .7 : 0;
    bars.forEach(b => { b.style.top = (R() * H) + 'px'; b.style.height = (2 + R() * 30) + 'px'; b.style.opacity = burst * R() * .5; });
    root.style.filter = `brightness(${t < 1.2 ? .4 + R() * .6 : 1})`;

    const drift = (n, t0, dx, dy, r) => tf(n, { x: dx * (1 - pr(t, t0, t0 + 1.0)) + t * 3, y: dy * (1 - pr(t, t0, t0 + 1.0)) - t * 4, r, o: pr(t, t0, t0 + .35) * kf(t, [[C.few - .3, 1], [C.few + .4, .45]]) });
    drift(n1, C.news, -500, -80, -7); drift(n2, C.news + .35, 500, -60, 6); drift(n3, C.news + .7, -500, 80, 4); drift(n4, C.news + 1.05, 500, 60, -5);

    const flick = t < C.face + 1.5 ? (R() > .25 ? 1 : .5) : 1;
    tf(frame, { s: kf(t, [[C.face, 1.1], [C.few, 1], [9, .97]]), y: kf(t, [[C.few - .4, 0], [C.few + .4, -160]]), r: -1.5, o: pr(t, C.face, C.face + 1.4, E.io) * flick });
    sil.style.filter = `contrast(1.2) brightness(${kf(t, [[C.face, .2], [C.face + 1.8, 1]])})`;

    name.ws.forEach((w, i) => slam(w, t, C.few + i * .22, { r: 0, from: 1.8 }));
    tf(redBar, { sx: pr(t, C.few - .15, C.few + .35, E.io), sy: 1, o: 1 });
    tf(sub, { x: 140 * (1 - pr(t, C.voice + .2, C.voice + .7)), r: -3, o: pr(t, C.voice + .2, C.voice + .5) });
  };
});

/* SCENE 2 — البدايات */
scene(C.s2, C.s3 + .8, 'bg-paper', (root) => {
  const head = el(root, 'abs tape ink', { right: '60px', top: '90px', fontSize: '46px' }, 'البدايات');
  const mapWrap = el(root, 'abs', { left: '60px', top: '150px', width: '700px', height: '1200px' });
  mapWrap.innerHTML = `<svg width="700" height="1200" viewBox="0 0 700 1200" style="overflow:visible">
    <path id="mo" fill="#cfc6b4" stroke="#1a1816" stroke-width="3.5" stroke-linejoin="round"/>
    <path id="mg" fill="#8e1b1b" stroke="#1a1816" stroke-width="2"/>
    <circle id="ky" r="9" fill="#f2ede3" stroke="#8e1b1b" stroke-width="4"/>
    <circle id="kr" r="9" fill="none" stroke="#8e1b1b" stroke-width="3"/></svg>`;
  const mapLabel = el(root, 'abs tape red', { left: '120px', top: '780px', fontSize: '50px' }, 'مخيم خان يونس');
  mapLabel.style.clipPath = tornPoly(52, 2.5);
  const mapSub = el(root, 'abs info', { left: '130px', top: '880px', fontSize: '34px', color: '#3a3530' }, 'جنوبي قطاع غزة');
  const s65 = stamp(root, '1965', 170, { left: '560px', top: '280px' });
  const card = el(root, 'abs news', { left: '480px', top: '1240px', width: '540px', height: '330px', padding: '30px 36px' });
  card.style.clipPath = tornPoly(53, 1.5);
  card.innerHTML = `<div class="meta"><span>ملف أرشيفي</span><span>رقم 1965/08</span></div>
    <div class="info" style="font-size:30px;line-height:1.9">الاسم: محمد دياب إبراهيم المصري<br>المواليد: 1965<br>المكان: مخيم خان يونس للاجئين</div>`;
  const camp = clipPlayer(root, 'camp', 175, { left: '50px', top: '1270px', width: '520px', height: '440px' }, { seed: 61, start: C.camp, speed: .8 });
  const campTag = el(root, 'abs tape', { left: '90px', top: '1690px', fontSize: '36px' }, 'المخيم');
  const uni = clipPlayer(root, 'university', 225, { left: '90px', top: '210px', width: '900px', height: '720px' }, { seed: 62, start: C.uni, speed: .9, freezeAt: C.arrest - .5 });
  const uniTag = el(root, 'abs tape red', { left: '330px', top: '880px', fontSize: '48px' }, 'الجامعة الإسلامية — غزة');
  uniTag.style.clipPath = tornPoly(63, 2);
  const intif = newsClip(root, { head: 'الانتفاضة الأولى', meta: ['1987', 'غزة'], w: 470, h: 300, size: 50, seed: 64 }, { left: '70px', top: '960px' });
  const arrest = clipPlayer(root, 'arrest89', 125, { left: '440px', top: '930px', width: '600px', height: '500px' }, { seed: 65, start: C.arrest, freezeAt: C.y89 + .4 });
  const s89 = stamp(root, '1989', 130, { left: '620px', top: '1450px' });
  const arrestTag = el(root, 'abs tape ink', { left: '200px', top: '1300px', fontSize: '44px' }, 'الاعتقال الأول');

  let mo, mg, ky, kr, len = 0;
  return (t) => {
    if (!mo) {
      const d = window.MAP; mo = root.querySelector('#mo'); mg = root.querySelector('#mg'); ky = root.querySelector('#ky'); kr = root.querySelector('#kr');
      mo.setAttribute('d', d.outline); mg.setAttribute('d', d.gaza);
      [ky, kr].forEach(c => { c.setAttribute('cx', d.khanYunis[0]); c.setAttribute('cy', d.khanYunis[1]); });
      len = mo.getTotalLength(); mo.style.strokeDasharray = len;
      mapWrap.style.transformOrigin = `${d.gazaCenter[0]}px ${d.gazaCenter[1]}px`;
    }
    const s = C.s2, out1 = pr(t, C.uni - .2, C.uni + .3);
    tf(head, { x: 200 * (1 - pr(t, s + .5, s + 1)), o: pr(t, s + .5, s + .8) });
    mo.style.strokeDashoffset = len * (1 - pr(t, s + .4, s + 2.0, E.io));
    mo.style.fillOpacity = pr(t, s + 1.6, s + 2.4);
    mg.style.opacity = pr(t, s + 2.2, s + 2.6);
    const z = kf(t, [[C.camp - 1.6, 1], [C.camp + .1, 3.1]]);
    tf(mapWrap, { s: z, x: kf(t, [[C.camp - 1.6, 0], [C.camp + .1, 190]]), y: kf(t, [[C.camp - 1.6, 0], [C.camp + .1, -150]]), o: 1 - out1 });
    mo.style.strokeWidth = 3.5 / z; mg.style.strokeWidth = 2 / z;
    ky.style.opacity = pr(t, C.camp, C.camp + .2); ky.setAttribute('r', 9 / z * 1.6);
    const pulse = (((t - C.camp) % 1.2) + 1.2) % 1.2 / 1.2;
    kr.style.opacity = t > C.camp ? 1 - pulse : 0; kr.setAttribute('r', (10 + pulse * 30) / z * 1.6);
    tf(mapLabel, { x: -60 * (1 - pr(t, C.camp + .1, C.camp + .5)), r: -2, o: pr(t, C.camp + .1, C.camp + .3) * (1 - out1) });
    tf(mapSub, { o: pr(t, C.south, C.south + .5) * (1 - out1) });
    slam(s65, t, C.y65, { r: -9 });
    s65.style.opacity = (t < C.y65 ? 0 : 1) * (1 - out1);
    tf(card, { y: 420 * (1 - pr(t, C.born, C.born + .7)), r: 2, o: pr(t, C.born, C.born + .3) * (1 - pr(t, C.arrest - .3, C.arrest)) });
    camp.update(t);
    tf(camp.box, { y: 500 * (1 - pr(t, C.camp + .3, C.camp + 1, E.back)), r: -3, o: pr(t, C.camp + .3, C.camp + .5) * (1 - out1) });
    tf(campTag, { r: 4, o: pr(t, C.camp + 1.1, C.camp + 1.4) * (1 - out1) });
    uni.update(t);
    const fz = C.arrest - .5;
    tf(uni.box, { y: -60 * (1 - pr(t, C.uni - .1, C.uni + .6)), s: kf(t, [[C.uni - .1, 1.08], [C.uni + .6, 1], [fz, 1], [fz + .6, .82]]), x: kf(t, [[fz, 0], [fz + .6, -120]]), r: kf(t, [[fz, 0], [fz + .6, -5]]), o: pr(t, C.uni - .1, C.uni + .2) });
    tf(uniTag, { x: 120 * (1 - pr(t, C.uni + .5, C.uni + .9)), r: -2, o: pr(t, C.uni + .5, C.uni + .7) * (1 - pr(t, fz, fz + .2)) });
    tf(intif, { x: -500 * (1 - pr(t, C.joined, C.joined + .6)), r: -4, o: pr(t, C.joined, C.joined + .2) });
    arrest.update(t);
    tf(arrest.box, { x: 600 * (1 - pr(t, C.arrest, C.arrest + .6, E.back)), r: 4, o: pr(t, C.arrest, C.arrest + .2) });
    slam(s89, t, C.y89, { r: -8 });
    tf(arrestTag, { r: -2, o: pr(t, C.y89 + .5, C.y89 + .8) });
    root.style.transform = `scale(${1 + (t - s) * .002})`;
  };
}, 'tear');

/* SCENE 3 — من الظل */
scene(C.s3, C.s4 + .8, 'bg-dark', (root) => {
  const big = el(root, 'abs', { left: '0', right: '0', top: '120px', textAlign: 'center', fontFamily: 'Cairo', fontWeight: 900, fontSize: '420px', color: 'transparent', WebkitTextStroke: '4px #8e1b1b', lineHeight: 1 }, '2002');
  const circle = el(root, 'abs', { left: '160px', top: '520px', width: '760px', height: '760px', borderRadius: '50%', background: 'var(--red)' });
  const portrait = img(root, A + 'portrait_main_ht.png', { left: '170px', top: '470px', width: '740px' });
  const tear = el(root, 'abs', { left: '-20px', top: '1290px', width: '1120px', height: '260px', background: 'url(../assets/paper.jpg) center/cover' });
  tear.style.clipPath = tornPoly(71, 9, 40);
  const lab = el(root, 'abs tape ink', { right: '70px', top: '1330px', fontSize: '54px' }, 'قيادة الجناح العسكري لحماس');
  const lab2 = el(root, 'abs info', { right: '80px', top: '1440px', fontSize: '34px', color: '#3a3530' }, 'كتائب القسام · منذ 2002');

  const nA = newsClip(root, { head: 'سلسلة تفجيرات تستهدف حافلات', meta: ['فبراير – مارس', '1996'], w: 560, h: 520, size: 58, seed: 72 }, { left: '30px', top: '170px' });
  const nB = newsClip(root, { head: 'القدس · عسقلان · تل أبيب', meta: ['1996', ''], w: 480, h: 300, size: 40, seed: 73 }, { left: '560px', top: '330px' });
  const s96 = stamp(root, '1996', 120, { left: '640px', top: '160px' }, 'stamp light');
  const street = clipPlayer(root, 'street', 75, { left: '520px', top: '640px', width: '500px', height: '420px' }, { seed: 74, start: C.buses + .5, speed: .9, freezeAt: C.buses + 2.6 });

  const silBox = el(root, 'abs clip', { left: '190px', top: '470px', width: '700px', height: '700px', padding: '16px' });
  silBox.style.clipPath = tornPoly(75, 1);
  const sil = img(silBox, A + 'silhouette_bw.jpg', { position: 'relative', width: '100%', height: '100%', objectFit: 'cover' });
  const wave = el(root, 'abs', { left: '140px', top: '1180px', width: '800px', height: '160px', display: 'flex', alignItems: 'center', gap: '6px' });
  const wbars = Array.from({ length: 50 }, () => el(wave, '', { flex: 1, background: '#f2ede3', borderRadius: '3px' }));
  const vTag = el(root, 'abs tape red', { left: '330px', top: '1400px', fontSize: '50px' }, 'تسجيلات صوتية فقط');
  vTag.style.clipPath = tornPoly(76, 2);
  const absent = el(root, 'abs title rtl', { left: 0, right: 0, top: '1290px', textAlign: 'center', fontSize: '84px', color: '#f2ede3' }, 'غيابه جزء من صورته');

  return (t) => {
    const R = rand(Math.round(t * FPS) + 99);
    const actOut = pr(t, C.buses - .3, C.buses + .2);
    tf(big, { y: kf(t, [[C.y02, 60], [C.buses, 0]]), o: pr(t, C.y02, C.y02 + .5) * (1 - actOut), s: kf(t, [[C.y02, 1.15], [C.buses, 1]]) });
    const pOut = pr(t, C.hidden, C.hidden + .8, E.io);
    const mx = kf(t, [[C.buses - .3, 0], [C.buses + .4, -170]]), my = kf(t, [[C.buses - .3, 0], [C.buses + .4, 240]]), ms = kf(t, [[C.buses - .3, 1], [C.buses + .4, .78]]);
    tf(circle, { x: mx, y: my, s: ms * pr(t, C.y02 + .1, C.y02 + .8, E.back) * (1 - pOut), o: 1 });
    tf(portrait, { y: 140 * (1 - pr(t, C.lead - .4, C.lead + .4, E.back)) + my, s: ms, x: mx, o: pr(t, C.lead - .4, C.lead) * (1 - pOut) });
    tf(tear, { y: 300 * (1 - pr(t, C.wing - .4, C.wing + .2)), o: 1 - actOut });
    tf(lab, { x: 200 * (1 - pr(t, C.wing, C.wing + .5)), r: -1.5, o: pr(t, C.wing, C.wing + .2) * (1 - actOut) });
    tf(lab2, { o: pr(t, C.wing + .7, C.wing + 1.2) * (1 - actOut) });
    const clipsOut = pr(t, C.hidden - .3, C.hidden + .3, E.in);
    tf(nA, { x: -600 * (1 - pr(t, C.buses, C.buses + .5, E.back)) - 700 * clipsOut, r: -5, o: pr(t, C.buses, C.buses + .2) });
    tf(nB, { x: 600 * (1 - pr(t, C.buses + .6, C.buses + 1.1, E.back)) + 700 * clipsOut, r: 4, o: pr(t, C.buses + .6, C.buses + .8) });
    s96.style.opacity = 0; if (t > C.y96) { slam(s96, t, C.y96, { r: 8 }); s96.style.opacity *= (1 - clipsOut); }
    street.update(t);
    tf(street.box, { y: 500 * (1 - pr(t, C.buses + .5, C.buses + 1, E.back)) + 1500 * clipsOut, r: kf(t, [[C.buses + 2.6, 0], [C.buses + 3, -4]]), s: kf(t, [[C.buses + 2.6, 1], [C.buses + 3, .94]]), o: pr(t, C.buses + .5, C.buses + .7) });
    const vIn = pr(t, C.hidden + .3, C.hidden + 1.1, E.io), vShrink = pr(t, C.absent - .3, C.absent + .9, E.io);
    tf(silBox, { s: lerp(1.06, 1, vIn) * lerp(1, .5, vShrink), y: lerp(0, -120, vShrink), o: vIn * (R() > .1 || t > C.audio ? 1 : .6) });
    sil.style.filter = `contrast(1.25) brightness(${.6 + vIn * .4})`;
    const amp = pr(t, C.audio - .1, C.audio + .3) * (1 - pr(t, C.absent - .4, C.absent));
    wbars.forEach((b, i) => { const v = Math.abs(Math.sin(t * 9 + i * .7) * Math.sin(t * 3.1 + i * 1.9)) * .8 + R() * .2; b.style.height = (6 + v * 150 * amp) + 'px'; });
    tf(wave, { o: amp });
    tf(vTag, { y: 60 * (1 - pr(t, C.audio + .3, C.audio + .7)), r: -2, o: pr(t, C.audio + .3, C.audio + .5) * (1 - pr(t, C.absent - .4, C.absent - .1)) });
    tf(absent, { y: kf(t, [[C.absent, 40], [C.absent + .8, -280]]), o: pr(t, C.absent, C.absent + .6) });
  };
}, 'tear');

/* SCENE 4 — المطاردة */
scene(C.s4, C.s5 + .8, 'bg-paper', (root) => {
  const head = el(root, 'abs tape ink', { right: '60px', top: '90px', fontSize: '46px' }, 'محاولات الاغتيال');
  const pw = 600, ph = 523, px = 400, py = 560, N = 6;
  const strips = Array.from({ length: N }, (_, i) => el(root, 'abs', {
    left: (px + i * pw / N) + 'px', top: py + 'px', width: (pw / N + 1) + 'px', height: ph + 'px',
    background: `url(../assets/portrait_interview_bw.png) ${-i * pw / N}px 0/${pw}px ${ph}px no-repeat`
  }));
  const dark = el(root, 'full', { background: 'radial-gradient(circle at 62% 42%, transparent 0, transparent 22%, #0d0c0b 48%)' });
  const years = ['2001', '2002', '2003', '2006', '2014'];
  const ys = years.map((y, i) => {
    const d = el(root, 'abs', { left: '70px', top: (300 + i * 230) + 'px', fontFamily: 'Cairo', fontWeight: 900, fontSize: '150px', color: 'var(--ink)', lineHeight: 1 }, y);
    const strike = el(d, 'abs', { left: '-10px', right: '-10px', top: '52%', height: '16px', background: 'var(--red2)', transformOrigin: 'left center' });
    return { d, strike };
  });
  const armor = clipPlayer(root, 'armor', 125, { left: '560px', top: '1220px', width: '460px', height: '380px' }, { seed: 81, start: C.attempts, freezeAt: C.hurt + .4 });
  const hurt = el(root, 'abs tape red', { left: '520px', top: '1560px', fontSize: '50px' }, 'إصابات بالغة');
  hurt.style.clipPath = tornPoly(82, 2);
  const back = el(root, 'abs title rtl', { left: 0, right: 0, top: '1340px', textAlign: 'center', fontSize: '110px' }, 'يعود إلى الظل');

  const beats = [C.years + .3, C.years + 1.2, C.attempts + .2, C.attempts + 1.1, C.attempts + 2.0];
  return (t) => {
    const R = rand(Math.round(t * FPS) + 5);
    const out = pr(t, C.each - .1, C.each + .3);
    tf(head, { x: 200 * (1 - pr(t, C.years, C.years + .5)), o: pr(t, C.years, C.years + .3) * (1 - out) });
    const lastBeat = beats.filter(b => t >= b).length;
    const align = pr(t, C.each - .3, C.each + .2, E.io);
    strips.forEach((s, i) => {
      const r2 = rand(i * 31 + lastBeat * 7);
      const jx = lastBeat ? (r2() - .5) * 60 : 0, jy = lastBeat ? (r2() - .5) * 90 : 0;
      const kick = lastBeat ? 1 + (1 - pr(t, beats[lastBeat - 1], beats[lastBeat - 1] + .3)) * .6 : 0;
      tf(s, { x: jx * kick * (1 - align), y: jy * kick * (1 - align), o: pr(t, C.s4 + .1, C.s4 + .5) });
      s.style.filter = `contrast(1.2) brightness(${lerp(1, .25, pr(t, C.each + .3, C.back + .6))})`;
    });
    ys.forEach(({ d, strike }, i) => {
      slam(d, t, beats[i], { r: -2, from: 1.6 });
      strike.style.transform = `scaleX(${pr(t, beats[i] + .3, beats[i] + .55, E.io)})`;
      d.style.opacity *= 1 - out;
    });
    armor.update(t);
    tf(armor.box, { y: 500 * (1 - pr(t, C.attempts, C.attempts + .5, E.back)), r: 3, o: pr(t, C.attempts, C.attempts + .2) * (1 - out) });
    tf(hurt, { x: -120 * (1 - pr(t, C.hurt, C.hurt + .4)), r: -3, o: pr(t, C.hurt, C.hurt + .2) * (1 - out) });
    tf(dark, { o: pr(t, C.each + .1, C.back, E.io) });
    tf(back, { y: 40 * (1 - pr(t, C.back, C.back + .6)), o: pr(t, C.back, C.back + .5) });
    root.style.transform = beats.some(b => t >= b && t < b + .08) ? `translate(${(R() - .5) * 14}px,${(R() - .5) * 14}px)` : '';
  };
}, 'tear');

/* SCENE 5 — الإعلان */
scene(C.s5, C.s6 + .8, 'bg-old', (root) => {
  const head = el(root, 'abs tape ink', { right: '60px', top: '90px', fontSize: '46px' }, 'خان يونس · 2024');
  const sJul = stamp(root, 'يوليو 2024', 104, { right: '70px', top: '230px' });
  const ruins = clipPlayer(root, 'ruins', 57, { left: '70px', top: '470px', width: '940px', height: '760px' }, { seed: 91, start: C.jul + .6, speed: .75, freezeAt: C.war - .3 });
  const tag = el(root, 'abs tape red', { left: '100px', top: '1190px', fontSize: '50px' }, 'المواصي — خان يونس');
  tag.style.clipPath = tornPoly(92, 2);
  const nWar = newsClip(root, { head: 'الحرب في غزة', meta: ['2023 – 2025', ''], w: 520, h: 360, size: 64, seed: 93 }, { left: '60px', top: '1330px' });
  const sJan = stamp(root, 'يناير 2025', 96, { left: '560px', top: '1380px' });
  const conf = el(root, 'abs news', { left: '560px', top: '1540px', width: '440px', height: '170px', padding: '24px 30px' });
  conf.style.clipPath = tornPoly(94, 2);
  conf.innerHTML = '<div class="info" style="font-size:40px;font-weight:600">حماس تؤكد مقتله</div>';
  const items = [head, sJul, tag, nWar, sJan, conf, ruins.box];

  return (t) => {
    tf(head, { x: 200 * (1 - pr(t, C.s5 + .2, C.s5 + .7)), o: pr(t, C.s5 + .2, C.s5 + .5) });
    slam(sJul, t, C.jul + .2, { r: -6 });
    ruins.update(t);
    const fz = C.war - .3;
    tf(ruins.box, { y: 120 * (1 - pr(t, C.jul + .6, C.jul + 1.2)), s: kf(t, [[C.jul + .6, 1.05], [C.jul + 1.2, 1], [fz, 1], [fz + .5, .94]]), r: kf(t, [[fz, 0], [fz + .5, -2.5]]), o: pr(t, C.jul + .6, C.jul + .9) });
    tf(tag, { x: -150 * (1 - pr(t, C.mawasi + .8, C.mawasi + 1.2)), r: -2, o: pr(t, C.mawasi + .8, C.mawasi + 1) });
    tf(nWar, { y: 500 * (1 - pr(t, C.war, C.war + .6, E.back)), r: -3, o: pr(t, C.war, C.war + .2) });
    slam(sJan, t, C.jan + .3, { r: 7 });
    tf(conf, { y: 200 * (1 - pr(t, C.conf, C.conf + .4)), r: 2, o: pr(t, C.conf, C.conf + .2) });
    items.forEach((n, i) => {
      const t0 = C.conf + .55 + i * .13, p = pr(t, t0, t0 + .4, E.in);
      if (t > t0) { n.style.transform += ` translate(0px,${p * -60}px)`; n.style.opacity = (parseFloat(n.style.opacity) || 1) * (1 - p); }
    });
  };
});

/* SCENE 6 — رحل كما عاش */
scene(C.s6, C.end, 'bg-dark', (root) => {
  const portrait = img(root, A + 'portrait_tree_bw.png', { left: '235px', top: '520px', width: '610px' });
  const fade = el(root, 'abs', { left: '200px', top: '1100px', width: '680px', height: '260px', background: 'linear-gradient(to bottom, transparent, #161514 70%)' });
  const silBox = el(root, 'abs', { left: '190px', top: '480px', width: '700px', height: '700px', overflow: 'hidden' });
  img(silBox, A + 'silhouette_bw.jpg', { left: 0, top: 0, width: '100%', height: '100%', objectFit: 'cover' });
  silBox.style.webkitMask = 'radial-gradient(circle at 50% 45%, #000 45%, transparent 72%)';
  const line = el(root, 'abs', { left: '390px', top: '1420px', width: '300px', height: '6px', background: 'var(--red)', transformOrigin: 'center' });
  const name = el(root, 'abs title rtl', { left: 0, right: 0, top: '1290px', textAlign: 'center', fontSize: '150px' }, 'محمد الضيف');
  const dates = el(root, 'abs', { left: 0, right: 0, top: '1460px', textAlign: 'center', fontFamily: 'Cairo', fontWeight: 400, fontSize: '56px', color: '#a49e93', letterSpacing: '6px' }, '1965 – 2024');
  const black = el(root, 'full', { background: '#000' });

  return (t) => {
    const cross = pr(t, C.left - .2, C.left + 1.6, E.io);
    tf(portrait, { s: kf(t, [[C.s6, 1], [C.left + 1.6, 1.07]], E.lin), y: kf(t, [[C.s6, 30], [C.left + 1.6, -10]], E.lin), o: pr(t, C.s6 + .2, C.s6 + 1.4, E.io) * (1 - cross) });
    portrait.style.filter = `contrast(1.1) brightness(${lerp(1, .3, cross)})`;
    tf(fade, { o: 1 });
    tf(silBox, { s: kf(t, [[C.left, 1.04], [C.name + 1, 1]], E.lin), o: cross });
    tf(name, { y: 30 * (1 - pr(t, C.name, C.name + .8)), o: pr(t, C.name, C.name + .8) });
    tf(line, { sx: pr(t, C.name + .6, C.name + 1.4, E.io), sy: 1, o: 1 });
    tf(dates, { o: pr(t, C.name + 1.1, C.name + 1.9) });
    tf(black, { o: pr(t, C.end - 1.8, C.end - .4, E.io) });
  };
});

/* ---------- global overlays ---------- */
const grain = img(stage, A + 'grain_0.png', { left: 0, top: 0, width: W + 'px', height: H + 'px', mixBlendMode: 'overlay', zIndex: 50 });
const vign = el(stage, 'overlay', { background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,.45) 100%)', zIndex: 51 });

window.seek = async (t) => {
  pending.length = 0;
  for (const s of scenes) {
    const on = t >= s.start && t < s.end;
    s.root.style.display = on ? 'block' : 'none';
    if (!on) continue;
    s.root.style.transform = '';
    s.update(t, s);
    if (s.transIn === 'tear') {
      const p = pr(t, s.start, s.start + .75, E.io);
      s.root.style.clipPath = p >= 1 ? 'none' : tearReveal(p, Math.round(s.start * 10));
      s.root.style.filter = p < 1 ? 'drop-shadow(0 -10px 22px rgba(0,0,0,.55))' : '';
    }
  }
  // scene 5 -> 6: soft crossfade instead of a tear
  const s6 = scenes[5]; s6.root.style.opacity = pr(t, C.s6, C.s6 + .7, E.io);
  const gi = Math.floor(t * FPS) % 6; grain.src = `${A}grain_${gi}.png`;
  pending.push(grain.decode().catch(() => { }));
  await Promise.all(pending);
};

window.ready = (async () => {
  window.MAP = await (await fetch(A + 'map.json')).json();
  await document.fonts.ready;
  await Promise.all([...document.images].map(i => i.decode().catch(() => { })));
  window.DURATION = DURATION; window.FPS = FPS;
  return true;
})();
