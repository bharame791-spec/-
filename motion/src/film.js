// One continuous shot: coffee bean → cardamom → dalla → grid → identity → designer → CTA.
// World space is one big canvas; a virtual camera travels through it. No cuts.
(function () {
  const { el, set, E, clamp, lerp, p, track, trim, pointAt, mixHex } = window.M;
  const T = window.THEME, C = T.colors, A = T.assets, COPY = T.copy;
  const W = 1080, H = 1920;
  const DURATION = 30;
  // The choreography is authored on a 53s master timeline; this curve retimes it to
  // the 30s cut. Quiet holds compress harder than key moves, and the monotone cubic
  // keeps playback speed smooth across scene boundaries (no velocity kinks).
  // Keys are [cut time, master time], locked to the recorded voice-over (audio/vo-cut.wav).
  const RETIME = [
    [0, 0], [2.1, 4.7], [3.4, 6.3], [4.5, 7.7], [5.55, 9.3], [6.95, 11.75],
    [8.8, 15.0], [10.0, 18.2], [11.05, 20.6], [12.95, 25.9], [14.25, 28.0], [15.1, 31.0],
    [16.75, 36.9], [21.4, 42.2], [22.6, 44.0], [23.75, 45.3], [24.4, 46.4],
    [25.5, 47.4], [27.4, 48.7], [28.7, 50.6], [30, 53],
  ];
  const retime = (function monotone(pts) {
    const n = pts.length, x = pts.map((q) => q[0]), y = pts.map((q) => q[1]);
    const d = [], m = [];
    for (let i = 0; i < n - 1; i++) d.push((y[i + 1] - y[i]) / (x[i + 1] - x[i]));
    m[0] = d[0]; m[n - 1] = d[n - 2];
    for (let i = 1; i < n - 1; i++) m[i] = d[i - 1] * d[i] <= 0 ? 0 : (2 * d[i - 1] * d[i]) / (d[i - 1] + d[i]);
    return (t) => {
      if (t <= x[0]) return y[0];
      if (t >= x[n - 1]) return y[n - 1];
      let i = 0;
      while (t > x[i + 1]) i++;
      const h = x[i + 1] - x[i], u = (t - x[i]) / h, u2 = u * u, u3 = u2 * u;
      return (2 * u3 - 3 * u2 + 1) * y[i] + (u3 - 2 * u2 + u) * h * m[i] + (-2 * u3 + 3 * u2) * y[i + 1] + (u3 - u2) * h * m[i + 1];
    };
  })(RETIME);
  let uid = 0;
  const id = (s) => `${s}${++uid}`;

  // dalla placement in world space (scenes 1–2)
  const DX = 540, DY = 800, DS = 0.85;
  const toWorld = (x, y) => ({ x: DX + x * DS, y: DY + y * DS });

  // ---------------------------------------------------------------- helpers
  function rtlText(parent, str, o) {
    const n = el('text', {
      x: o.x || 0, y: o.y || 0, 'font-size': o.size || 60, 'font-weight': o.weight || 500,
      fill: o.fill || C.navy, 'text-anchor': o.anchor || 'middle', direction: 'rtl',
      'font-family': T.font, 'dominant-baseline': o.baseline || 'alphabetic',
    }, parent);
    n.textContent = str;
    return n;
  }

  // a line of text that rises out of a mask
  function maskLine(parent, str, o) {
    const g = el('g', {}, parent);
    const cid = id('clip');
    const defs = el('defs', {}, g);
    const cp = el('clipPath', { id: cid, clipPathUnits: 'userSpaceOnUse' }, defs);
    const size = o.size || 60;
    const rect = el('rect', { x: -2000, y: (o.y || 0) - size * 1.15, width: 5000, height: size * 1.55 }, cp);
    const clipped = el('g', { 'clip-path': `url(#${cid})` }, g);
    const inner = el('g', {}, clipped);
    const text = rtlText(inner, str, o);
    return {
      g, text, rect, size,
      update(kin, kout = 0) {
        const dy = (1 - kin) * size * 1.3 - kout * size * 1.3;
        set(inner, { transform: `translate(0 ${dy})` });
        g.style.display = kin <= 0 || kout >= 1 ? 'none' : '';
      },
    };
  }

  // words that enter one by one (RTL order: first word is right-most)
  function maskWords(parent, words, o) {
    const g = el('g', {}, parent);
    const items = words.map((w) => maskLine(g, w, { ...o, x: 0, anchor: 'start' }));
    const space = (o.size || 60) * 0.28;
    const widths = items.map((it) => it.text.getComputedTextLength());
    const total = widths.reduce((a, b) => a + b, 0) + space * (items.length - 1);
    let x = (o.x || 540) + total / 2;
    items.forEach((it, i) => { set(it.text, { x }); x -= widths[i] + space; });
    return {
      g, items,
      update(t, t0, stagger, dur, tOut) {
        items.forEach((it, i) => {
          const kin = p(t, t0 + i * stagger, t0 + i * stagger + dur, E.out);
          const kout = tOut ? p(t, tOut + i * 0.05, tOut + i * 0.05 + 0.45, E.in) : 0;
          it.update(kin, kout);
        });
      },
    };
  }

  // a horizontal wipe from right to left (Arabic reading direction)
  function rtlWipe(parent, o) {
    const cid = id('wipe');
    const cp = el('clipPath', { id: cid, clipPathUnits: 'userSpaceOnUse' }, el('defs', {}, parent));
    const r = el('rect', { x: o.x1, y: o.y0, width: 0, height: o.y1 - o.y0 }, cp);
    const g = el('g', { 'clip-path': `url(#${cid})` }, parent);
    return {
      g,
      update(k) {
        const w = (o.x1 - o.x0) * clamp(k);
        set(r, { x: o.x1 - w, width: w });
      },
    };
  }

  function stroke(parent, d, o = {}) {
    return el('path', {
      d, fill: 'none', stroke: o.stroke || C.blue, 'stroke-width': o.width || 5,
      'stroke-linecap': 'round', 'stroke-linejoin': 'round', ...(o.attrs || {}),
    }, parent);
  }

  function roundedDiamond(parent, size, fill) {
    const g = el('g', {}, parent);
    el('rect', {
      x: -size / 2, y: -size / 2, width: size, height: size, rx: size * 0.22,
      fill, transform: 'rotate(45)',
    }, g);
    return g;
  }

  function makeLogo(parent) {
    const [lw, lh] = A.logoSize;
    const g = el('g', {}, parent);
    const inner = el('g', { transform: `translate(${-1061} ${-940})` }, g);
    const mClip = id('lm');
    const cp = el('clipPath', { id: mClip, clipPathUnits: 'userSpaceOnUse' }, el('defs', {}, inner));
    const mRect = el('rect', { x: 0, y: 0, width: lw, height: lh }, cp);
    const m = el('image', { href: A.logoM, width: lw, height: lh, 'clip-path': `url(#${mClip})` }, inner);
    const reg = el('image', { href: A.logoReg, width: lw, height: lh }, inner);
    const dg = el('g', {}, inner);
    const diamond = el('image', { href: A.logoDiamond, width: lw, height: lh }, dg);
    return {
      g,
      // width in px of the visible mark; reveal 0..1 wipes the M upward, pop 0..1 drops the diamond
      place(cx, cy, width, reveal = 1, pop = 1, opacity = 1) {
        const s = width / 1773;
        set(g, { transform: `translate(${cx} ${cy}) scale(${s})`, opacity });
        g.style.display = opacity <= 0.001 ? 'none' : '';
        const top = 1800 - 1720 * clamp(reveal);
        set(mRect, { y: top, height: lh - top });
        const ps = Math.max(0.0001, pop);
        set(dg, { transform: `translate(1007 454) rotate(${(1 - clamp(pop)) * -90}) scale(${ps}) translate(-1007 -454)`, opacity: clamp(pop * 3) });
        set(reg, { opacity: clamp(reveal * pop) });
      },
    };
  }

  // ---------------------------------------------------------------- stage
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, id: 'film' });
  const stage = document.getElementById('stage');
  stage.appendChild(svg);

  const bgG = el('g', {}, svg);
  el('rect', { x: -200, y: -200, width: W + 400, height: H + 400, fill: C.white }, bgG);
  const bgMain = el('image', { href: A.bgMain, x: -81, y: -144, width: 1242, height: 2208, preserveAspectRatio: 'xMidYMid slice' }, bgG);
  const bgReveal = el('image', { href: A.bgReveal, x: -81, y: -144, width: 1242, height: 2208, preserveAspectRatio: 'xMidYMid slice', opacity: 0 }, bgG);

  const world = el('g', {}, svg);

  // ================================================================ SCENE 1–2: DALLA
  const dalla = el('g', {}, world);
  const silhouette =
    'M72,-300 C72,-270 44,-250 42,-200 L42,-120 C42,-60 150,-20 158,100 C165,200 130,270 110,300 L118,330 L-118,330 L-110,300 ' +
    'C-130,270 -165,200 -158,100 C-150,-20 -42,-60 -42,-120 L-42,-200 C-44,-250 -72,-270 -72,-300 Z';
  const dFill = el('path', { d: silhouette, fill: C.white, opacity: 0 }, dalla);
  const dLidFill = el('path', { d: 'M-62,-300 C-62,-345 -25,-362 0,-362 C25,-362 62,-345 62,-300 Z', fill: C.white, opacity: 0 }, dalla);
  const liqClip = id('liq');
  el('path', { d: silhouette }, el('clipPath', { id: liqClip, clipPathUnits: 'userSpaceOnUse' }, el('defs', {}, dalla)));
  const liquidG = el('g', { 'clip-path': `url(#${liqClip})` }, dalla);
  const liquid = el('path', { fill: C.blue, opacity: 0.92 }, liquidG);
  const liquidSurf = el('path', { fill: 'none', stroke: C.white, 'stroke-width': 4, opacity: 0.7 }, liquidG);
  const silPath = el('path', { d: silhouette, fill: 'none', stroke: 'none' }, dalla);
  const ds = { stroke: C.blue, width: 5 };
  const dSpout = stroke(dalla, 'M46,-104 C120,-150 186,-250 236,-346 L262,-338 C214,-236 170,-110 96,-30', ds);
  const dHandleO = stroke(dalla, 'M-42,-240 C-150,-250 -205,-170 -195,-70 C-188,10 -160,45 -132,62', { ...ds, width: 6 });
  const dHandleI = stroke(dalla, 'M-42,-212 C-128,-218 -172,-160 -166,-76 C-160,-14 -146,16 -134,30', ds);
  const dContourR = stroke(dalla, 'M72,-300 C72,-270 44,-250 42,-200 L42,-120 C42,-60 150,-20 158,100 C165,200 130,270 110,300 L118,330 L0,330', ds);
  const dContourL = stroke(dalla, 'M-72,-300 C-72,-270 -44,-250 -42,-200 L-42,-120 C-42,-60 -150,-20 -158,100 C-165,200 -130,270 -110,300 L-118,330 L0,330', ds);
  const dLidR = stroke(dalla, 'M62,-300 C62,-345 25,-362 0,-362', ds);
  const dLidL = stroke(dalla, 'M-62,-300 C-62,-345 -25,-362 0,-362', ds);
  const dFinial = el('g', {}, dalla);
  stroke(dFinial, 'M0,-362 L0,-378', ds);
  el('path', { d: 'M0,-432 C9,-414 14,-398 0,-382 C-14,-398 -9,-414 0,-432 Z', fill: C.orange }, dFinial);
  const dBands = [
    stroke(dalla, 'M-43,-165 Q0,-152 43,-165', ds),
    stroke(dalla, 'M-44,-120 Q0,-104 44,-120', ds),
    stroke(dalla, 'M-156,110 Q0,165 156,110', ds),
    stroke(dalla, 'M-118,330 Q0,350 118,330', ds),
  ];
  const dMouth = el('ellipse', { cx: 0, cy: -300, rx: 72, ry: 13, fill: C.white, stroke: C.blue, 'stroke-width': 5, opacity: 0 }, dalla);

  // ---- fire: a curve rises from the cardamom seeds, lands on a burner and ignites.
  // Heat climbs into the dalla, the coffee rises inside it, and steam leaves the spout.
  const FIRE_Y = 482;
  const flameLine = stroke(dalla, `M0,753 C-80,690 80,580 0,${FIRE_Y}`, { stroke: C.orange, width: 5 });
  const burner = [stroke(dalla, `M0,${FIRE_Y + 12} L-118,${FIRE_Y + 12}`, { stroke: C.navy, width: 5 }), stroke(dalla, `M0,${FIRE_Y + 12} L118,${FIRE_Y + 12}`, { stroke: C.navy, width: 5 })];
  const glowId = id('glow');
  const glowGrad = el('radialGradient', { id: glowId }, el('defs', {}, dalla));
  el('stop', { offset: '0%', 'stop-color': C.orange, 'stop-opacity': 0.42 }, glowGrad);
  el('stop', { offset: '100%', 'stop-color': C.orange, 'stop-opacity': 0 }, glowGrad);
  const glow = el('circle', { cx: 0, cy: FIRE_Y - 50, r: 170, fill: `url(#${glowId})`, opacity: 0 }, dalla);
  const flameG = el('g', {}, dalla);
  const flameSide = [el('path', { fill: C.orange }, flameG), el('path', { fill: C.orange }, flameG)];
  const flameOuter = el('path', { fill: C.orange }, flameG);
  const flameMid = el('path', { fill: mixHex(C.orange, C.white, 0.5) }, flameG);
  const flameCore = el('path', { fill: C.white }, flameG);
  const flameBase = el('ellipse', { cx: 0, cy: -5, rx: 30, ry: 7, fill: C.blue, opacity: 0.9 }, flameG);
  function tongue(h, w, sx) {
    return `M0,0 C${-w},${-0.08 * h} ${-w * 1.1 + sx * 0.2},${-0.5 * h} ${-w * 0.35 + sx * 0.6},${-0.78 * h} ` +
      `C${-w * 0.15 + sx * 0.9},${-0.9 * h} ${sx},${-0.96 * h} ${sx},${-h} ` +
      `C${sx},${-0.96 * h} ${w * 0.15 + sx * 0.9},${-0.9 * h} ${w * 0.35 + sx * 0.6},${-0.78 * h} ` +
      `C${w * 1.1 + sx * 0.2},${-0.5 * h} ${w},${-0.08 * h} 0,0 Z`;
  }
  const heat = [-46, 0, 46].map((x) => stroke(dalla,
    `M${x},${FIRE_Y - 110} C${x + 14},${FIRE_Y - 150} ${x - 14},${FIRE_Y - 190} ${x},${FIRE_Y - 230} C${x + 14},${FIRE_Y - 270} ${x - 14},${FIRE_Y - 310} ${x},${FIRE_Y - 350} C${x + 14},${FIRE_Y - 390} ${x - 14},${FIRE_Y - 430} ${x},${FIRE_Y - 470}`,
    { stroke: C.orange, width: 4, attrs: { opacity: 0.75 } }));
  const steam = [
    stroke(dalla, 'M252,-362 C232,-402 282,-432 258,-472 C236,-508 274,-538 260,-578', { stroke: C.blue, width: 4, attrs: { opacity: 0.5 } }),
    stroke(dalla, 'M236,-372 C212,-410 252,-446 232,-482 C214,-514 246,-542 236,-572', { stroke: C.blue, width: 3, attrs: { opacity: 0.35 } }),
  ];

  // ---- beans
  const BEAN = 'M0,-50 C28,-50 36,-22 36,0 C36,26 24,50 0,50 C-24,50 -36,26 -36,0 C-36,-22 -28,-50 0,-50 Z';
  const beansG = el('g', {}, world);
  const beans = [];
  for (let i = 0; i < 7; i++) {
    const g = el('g', {}, beansG);
    const body = el('path', { d: BEAN, fill: C.blue }, g);
    const crease = stroke(g, 'M3,-41 C-17,-18 17,18 -3,41', { stroke: C.white, width: 5 });
    beans.push({ g, body, crease });
  }
  const morph = el('ellipse', { cx: 0, cy: 0, rx: 36, ry: 50, fill: 'none', stroke: C.blue, 'stroke-width': 5, opacity: 0 }, world);

  // ---- hook text
  const hook = el('g', {}, world);
  const hookParts = COPY.hook.split(' ');
  const hookL1 = maskLine(hook, hookParts.slice(0, 3).join(' '), { x: 540, y: 1405, size: 74, weight: 700, fill: C.navy });
  const hookL2 = maskLine(hook, hookParts.slice(3).join(' '), { x: 540, y: 1500, size: 74, weight: 700, fill: C.blue });

  // ---- cardamom
  const POD = 'M0,-46 C23,-30 25,24 0,46 C-25,24 -23,-30 0,-46 Z';
  const podsG = el('g', {}, world);
  const pods = [];
  for (let j = 0; j < 5; j++) {
    const g = el('g', {}, podsG);
    const left = el('g', {}, g), right = el('g', {}, g);
    el('path', { d: 'M0,-46 C-23,-30 -25,24 0,46 Z', fill: '#8CC3EA' }, left);
    el('path', { d: 'M0,-46 C23,-30 25,24 0,46 Z', fill: '#8CC3EA' }, right);
    stroke(g, 'M0,-40 L0,40', { stroke: C.blue, width: 3 });
    el('path', { d: POD, fill: 'none', stroke: C.blue, 'stroke-width': 3 }, g);
    pods.push({ g, left, right });
  }
  const seeds = [];
  for (let s = 0; s < 7; s++) seeds.push(el('ellipse', { rx: 7, ry: 9, fill: C.navy }, world));

  // ---- ingredient labels
  const labelG = el('g', {}, world);
  const labelMark = roundedDiamond(labelG, 22, C.orange);
  const lblBean = maskLine(labelG, COPY.bean, { x: 540, y: 1600, size: 66, weight: 500 });
  const lblCard = maskLine(labelG, COPY.cardamom, { x: 540, y: 1600, size: 66, weight: 500 });
  const lblFire = maskLine(labelG, COPY.fire, { x: 540, y: 1352, size: 58, weight: 500 });

  // ================================================================ POUR → GRID
  const pourD = 'M752,509 C820,515 880,600 880,800 C880,1200 980,1700 1000,2100 C1010,2350 1040,2550 960,2550 L120,2550';
  const pourCurve = el('path', { d: 'M752,509 C820,515 880,600 880,800 C880,1200 980,1700 1000,2100 C1010,2350 1040,2550 960,2550', fill: 'none', stroke: 'none' }, world);
  const pour = stroke(world, pourD, { stroke: C.blue, width: 6 });

  const gridG = el('g', {}, world);
  const GX = [], GY = [];
  for (let k = 0; k <= 6; k++) GX.push(120 + k * 140);
  for (let k = 0; k <= 8; k++) GY.push(2550 + k * 137.5);
  const vLines = GX.map((x, k) => stroke(gridG, `M${x},2550 L${x},3650`, { stroke: C.navy, width: k % 6 === 0 ? 2 : 1.5, attrs: { opacity: k % 6 === 0 ? 0.45 : 0.22 } }));
  const hLines = GY.slice(1).map((y, k) => stroke(gridG, `M960,${y} L120,${y}`, { stroke: C.navy, width: k === 7 ? 2 : 1.5, attrs: { opacity: k === 7 ? 0.45 : 0.22 } }));

  const s3 = el('g', {}, world);
  const eyebrow1 = maskLine(s3, COPY.eyebrow1, { x: 940, y: 2628, size: 30, weight: 500, fill: C.blue, anchor: 'start' });
  const eyebrow2 = maskLine(s3, COPY.eyebrow2, { x: 940, y: 2628, size: 30, weight: 500, fill: C.blue, anchor: 'start' });
  const head1 = maskLine(s3, COPY.content, { x: 940, y: 2770, size: 112, weight: 700, anchor: 'start' });
  const head2 = maskLine(s3, COPY.identity, { x: 940, y: 2770, size: 96, weight: 700, anchor: 'start' });
  const bars = [640, 520, 380].map((w, i) => el('rect', { x: 940 - w, y: 2826 + i * 32, width: w, height: 12, rx: 6, fill: C.navy, opacity: 0.28 }, s3));
  const footBars = [820, 600].map((w, i) => el('rect', { x: 940 - w, y: 3532 + i * 34, width: w, height: 12, rx: 6, fill: C.navy, opacity: 0.2 }, s3));

  // modules
  const shadowId = id('sh');
  const f = el('filter', { id: shadowId, x: '-20%', y: '-20%', width: '140%', height: '140%' }, el('defs', {}, svg));
  el('feDropShadow', { dx: 0, dy: 18, stdDeviation: 22, 'flood-color': C.navy, 'flood-opacity': 0.14 }, f);

  const block = el('g', {}, world);
  const blockRect = el('rect', { rx: 22, fill: C.white, filter: `url(#${shadowId})` }, block);
  const blockGlyph = el('g', {}, block);
  el('circle', { cx: 80, cy: -70, r: 34, fill: C.orange }, blockGlyph);
  el('path', { d: 'M-170,120 L-60,-20 L10,60 L60,10 L170,120 Z', fill: C.sky }, blockGlyph);
  el('path', { d: 'M-60,-20 L10,60 L-20,95', fill: 'none', stroke: C.blue, 'stroke-width': 4, 'stroke-linejoin': 'round', opacity: 0.6 }, blockGlyph);
  const blockInset = el('rect', { fill: 'none', stroke: C.sky, 'stroke-width': 3, rx: 14, opacity: 0 }, block);
  const blockBars = [0.62, 0.42].map(() => el('rect', { rx: 6, fill: C.navy, opacity: 0 }, block));
  const blockLogo = makeLogo(block);

  const elCircle = el('circle', { fill: C.orange }, s3);
  const elSquare = el('rect', { fill: C.navy }, s3);
  const elSwatch3 = el('circle', { fill: C.navy }, s3);
  const elPill = el('rect', { fill: C.blue }, s3);
  const elDot = el('circle', { cx: 150, cy: 3550, r: 9, fill: C.orange }, s3);
  const specimen = maskLine(s3, 'أبجد', { x: 260, y: 3330, size: 104, weight: 300, fill: C.navy });

  // ================================================================ SCENE 4: APPLICATIONS
  const s4 = el('g', {}, world);
  const headline = maskWords(s4, COPY.designs, { x: 540, y: 2500, size: 100, weight: 700, fill: C.navy });
  const valueLine = maskLine(s4, COPY.value, { x: 540, y: 2610, size: 54, weight: 500, fill: C.blue });

  const connectors = el('g', {}, world);
  const conA = stroke(connectors, 'M290,3262 L290,3390 L380,3390', { stroke: C.navy, width: 2.5, attrs: { opacity: 0.55 } });
  const conB = stroke(connectors, 'M720,3162 L720,3218', { stroke: C.navy, width: 2.5, attrs: { opacity: 0.55 } });
  const nodes = [[290, 3390], [720, 3190], [380, 3390]].map(([x, y]) => {
    const n = roundedDiamond(connectors, 16, C.orange);
    n.__x = x; n.__y = y;
    return n;
  });

  const unitsG = el('g', {}, world);
  function unit(fill, rx) {
    const g = el('g', {}, unitsG);
    const r = el('rect', { fill, rx, filter: `url(#${shadowId})` }, g);
    const c = el('g', {}, g);
    return { g, r, c, rx };
  }
  // U1 — social post 460×460
  const U1 = unit(C.blue, 26);
  roundedDiamond(U1.c, 150, C.orange).setAttribute('transform', 'translate(230 200)');
  el('rect', { x: 120, y: 350, width: 220, height: 16, rx: 8, fill: C.white }, U1.c);
  el('rect', { x: 160, y: 382, width: 140, height: 12, rx: 6, fill: C.white, opacity: 0.6 }, U1.c);
  el('circle', { cx: 410, cy: 50, r: 14, fill: C.white, opacity: 0.85 }, U1.c);
  U1.W = 460; U1.H = 460;
  // U2 — business card 560×320
  const U2 = unit(C.white, 22);
  const cardLogo = makeLogo(U2.c);
  cardLogo.place(150, 160, 170);
  el('rect', { x: 290, y: 0, width: 3, height: 320, fill: C.sky }, U2.c);
  el('rect', { x: 330, y: 118, width: 180, height: 18, rx: 9, fill: C.navy }, U2.c);
  el('rect', { x: 370, y: 152, width: 140, height: 12, rx: 6, fill: C.blue }, U2.c);
  [196, 222].forEach((y, i) => el('rect', { x: 390 - i * 30, y, width: 120 + i * 30, height: 9, rx: 4.5, fill: C.navy, opacity: 0.3 }, U2.c));
  U2.W = 560; U2.H = 320;
  // U3 — story 300×560
  const U3 = unit(C.navy, 30);
  const avClip = id('av');
  el('circle', { cx: 150, cy: 92, r: 44 }, el('clipPath', { id: avClip }, el('defs', {}, U3.c)));
  el('image', { href: A.portrait, x: 106, y: 48, width: 88, height: 88, 'clip-path': `url(#${avClip})` }, U3.c);
  el('rect', { x: 30, y: 170, width: 240, height: 190, rx: 16, fill: C.blue }, U3.c);
  roundedDiamond(U3.c, 60, C.orange).setAttribute('transform', 'translate(150 265)');
  el('rect', { x: 70, y: 392, width: 160, height: 14, rx: 7, fill: C.white }, U3.c);
  el('rect', { x: 95, y: 420, width: 110, height: 10, rx: 5, fill: C.white, opacity: 0.5 }, U3.c);
  el('rect', { x: 80, y: 470, width: 140, height: 46, rx: 23, fill: C.orange }, U3.c);
  U3.W = 300; U3.H = 560;

  function placeUnit(u, r, rot, contentK, opacity = 1) {
    const [x, y, w, h] = r;
    set(u.r, { x, y, width: Math.max(1, w), height: Math.max(1, h), rx: Math.min(u.rx, w / 2, h / 2) });
    const s = Math.min(w / u.W, h / u.H);
    const cx = x + w / 2, cy = y + h / 2;
    set(u.c, { transform: `translate(${cx - (u.W * s) / 2} ${cy - (u.H * s) / 2}) scale(${s})`, opacity: contentK });
    set(u.g, { transform: `rotate(${rot} ${cx} ${cy})`, opacity });
    u.g.style.display = opacity <= 0.001 ? 'none' : '';
  }

  // ================================================================ SCENE 5: DESIGNER
  const badge = el('g', {}, world);
  const framePath = stroke(badge,
    'M470,2580 L204,2580 Q160,2580 160,2624 L160,3316 Q160,3360 204,3360 L876,3360 Q920,3360 920,3316 L920,2624 Q920,2580 876,2580 L610,2580',
    { stroke: C.navy, width: 3 });
  const corners = [[160, 2580], [920, 2580], [160, 3360], [920, 3360]].map(([x, y]) => {
    const n = roundedDiamond(badge, 18, C.orange);
    n.__x = x; n.__y = y;
    return n;
  });
  const phClip = id('ph');
  const phCircle = el('circle', { cx: 540, cy: 2850, r: 0 }, el('clipPath', { id: phClip, clipPathUnits: 'userSpaceOnUse' }, el('defs', {}, badge)));
  const phG = el('g', { 'clip-path': `url(#${phClip})` }, badge);
  el('circle', { cx: 540, cy: 2850, r: 172, fill: C.blue }, phG);
  const photo = el('image', { href: A.portrait, width: 380, height: 380, x: 350, y: 2660 }, phG);
  const phRing = stroke(badge, 'M540,2668 A182,182 0 1 1 539.9,2668', { stroke: C.blue, width: 4 });
  const badgeLogo = makeLogo(badge);
  const nameWipe = rtlWipe(badge, { x0: 120, x1: 960, y0: 3020, y1: 3200 });
  const nameText = rtlText(nameWipe.g, COPY.name, { x: 540, y: 3165, size: 124, weight: 700, fill: C.navy });
  const subtitle = maskLine(badge, COPY.title, { x: 540, y: 3262, size: 34, weight: 500, fill: C.blue });

  // ================================================================ SCENE 6: CTA
  const s6 = el('g', {}, world);
  const ctaFrameD = 'L830,3120 Q830,3150 800,3150 L280,3150 Q250,3150 250,3120 L250,2910 Q250,2880 280,2880 L800,2880 Q830,2880 830,2910';
  const ctaLeadD = 'M540,2656 C540,2770 830,2770 830,2900';
  const ctaLead = el('path', { d: ctaLeadD, fill: 'none', stroke: 'none' }, s6);
  const ctaLine = stroke(s6, `${ctaLeadD} ${ctaFrameD}`, { stroke: C.orange, width: 6 });
  const wordWipe = rtlWipe(s6, { x0: 260, x1: 820, y0: 2885, y1: 3145 });
  const wordG = el('g', {}, wordWipe.g);
  const wordText = rtlText(wordG, COPY.word, { x: 540, y: 3018, size: 190, weight: 700, fill: C.blue, baseline: 'central' });
  const cta = maskWords(s6, COPY.cta.split(' '), { x: 540, y: 3290, size: 70, weight: 700, fill: C.navy });
  const outroG = el('g', {}, s6);
  const outroA = maskLine(outroG, COPY.outroA, { y: 3392, size: 42, weight: 500, fill: C.navy, anchor: 'start' });
  const outroB = maskLine(outroG, COPY.outroB, { y: 3392, size: 42, weight: 700, fill: C.blue, anchor: 'start' });
  const wA = outroA.text.getComputedTextLength(), wB = outroB.text.getComputedTextLength();
  const gapAB = 13;
  const outroRight = 540 + (wA + gapAB + wB) / 2;
  set(outroA.text, { x: outroRight });
  set(outroB.text, { x: outroRight - wA - gapAB });
  const underline = stroke(s6, `M${outroRight - wA - gapAB},3412 L${outroRight - wA - gapAB - wB},3412`, { stroke: C.orange, width: 6 });

  const bubble = el('g', {}, s6);
  el('rect', { x: -60, y: -46, width: 120, height: 92, rx: 30, fill: C.orange }, bubble);
  el('path', { d: 'M-34,38 L-50,70 L-6,44 Z', fill: C.orange }, bubble);
  [-28, 0, 28].forEach((x) => el('circle', { cx: x, cy: 0, r: 8, fill: C.white }, bubble));

  // dalla sits above CTA elements once it becomes the sticker
  world.appendChild(dalla);

  // ================================================================ CAMERA
  const camX = track([[0, 540], [9, 540], [12, 575, E.inOut], [15.3, 540], [16.6, 620], [18, 540]]);
  const camY = track([[0, 545], [3.7, 545], [6.2, 960, E.out], [11.4, 960], [12.3, 1105], [13.1, 1085, E.lin], [14.3, 935], [15.3, 960], [18, 3100, E.inOut], [44, 3100], [46, 2960, E.inOut]]);
  const camZ = track([
    [0, 3.0], [2.6, 2.5, E.soft], [3.7, 2.9], [6.2, 1.0, E.out], [11.4, 1.02, E.lin], [12.3, 1.75], [13.1, 1.82, E.lin], [14.3, 0.98], [15.3, 1.04, E.lin],
    [16.6, 0.86], [18, 1], [21, 1.05], [23, 1], [36, 1, E.lin], [44, 1.04, E.lin], [46, 1],
  ]);
  const rotX = track([[0, 0], [18.6, 0], [20.4, 4], [22.6, 0]]);
  const rotY = track([[0, 0], [6.2, 0], [10, -3], [14, 2.5], [15.5, 0], [18.6, 0], [20.4, -3], [22.6, 0]]);

  // ================================================================ RENDER
  function renderMaster(t) {
    // ---- camera
    const cx = camX(t), cy = camY(t), z = camZ(t);
    set(world, { transform: `translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})` });
    const rx = rotX(t), ry = rotY(t);
    stage.style.transform = `perspective(2400px) rotateX(${rx}deg) rotateY(${ry}deg) scale(${1 + (Math.abs(rx) + Math.abs(ry)) * 0.012})`;
    const par = clamp((cy - 545) / 2555);
    set(bgMain, { transform: `translate(${(540 - cx) * 0.08} ${lerp(40, -40, par)})` });
    set(bgReveal, { opacity: p(t, 35.4, 38.4, E.inOut), transform: `translate(0 ${lerp(30, -30, p(t, 35, 53, E.lin))})` });

    // ---- scene 1: beans gather, hero bean becomes the dalla mouth
    const ring = 0.21 * t;
    const mouth = toWorld(0, -300);
    const hero = beans[0];
    {
      const grow = p(t, 2.8, 3.8, E.inOut);
      const s = 1 + grow * 0.5;
      const rot = -24 + 5 * t;
      set(hero.g, { transform: `translate(${mouth.x} ${mouth.y}) rotate(${rot * (1 - grow)}) scale(${s})`, opacity: 1 - p(t, 3.2, 3.8, E.lin) });
      trim(hero.crease, p(t, 2.9, 3.5, E.inOut), 1);
      hero.g.style.display = t > 3.85 ? 'none' : '';
      const mk = p(t, 3.0, 3.8, E.inOut);
      set(morph, {
        cx: mouth.x, cy: mouth.y,
        rx: lerp(36 * s, 72 * DS, mk), ry: lerp(50 * s, 13 * DS, mk),
        transform: `rotate(${rot * (1 - grow)} ${mouth.x} ${mouth.y})`,
        'stroke-width': lerp(5 * s, 5 * DS, mk),
        opacity: p(t, 2.8, 3.1, E.lin) * (t < 3.8 ? 1 : 0),
      });
    }
    const silL = silPath.__len || (silPath.__len = silPath.getTotalLength());
    for (let i = 1; i < 7; i++) {
      const b = beans[i];
      const a0 = (i - 1) * (Math.PI / 3);
      const enter = p(t, 0.45 + 0.2 * (i - 1), 2.3 + 0.2 * (i - 1), E.out);
      const r = lerp(620, 150, enter);
      const ang = a0 + ring + (1 - enter) * 1.9;
      let x = mouth.x + Math.cos(ang) * r, y = mouth.y + Math.sin(ang) * r;
      let rot = (ang * 180) / Math.PI + 90 + (1 - enter) * 120;
      let sc = 0.92;
      // ride the dalla silhouette
      const kc = p(t, 5.0 + 0.05 * i, 6.4 + 0.05 * i, E.inOut);
      if (kc > 0) {
        const u = ((i - 1) / 6 + 0.085 * Math.max(0, t - 5.0)) % 1;
        const pt = pointAt(silPath, u);
        const w = toWorld(pt.x, pt.y);
        x = lerp(x, w.x, kc); y = lerp(y, w.y, kc);
        rot = lerp(rot, pt.angle + 90, kc);
        sc = lerp(sc, 0.5, kc);
      }
      // gather into a rosette
      const j = i - 1;
      const kr = p(t, 6.7 + 0.08 * j, 7.9 + 0.08 * j, E.inOut);
      if (kr > 0) {
        const ra = j * (Math.PI / 3) - Math.PI / 2 + p(t, 7.9, 8.8, E.soft) * 0.14;
        const tx = 540 + Math.cos(ra) * 74, ty = 1390 + Math.sin(ra) * 74;
        x = lerp(x, tx, kr) + Math.sin(Math.PI * kr) * 90 * (j % 2 ? 1 : -1);
        y = lerp(y, ty, kr);
        rot = lerp(rot, (ra * 180) / Math.PI + 90, kr);
        sc = lerp(sc, 0.72, kr);
      }
      // withdraw toward the right edge
      const kx = p(t, 8.7 + 0.06 * j, 9.8 + 0.06 * j, E.in);
      x += kx * 820; y += -Math.sin(Math.PI * kx) * 80;
      rot += kx * 70;
      set(b.g, { transform: `translate(${x} ${y}) rotate(${rot}) scale(${sc})` });
      trim(b.crease, 0, 1);
      b.g.style.display = kx >= 1 ? 'none' : '';
    }

    // dalla outline
    const dPos = track([[0, [DX, DY, DS, 0]], [43.9, [DX, DY, DS, 0]], [44, [-280, 3010, 0.27, -6], E.lin], [46.4, [-280, 3010, 0.27, -6]], [47.8, [222, 3010, 0.27, 0], E.out], [48.8, [222, 3010, 0.27, 9], E.soft]])(t);
    set(dalla, { transform: `translate(${dPos[0]} ${dPos[1]}) rotate(${dPos[3]}) scale(${dPos[2]})` });
    dalla.style.display = t > 18.2 && t < 44 ? 'none' : '';
    set(dMouth, { opacity: t >= 3.8 ? 1 : 0 });
    // the small sticker version needs a bolder line to stay legible
    const sticker = p(t, 44, 45, E.lin);
    if (sticker > 0) {
      dalla.querySelectorAll('path[stroke], ellipse').forEach((n) => n.setAttribute('stroke-width', lerp(n === dHandleO ? 6 : 5, 11, sticker)));
    }
    const kC = p(t, 3.8, 5.9, E.soft);
    trim(dContourR, 0, kC); trim(dContourL, 0, kC);
    const kLid = p(t, 4.1, 5.0, E.inOut);
    trim(dLidR, 0, kLid); trim(dLidL, 0, kLid);
    const fin = p(t, 4.9, 5.5, E.settle);
    set(dFinial, { transform: `translate(0 -362) scale(${Math.max(0.001, fin)}) translate(0 362)`, opacity: clamp(fin * 2) });
    trim(dSpout, 0, p(t, 13.0, 13.8, E.inOut));
    trim(dHandleO, 0, p(t, 13.1, 14.0, E.inOut));
    trim(dHandleI, 0, p(t, 13.25, 14.1, E.inOut));
    dBands.forEach((b, i) => trim(b, 0, p(t, 13.5 + i * 0.12, 14.2 + i * 0.12, E.out)));
    const fillK = p(t, 12.6, 13.1, E.lin);
    set(dFill, { opacity: fillK }); set(dLidFill, { opacity: fillK });

    // coffee rises inside the dalla, its surface rocking gently
    const lvl = lerp(345, -110, p(t, 12.9, 14.5, E.soft));
    const wv = Math.sin(t * 2.2) * 7 * (1 - p(t, 49.5, 50.6, E.inOut));
    set(liquid, { d: `M-220,${lvl + wv} C-80,${lvl - 14 - wv} 80,${lvl + 14 + wv} 220,${lvl - wv} L220,360 L-220,360 Z` });
    set(liquidSurf, { d: `M-220,${lvl + wv} C-80,${lvl - 14 - wv} 80,${lvl + 14 + wv} 220,${lvl - wv}` });
    liquidG.style.display = t < 12.9 ? 'none' : '';

    // flame
    trim(flameLine, p(t, 11.95, 12.45, E.in), p(t, 11.5, 12.3, E.inOut));
    burner.forEach((b) => trim(b, 0, p(t, 12.0, 12.45, E.out)));
    const fireOn = t < 44 ? 1 : 0;
    const ig = p(t, 12.22, 12.85, E.settle) * fireOn;
    const breathe = (ph) => 1 + 0.06 * Math.sin(t * 2.0 + ph);
    const sx = (ph) => 7 * Math.sin(t * 1.6 + ph) * p(t, 12.5, 13.0, E.lin);
    set(flameG, { transform: `translate(0 ${FIRE_Y}) scale(${Math.max(0.001, ig)})` });
    flameG.style.display = ig <= 0.001 ? 'none' : '';
    set(flameSide[0], { d: tongue(78 * breathe(1.3), 22, sx(2)), transform: 'translate(-18 0) rotate(-20)' });
    set(flameSide[1], { d: tongue(86 * breathe(2.6), 24, sx(3)), transform: 'translate(18 0) rotate(18)' });
    set(flameOuter, { d: tongue(136 * breathe(0), 46, sx(0)) });
    set(flameMid, { d: tongue(98 * breathe(0.8), 32, sx(0.6)) });
    set(flameCore, { d: tongue(54 * breathe(1.7), 17, sx(1.2) * 0.6) });
    set(glow, { opacity: ig * (0.85 + 0.15 * Math.sin(t * 2.0)), r: 170 * breathe(0.4) });
    burner.forEach((b) => { b.style.display = fireOn ? '' : 'none'; });
    heat.forEach((h, i) => {
      const k = p(t, 12.7 + i * 0.16, 13.9 + i * 0.16, E.inOut);
      trim(h, Math.max(0, k - 0.3), k);
      h.setAttribute('opacity', 0.75 * (1 - p(t, 13.6 + i * 0.16, 13.9 + i * 0.16, E.lin)));
    });
    steam.forEach((st, i) => {
      const k = p(t, 13.9 + i * 0.2, 14.9 + i * 0.2, E.out);
      trim(st, Math.max(0, k - 0.45), k);
      st.style.opacity = 1 - p(t, 14.6 + i * 0.2, 15.1 + i * 0.2, E.lin);
    });

    // hook text
    hookL1.update(p(t, 4.7, 5.5, E.out), p(t, 6.1, 6.6, E.in));
    hookL2.update(p(t, 4.85, 5.65, E.out), p(t, 6.15, 6.65, E.in));

    // cardamom
    pods.forEach((pd, j) => {
      const enter = p(t, 8.9 + 0.07 * j, 9.9 + 0.07 * j, E.out);
      const d = j - 2;
      let x = lerp(-180, 540 + d * 150, enter), y = 1390 - (2 - Math.abs(d)) * 22 - Math.sin(Math.PI * enter) * 60;
      let sc = j === 2 ? 1.25 : 0.9;
      let rot = d * 14 + (1 - enter) * -60;
      let op = 1;
      if (j !== 2) {
        const ex = p(t, 10.5, 11.3, E.in);
        x += d * 140 * ex; op = 1 - ex;
      }
      set(pd.g, { transform: `translate(${x} ${y}) rotate(${rot}) scale(${sc})`, opacity: op });
      pd.g.style.display = t < 8.85 || op <= 0 ? 'none' : '';
      if (j === 2) {
        const open = p(t, 9.9, 10.6, E.out);
        set(pd.left, { transform: `translate(${-14 * open} 0) rotate(${-32 * open} 0 46)` });
        set(pd.right, { transform: `translate(${14 * open} 0) rotate(${32 * open} 0 46)` });
        set(pd.g, { opacity: 1 - p(t, 10.8, 11.3, E.lin) });
        pd.g.style.display = t < 8.85 || t > 11.3 ? 'none' : '';
      }
    });
    seeds.forEach((sd, s) => {
      const out = p(t, 10.05, 10.8, E.out);
      const a = (s * 2 * Math.PI) / 7 + out * 3.6;
      let x = 540 + Math.cos(a) * 78 * out, y = 1380 + Math.sin(a) * 78 * out;
      const row = p(t, 10.8 + 0.03 * s, 11.35 + 0.03 * s, E.inOut);
      x = lerp(x, 540 + (s - 3) * 38, row); y = lerp(y, 1440, row);
      const gone = p(t, 11.45 + Math.abs(s - 3) * 0.07, 11.8 + Math.abs(s - 3) * 0.07, E.in);
      const sc = clamp(out * 4) * (1 - gone);
      set(sd, { cx: x, cy: y, transform: `rotate(${a * 57.3 * (1 - row)} ${x} ${y}) scale(1)`, rx: 7 * sc, ry: 9 * sc });
      sd.style.display = t < 10.05 || gone >= 1 ? 'none' : '';
    });

    // labels
    const mk = p(t, 7.5, 8.0, E.settle) * (1 - p(t, 14.6, 15.0, E.in));
    const turn = p(t, 9.1, 9.6, E.inOut) + p(t, 11.5, 12.0, E.inOut);
    set(labelMark, { transform: `translate(540 ${lerp(1500, 1268, p(t, 11.3, 11.8, E.inOut))}) rotate(${turn * 90}) scale(${Math.max(0.001, mk)})` });
    lblBean.update(p(t, 7.7, 8.4, E.out), p(t, 8.75, 9.15, E.in));
    lblCard.update(p(t, 9.3, 10.0, E.out), p(t, 11.1, 11.45, E.in));
    lblFire.update(p(t, 11.75, 12.45, E.out), p(t, 14.6, 15.0, E.in));

    // ---- pour line → geometric line
    const pourL = pour.__len || (pour.__len = pour.getTotalLength());
    const curveF = (pourCurve.__len || (pourCurve.__len = pourCurve.getTotalLength())) / pourL;
    const head = p(t, 15.0, 17.6, E.inOut);
    const tail = p(t, 15.7, 17.9, E.inOut) * curveF;
    trim(pour, tail, head);
    const lineK = p(t, 16.4, 17.6, E.inOut);
    set(pour, { stroke: mixHex(C.blue, C.navy, lineK), 'stroke-width': lerp(6, 2.5, lineK), opacity: 1 - p(t, 21.0, 22.0, E.lin) * 0.55 - p(t, 23.4, 24.2, E.lin) * 0.45 });
    pour.style.display = t < 15 || t > 24.3 ? 'none' : '';

    // ---- grid
    const gridOp = 1 - p(t, 21.0, 22.0, E.inOut) * 0.6 - p(t, 23.4, 24.2, E.inOut) * 0.4;
    set(gridG, { opacity: gridOp });
    gridG.style.display = t < 16.9 || gridOp <= 0 ? 'none' : '';
    vLines.forEach((ln, k) => trim(ln, 0, p(t, 17.0 + (6 - k) * 0.08, 17.75 + (6 - k) * 0.08, E.out)));
    hLines.forEach((ln, k) => trim(ln, 0, p(t, 17.3 + k * 0.07, 18.1 + k * 0.07, E.out)));

    const s3out = p(t, 23.4, 24.2, E.in);
    set(s3, { opacity: 1 - s3out, transform: `translate(540 3100) scale(${1 - s3out * 0.06}) translate(-540 -3100)` });
    s3.style.display = t < 17 || s3out >= 1 ? 'none' : '';
    eyebrow1.update(p(t, 17.9, 18.5, E.out), p(t, 20.3, 20.7, E.in));
    eyebrow2.update(p(t, 20.6, 21.2, E.out));
    head1.update(p(t, 18.2, 18.95, E.out), p(t, 20.3, 20.8, E.in));
    head2.update(p(t, 20.6, 21.35, E.out));
    bars.forEach((b, i) => {
      const k = p(t, 18.6 + i * 0.09, 19.3 + i * 0.09, E.out);
      const w = [640, 520, 380][i] * k;
      set(b, { x: 940 - w, width: Math.max(0, w) });
    });
    footBars.forEach((b, i) => {
      const k = p(t, 19.4 + i * 0.1, 20.1 + i * 0.1, E.out);
      const w = [820, 600][i] * k;
      set(b, { x: 940 - w, width: Math.max(0, w) });
    });

    // elements → palette swatches
    const pop1 = p(t, 19.2, 19.85, E.settle), pop2 = p(t, 19.35, 20.0, E.settle), pop3 = p(t, 19.5, 20.15, E.settle);
    const sw2k = p(t, 20.6, 21.4, E.inOut);
    set(elCircle, { cx: lerp(190, 165, sw2k), cy: lerp(3045, 3060, sw2k), r: Math.max(0, lerp(56, 38, sw2k) * pop1) });
    const sq = lerp(105, 76, sw2k) * pop2, sqc = [lerp(332, 260, sw2k), lerp(3042, 3060, sw2k)];
    set(elSquare, { x: sqc[0] - sq / 2, y: sqc[1] - sq / 2, width: Math.max(0, sq), height: Math.max(0, sq), rx: lerp(14, 38, sw2k) * pop2, fill: mixHex(C.navy, C.blue, sw2k) });
    set(elSwatch3, { cx: 355, cy: 3060, r: 38 * p(t, 21.1, 21.7, E.settle) });
    const pillOut = p(t, 20.7, 21.2, E.in);
    const pw = 240 * pop3 * (1 - pillOut);
    set(elPill, { x: 260 - pw / 2, y: 3240, width: Math.max(0, pw), height: 74, rx: 37, opacity: pop3 > 0 ? 1 : 0 });
    set(elDot, { r: 9 * p(t, 19.7, 20.2, E.settle) });
    specimen.update(p(t, 21.05, 21.8, E.out));

    // image block → brand block → board
    const toBoard = p(t, 23.6, 25.0, E.inOut);
    const bx = lerp(550, 190, toBoard), by = lerp(2972, 2700, toBoard), bw = lerp(390, 700, toBoard), bh = lerp(393, 875, toBoard);
    const reveal = p(t, 18.9, 19.6, E.out);
    const split = p(t, 26.0, 26.35, E.in);
    set(blockRect, { x: bx, y: by + bh * (1 - reveal), width: bw, height: bh * reveal });
    set(block, { opacity: 1 - split });
    block.style.display = t < 18.9 || split >= 1 ? 'none' : '';
    const bcx = bx + bw / 2, bcy = by + bh / 2;
    set(blockGlyph, { transform: `translate(${bcx} ${bcy + 10}) scale(${bw / 390})`, opacity: reveal * (1 - p(t, 20.6, 21.0, E.lin)) });
    const lp = p(t, 20.9, 21.8, E.out);
    blockLogo.place(bcx, lerp(bcy, by + bh * 0.42, toBoard), lerp(240, 430, toBoard), p(t, 20.9, 21.6, E.out), p(t, 21.3, 22.0, E.settle), lp);
    const det = p(t, 24.6, 25.4, E.out);
    set(blockInset, { x: bx + 28, y: by + 28, width: Math.max(0, bw - 56), height: Math.max(0, bh - 56), opacity: det });
    blockBars.forEach((b, i) => {
      const w = bw * [0.62, 0.42][i] * det;
      set(b, { x: bcx - w / 2, y: by + bh * 0.78 + i * 36, width: Math.max(0, w), height: i ? 12 : 18, opacity: i ? 0.3 : 0.85 });
    });

    // ---- scene 4: three applications
    headline.update(t, 25.9, 0.14, 0.75, 31.0);
    valueLine.update(p(t, 28.0, 28.75, E.out), p(t, 31.1, 31.6, E.in));

    const thirds = [[190, 2700, 700, 292], [190, 2992, 700, 292], [190, 3284, 700, 291]];
    const gap = p(t, 26.0, 26.35, E.out) * 8;
    const shrink = p(t, 31.0, 33.8, E.inOut);
    const recede = p(t, 36.0, 37.0, E.soft);
    const unitsOut = p(t, 44.0, 44.8, E.in);
    const go = p(t, 26.3, 27.6, E.inOut);
    const ali = p(t, 28.2, 29.4, E.inOut);
    function lerpR(a, b, k) { return a.map((v, i) => lerp(v, b[i], k)); }
    function inset(r, g) { return [r[0], r[1] + g, r[2], r[3] - g * 2]; }
    function rec(r, k) {
      const s = 1 - k * 0.22, cx = r[0] + r[2] / 2, cy = r[1] + r[3] / 2;
      return [cx - (r[2] * s) / 2, cy - (r[3] * s) / 2, r[2] * s, r[3] * s];
    }
    const unitOp = (t < 26.0 ? 0 : 1) * (1 - recede * 0.75) * (1 - unitsOut);
    unitsG.style.display = t < 26.0 || unitsOut >= 1 ? 'none' : '';
    // U1 slides into place
    {
      let r = lerpR(inset(thirds[0], gap), [480, 2700, 460, 460], go);
      r = lerpR(r, [860, 2410, 150, 150], shrink);
      placeUnit(U1, rec(r, recede), 0, p(t, 27.0, 27.7, E.lin), unitOp);
    }
    // U2 rotates slightly
    {
      let r = lerpR(inset(thirds[2], gap), [330, 3290, 560, 320], go);
      r = lerpR(r, [380, 3220, 560, 320], ali);
      r = lerpR(r, [600, 3420, 340, 194], shrink);
      const rot = lerp(0, -6, p(t, 26.6, 27.8, E.out)) * (1 - ali) + shrink * 4;
      placeUnit(U2, rec(r, recede), rot, p(t, 27.1, 27.8, E.lin), unitOp);
    }
    // U3 expands to reveal its detail
    {
      const ex = p(t, 27.0, 28.1, E.out);
      let r = lerpR(inset(thirds[1], gap), [215, 2900, 150, 280], go);
      r = lerpR(r, [140, 2700, 300, 560], ex);
      r = lerpR(r, [70, 2370, 100, 187], shrink);
      placeUnit(U3, rec(r, recede), 0, p(t, 27.5, 28.2, E.lin), unitOp);
    }
    const conK = p(t, 28.8, 29.8, E.inOut), conOut = p(t, 30.8, 31.6, E.inOut);
    trim(conA, conOut, conK); trim(conB, conOut, conK);
    connectors.style.display = t < 28.8 || conOut >= 1 ? 'none' : '';
    nodes.forEach((n, i) => {
      const k = p(t, 29.2 + i * 0.12, 29.8 + i * 0.12, E.settle) * (1 - conOut);
      set(n, { transform: `translate(${n.__x} ${n.__y}) scale(${Math.max(0.001, k)})` });
    });

    // ---- scene 5: frame, portrait, name
    const fr = lerp(0, 0.45, p(t, 33.6, 36.2, E.inOut)) + 0.4 * p(t, 36.4, 39.0, E.inOut) + 0.15 * p(t, 42.2, 43.3, E.inOut);
    trim(framePath, 0, fr);
    badge.style.display = t < 33.6 ? 'none' : '';
    corners.forEach((n, i) => {
      const k = p(t, 42.7 + i * 0.1, 43.3 + i * 0.1, E.settle);
      set(n, { transform: `translate(${n.__x} ${n.__y}) scale(${Math.max(0.001, k)})` });
    });
    const ph = p(t, 36.5, 37.8, E.out);
    set(phCircle, { r: 172 * ph });
    const phs = lerp(1.2, 1, ph);
    set(photo, { transform: `translate(540 2850) scale(${phs}) translate(-540 -2850)` });
    trim(phRing, 0, p(t, 37.2, 38.3, E.inOut));
    badgeLogo.place(540, 2580, 118, p(t, 38.2, 38.9, E.out), p(t, 38.6, 39.3, E.settle), t < 38.2 ? 0 : 1);
    const nk = p(t, 36.9, 38.2, E.soft);
    nameWipe.update(nk);
    set(nameText, { transform: `translate(0 ${(1 - nk) * 24})` });
    subtitle.update(p(t, 38.8, 39.6, E.out));

    // ---- scene 6: badge rises, CTA takes over
    const up = p(t, 44.0, 45.2, E.inOut);
    const bs = lerp(1, 0.4, up), bty = lerp(2970, 2500, up);
    set(badge, { transform: `translate(540 ${bty}) scale(${bs}) translate(-540 -2970)` });

    s6.style.display = t < 44.8 ? 'none' : '';
    const ctaL = ctaLine.__len || (ctaLine.__len = ctaLine.getTotalLength());
    const ctaLeadF = (ctaLead.__len || (ctaLead.__len = ctaLead.getTotalLength())) / ctaL;
    trim(ctaLine, p(t, 45.7, 46.6, E.inOut) * ctaLeadF, p(t, 44.9, 46.2, E.inOut));
    const wk = p(t, 45.3, 46.2, E.out);
    wordWipe.update(wk);
    const wsc = lerp(0.92, 1, p(t, 45.3, 46.6, E.out));
    set(wordG, { transform: `translate(540 3015) scale(${wsc}) translate(-540 -3015)` });
    cta.update(t, 46.4, 0.16, 0.7);
    outroA.update(p(t, 47.4, 48.15, E.out));
    outroB.update(p(t, 47.55, 48.3, E.out));
    trim(underline, 0, p(t, 48.7, 49.5, E.inOut));

    const bk = p(t, 45.9, 46.9, E.inOut);
    const bp = pointAt(ctaLead, bk);
    const land = p(t, 46.7, 47.3, E.settle);
    const bxp = lerp(bp.x, 846, land), byp = lerp(bp.y, 2862, land);
    const bRot = lerp(bp.angle - 90, 0, land);
    set(bubble, { transform: `translate(${bxp} ${byp}) rotate(${bRot}) scale(${0.35 + 0.65 * p(t, 45.9, 46.7, E.out)})` });
    bubble.style.display = t < 45.9 ? 'none' : '';
  }

  const render = (t) => renderMaster(retime(t));

  window.FILM = { render, DURATION, W, H };
})();
