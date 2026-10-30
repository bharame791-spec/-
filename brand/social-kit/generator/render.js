// مولّد خلفيات السوشيال ميديا لهوية رام.
// التشغيل: node brand/social-kit/generator/render.js
// المخرجات: brand/social-kit/{backgrounds,glass-backgrounds,glass-shapes}

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { SHAPES, sparkle } = require('./shapes');

const ROOT = path.resolve(__dirname, '..');
const ASSETS = path.resolve(ROOT, '../assets');
const symbolWhite = 'data:image/png;base64,' + fs.readFileSync(path.join(ASSETS, 'ram-symbol-mono-white.png')).toString('base64');

// ألوان الهوية
const C = {
  night: '#071530', deep: '#0B1E48', navy: '#102A62', royal: '#2F5089',
  sky: '#5D7FB8', steel: '#939FAD', silver: '#E9EDF3', white: '#FFFFFF',
};
const rgba = (hex, a) => {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`;
};

const SIZES = {
  post: [1080, 1350],   // 4:5 منشور إنستغرام / فيسبوك
  square: [1080, 1080], // 1:1
  story: [1080, 1920],  // 9:16 ستوري / ريلز
};

const GRAIN = `url("data:image/svg+xml;utf8,${encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="260" height="260"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#n)"/></svg>'
)}")`;

// ---------- الخلفيات المتدرجة ----------
// كل خلفية: طبقات CSS + عناصر إضافية اختيارية (أشعة، أقواس، شبكة، رمز).
const BACKGROUNDS = {
  '01-deep-night': {
    name: 'ليل عميق',
    css: () => `
      radial-gradient(70% 45% at 50% 0%, ${rgba(C.royal, 0.75)}, transparent 70%),
      radial-gradient(60% 40% at 0% 100%, ${rgba(C.steel, 0.28)}, transparent 70%),
      linear-gradient(170deg, ${C.deep} 0%, ${C.night} 100%)`,
    extra: (w, h) => beam(w, h, -32, 0.55, 0.07) ,
  },
  '02-royal': {
    name: 'أزرق ملكي',
    css: () => `
      radial-gradient(65% 50% at 100% 0%, ${rgba(C.sky, 0.55)}, transparent 70%),
      radial-gradient(50% 35% at 0% 85%, ${rgba(C.night, 0.7)}, transparent 75%),
      linear-gradient(150deg, ${C.royal} 0%, ${C.navy} 50%, ${C.night} 100%)`,
    extra: (w, h) => beam(w, h, -38, 0.35, 0.06),
  },
  '03-steel-glow': {
    name: 'وهج فولاذي',
    css: () => `
      radial-gradient(75% 55% at 0% 100%, ${rgba(C.steel, 0.7)}, transparent 70%),
      radial-gradient(40% 30% at 5% 98%, ${rgba(C.silver, 0.35)}, transparent 70%),
      radial-gradient(55% 40% at 100% 0%, ${rgba(C.royal, 0.55)}, transparent 70%),
      linear-gradient(165deg, ${C.navy} 0%, ${C.deep} 45%, ${C.night} 100%)`,
    extra: (w, h) => beam(w, h, -40, 0.72, 0.08),
  },
  '04-silver-dawn': {
    name: 'فجر فضي (فاتح)',
    light: true,
    css: () => `
      radial-gradient(70% 45% at 50% 0%, ${rgba(C.white, 0.95)}, transparent 70%),
      radial-gradient(70% 50% at 100% 100%, ${rgba(C.royal, 0.38)}, transparent 70%),
      radial-gradient(50% 40% at 0% 70%, ${rgba(C.steel, 0.35)}, transparent 70%),
      linear-gradient(170deg, #F4F6FA 0%, ${C.silver} 45%, #C9D2DF 100%)`,
    extra: (w, h) => beam(w, h, -35, 0.6, 0.35, C.white),
  },
  '05-wave': {
    name: 'موجة',
    css: () => `
      radial-gradient(60% 45% at 15% 85%, ${rgba(C.royal, 0.7)}, transparent 70%),
      radial-gradient(50% 35% at 90% 10%, ${rgba(C.sky, 0.3)}, transparent 70%),
      linear-gradient(160deg, ${C.deep} 0%, ${C.night} 100%)`,
    extra: (w, h) => arcs(w, h),
  },
  '06-grid': {
    name: 'شبكة إحداثيات',
    css: () => `
      radial-gradient(65% 45% at 50% 40%, ${rgba(C.royal, 0.6)}, transparent 75%),
      linear-gradient(180deg, ${C.navy} 0%, ${C.night} 100%)`,
    extra: (w, h) => grid(w, h),
  },
  '07-symbol': {
    name: 'الرمز',
    css: () => `
      radial-gradient(60% 45% at 85% 20%, ${rgba(C.sky, 0.45)}, transparent 70%),
      radial-gradient(70% 50% at 0% 100%, ${rgba(C.steel, 0.3)}, transparent 70%),
      linear-gradient(155deg, ${C.royal} 0%, ${C.navy} 45%, ${C.night} 100%)`,
    extra: (w, h) => `<img src="${symbolWhite}" style="position:absolute;height:${h * 0.95}px;right:${-w * 0.2}px;top:${h * 0.08}px;opacity:.07">`,
  },
  '08-beams': {
    name: 'أشعة',
    css: () => `
      radial-gradient(55% 40% at 0% 100%, ${rgba(C.sky, 0.45)}, transparent 70%),
      radial-gradient(60% 40% at 100% 0%, ${rgba(C.royal, 0.45)}, transparent 70%),
      linear-gradient(175deg, ${C.deep} 0%, ${C.night} 100%)`,
    extra: (w, h) => beam(w, h, -42, 0.62, 0.1) + beam(w, h, -42, 0.8, 0.06) + beam(w, h, -42, 0.25, 0.04),
  },
};

function beam(w, h, deg, pos, a, color = C.white) {
  // شريط ضوئي مائل ناعم
  const bw = Math.max(w, h) * 0.22;
  return `<div style="position:absolute;left:${w * pos - bw / 2}px;top:${-h * 0.5}px;width:${bw}px;height:${h * 2}px;
    transform:rotate(${deg}deg);background:linear-gradient(90deg,transparent,${rgba(color, a)},transparent);filter:blur(${w * 0.03}px)"></div>`;
}

function arcs(w, h) {
  // أقواس متحدة المركز تستعيد انحناءة الرمز
  const cx = w * 0.1, cy = h * 0.95;
  let s = '';
  for (let i = 0; i < 9; i++) {
    const r = w * (0.35 + i * 0.12);
    s += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${rgba(C.white, 0.13 - i * 0.011)}" stroke-width="${i % 3 === 0 ? 2 : 1}"/>`;
  }
  s += `<circle cx="${cx}" cy="${cy}" r="${w * 0.59}" fill="none" stroke="${rgba(C.steel, 0.45)}" stroke-width="3" stroke-dasharray="${w * 0.5} ${w * 4}" stroke-linecap="round" transform="rotate(-80 ${cx} ${cy})"/>`;
  return `<svg width="${w}" height="${h}" style="position:absolute;inset:0">${s}</svg>`;
}

function grid(w, h) {
  // شبكة خرائط عسكرية بتلاشٍ دائري + علامات تصويب
  const step = w / 12;
  let s = '';
  for (let x = step; x < w; x += step) s += `<line x1="${x}" y1="0" x2="${x}" y2="${h}"/>`;
  for (let y = step; y < h; y += step) s += `<line x1="0" y1="${y}" x2="${w}" y2="${y}"/>`;
  const cross = (x, y) => `<g stroke="${rgba(C.white, 0.35)}" stroke-width="2"><line x1="${x - 14}" y1="${y}" x2="${x + 14}" y2="${y}"/><line x1="${x}" y1="${y - 14}" x2="${x}" y2="${y + 14}"/></g>`;
  return `<svg width="${w}" height="${h}" style="position:absolute;inset:0;-webkit-mask-image:radial-gradient(70% 55% at 50% 45%,#000 30%,transparent 100%)">
    <g stroke="${rgba(C.white, 0.07)}" stroke-width="1">${s}</g>
    ${cross(step * 2, step * 2)}${cross(w - step * 2, step * 2)}${cross(step * 2, h - step * 2)}${cross(w - step * 2, h - step * 2)}
    <circle cx="${w / 2}" cy="${h * 0.45}" r="${w * 0.3}" fill="none" stroke="${rgba(C.white, 0.06)}" stroke-width="1.5"/>
    <circle cx="${w / 2}" cy="${h * 0.45}" r="${w * 0.42}" fill="none" stroke="${rgba(C.white, 0.05)}" stroke-width="1" stroke-dasharray="4 10"/>
  </svg>`;
}

function bgLayer(id, w, h) {
  const b = BACKGROUNDS[id];
  return `<div style="position:absolute;inset:0;background:${b.css()};overflow:hidden">${b.extra ? b.extra(w, h) : ''}</div>`;
}
const grainLayer = (light) => `<div style="position:absolute;inset:0;background-image:${GRAIN};mix-blend-mode:${light ? 'multiply' : 'overlay'};opacity:${light ? 0.07 : 0.16}"></div>`;

// ---------- الزجاج ----------
let gid = 0;
function glass(shape, x, y, w, h, mode = 'dark', extra = {}) {
  const d = SHAPES[shape](w, h);
  const id = 'g' + gid++;
  const fill = {
    dark: `linear-gradient(150deg, ${rgba(C.white, 0.21)}, ${rgba(C.white, 0.06)} 55%, ${rgba(C.white, 0.11)})`,
    light: `linear-gradient(150deg, ${rgba(C.white, 0.62)}, ${rgba(C.white, 0.32)} 60%, ${rgba(C.white, 0.45)})`,
    accent: `linear-gradient(150deg, ${rgba(C.sky, 0.95)}, ${rgba(C.royal, 0.95)} 50%, ${rgba(C.navy, 0.95)})`,
    steel: `linear-gradient(150deg, ${rgba('#B9C3CF', 0.95)}, ${rgba(C.steel, 0.95)} 60%, ${rgba('#7A8696', 0.95)})`,
  }[mode];
  const rimA = mode === 'light' ? 1 : 0.75;
  return `<div style="position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px">
    <svg width="${w}" height="${h}" style="position:absolute;inset:0;overflow:visible">
      <defs><filter id="s${id}" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="22"/></filter></defs>
      <path d="${d}" fill="${rgba('#020818', mode === 'light' ? 0.12 : 0.4)}" transform="translate(0 22)" filter="url(#s${id})"/>
    </svg>
    <div style="position:absolute;inset:0;clip-path:path('${d}');backdrop-filter:blur(${extra.blur ?? 26}px) saturate(150%);-webkit-backdrop-filter:blur(${extra.blur ?? 26}px) saturate(150%);background:${fill}"></div>
    <svg width="${w}" height="${h}" style="position:absolute;inset:0;overflow:visible">
      <defs>
        <linearGradient id="r${id}" x1="1" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#fff" stop-opacity="${rimA}"/>
          <stop offset=".45" stop-color="#fff" stop-opacity="${rimA * 0.16}"/>
          <stop offset=".75" stop-color="#fff" stop-opacity="${rimA * 0.06}"/>
          <stop offset="1" stop-color="#fff" stop-opacity="${rimA * 0.45}"/>
        </linearGradient>
      </defs>
      <path d="${d}" fill="none" stroke="url(#r${id})" stroke-width="2"/>
    </svg>
  </div>`;
}
function glow(x, y, r, color, a) {
  return `<div style="position:absolute;left:${x - r}px;top:${y - r}px;width:${r * 2}px;height:${r * 2}px;border-radius:50%;background:radial-gradient(circle,${rgba(color, a)},transparent 70%)"></div>`;
}
function sparkles(list) {
  return `<svg width="1080" height="1350" style="position:absolute;inset:0;overflow:visible">${list
    .map(([x, y, s, a]) => `<path d="${sparkle(x, y, s)}" fill="none" stroke="${rgba(C.white, a)}" stroke-width="2.2" stroke-linejoin="round"/>`)
    .join('')}</svg>`;
}

// ---------- تراكيب زجاجية جاهزة (1080×1350) ----------
const COMPOSITIONS = {
  'glass-01-speaker': {
    name: 'بطاقة متحدث',
    bg: '03-steel-glow',
    body: () =>
      glow(700, 620, 380, C.sky, 0.35) +
      glass('notchPanel', 330, 470, 600, 500) +
      glass('photoFrame', 150, 430, 400, 440, 'dark', { blur: 18 }) +
      glass('tile', 150, 820, 190, 190, 'accent') +
      glass('pill', 640, 700, 250, 62) +
      glass('pill', 640, 830, 250, 62) +
      sparkles([[560, 395, 26, 0.6], [520, 425, 13, 0.45]]),
  },
  'glass-02-quote': {
    name: 'اقتباس',
    bg: '08-beams',
    body: () =>
      glow(560, 600, 420, C.royal, 0.5) +
      glass('quoteBubble', 140, 300, 800, 660) +
      glass('rhombus', 210, 610, 120, 120, 'accent') +
      sparkles([[640, 220, 30, 0.65], [600, 255, 15, 0.5]]),
  },
  'glass-03-breaking': {
    name: 'خبر عاجل',
    bg: '01-deep-night',
    body: () =>
      glow(540, 420, 420, C.sky, 0.3) +
      glass('photoFrame', 80, 160, 920, 640, 'dark', { blur: 14 }) +
      glow(300, 1050, 360, C.royal, 0.6) +
      glass('tabBanner', 80, 850, 920, 380) +
      glass('pill', 760, 870, 210, 58, 'steel'),
  },
  'glass-04-study-cover': {
    name: 'غلاف دراسة',
    bg: '07-symbol',
    body: () =>
      glow(500, 800, 420, C.sky, 0.35) +
      glass('pill', 680, 380, 280, 66) +
      glass('notchPanel', 120, 480, 840, 600) +
      glass('rhombus', 120, 1110, 90, 90, 'steel') +
      sparkles([[200, 400, 24, 0.55]]),
  },
  'glass-05-infographic': {
    name: 'إنفوغراف / أرقام',
    bg: '06-grid',
    body: () =>
      glow(540, 680, 460, C.royal, 0.5) +
      glass('pill', 290, 190, 500, 76) +
      glass('tile', 110, 340, 410, 380) +
      glass('tile', 560, 340, 410, 380) +
      glass('tile', 110, 760, 410, 380) +
      glass('tile', 560, 760, 410, 380, 'accent'),
  },
  'glass-06-light-card': {
    name: 'بطاقة فاتحة',
    bg: '04-silver-dawn',
    light: true,
    body: () =>
      glow(760, 980, 380, C.royal, 0.35) +
      glow(260, 380, 300, C.steel, 0.45) +
      glass('quoteBubble', 140, 280, 800, 700, 'light') +
      glass('tile', 200, 1080, 130, 130, 'accent'),
  },
};

// ---------- الإخراج ----------
const page = (w, h, inner, transparent = false) => `<!doctype html><html><head><meta charset="utf-8"><style>
  html,body{margin:0;width:${w}px;height:${h}px;overflow:hidden;background:${transparent ? 'transparent' : '#000'}}
  .c{position:relative;width:${w}px;height:${h}px;overflow:hidden}
</style></head><body><div class="c">${inner}</div></body></html>`;

function shapeSVG(shape, w, h, mode) {
  const d = SHAPES[shape](w, h);
  const pad = 2;
  const fills = {
    dark: [['#fff', 0.21], ['#fff', 0.06], ['#fff', 0.11]],
    light: [['#fff', 0.62], ['#fff', 0.32], ['#fff', 0.45]],
  }[mode];
  const rimA = mode === 'light' ? 1 : 0.75;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w + pad * 2}" height="${h + pad * 2}" viewBox="${-pad} ${-pad} ${w + pad * 2} ${h + pad * 2}">
  <defs>
    <linearGradient id="fill" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="${fills[0][0]}" stop-opacity="${fills[0][1]}"/>
      <stop offset=".55" stop-color="${fills[1][0]}" stop-opacity="${fills[1][1]}"/>
      <stop offset="1" stop-color="${fills[2][0]}" stop-opacity="${fills[2][1]}"/>
    </linearGradient>
    <linearGradient id="rim" x1="1" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="${rimA}"/>
      <stop offset=".45" stop-color="#fff" stop-opacity="${(rimA * 0.16).toFixed(2)}"/>
      <stop offset=".75" stop-color="#fff" stop-opacity="${(rimA * 0.06).toFixed(2)}"/>
      <stop offset="1" stop-color="#fff" stop-opacity="${(rimA * 0.45).toFixed(2)}"/>
    </linearGradient>
  </defs>
  <path d="${d}" fill="url(#fill)"/>
  <path d="${d}" fill="none" stroke="url(#rim)" stroke-width="2"/>
</svg>
`;
}

const SHAPE_EXPORTS = [
  ['notchPanel', 600, 500, 'panel-notched'],
  ['quoteBubble', 800, 660, 'quote-bubble'],
  ['photoFrame', 400, 440, 'photo-frame'],
  ['tabBanner', 920, 380, 'news-banner'],
  ['pill', 300, 70, 'pill'],
  ['tile', 300, 300, 'tile'],
  ['rhombus', 200, 200, 'rhombus'],
];

(async () => {
  const outBg = path.join(ROOT, 'backgrounds');
  const outGlass = path.join(ROOT, 'glass-backgrounds');
  const outShapes = path.join(ROOT, 'glass-shapes');
  for (const d of [outBg, outGlass, outShapes]) fs.mkdirSync(d, { recursive: true });

  const browser = await chromium.launch();
  const ctx = await browser.newContext({ deviceScaleFactor: 1 });
  const p = await ctx.newPage();

  for (const id of Object.keys(BACKGROUNDS)) {
    for (const [size, [w, h]] of Object.entries(SIZES)) {
      await p.setViewportSize({ width: w, height: h });
      await p.setContent(page(w, h, bgLayer(id, w, h) + grainLayer(BACKGROUNDS[id].light)));
      await p.screenshot({ path: path.join(outBg, `ram-bg-${id}-${size}.jpg`), type: 'jpeg', quality: 94 });
    }
  }

  for (const [id, c] of Object.entries(COMPOSITIONS)) {
    await p.setViewportSize({ width: 1080, height: 1350 });
    await p.setContent(page(1080, 1350, bgLayer(c.bg, 1080, 1350) + c.body() + grainLayer(c.light)));
    await p.screenshot({ path: path.join(outGlass, `ram-${id}.jpg`), type: 'jpeg', quality: 94 });
  }

  // أشكال منفصلة: SVG قابل للتعديل + PNG شفاف بدقة مضاعفة
  const ctx2 = await browser.newContext({ deviceScaleFactor: 2 });
  const p2 = await ctx2.newPage();
  for (const [shape, w, h, name] of SHAPE_EXPORTS) {
    for (const mode of ['dark', 'light']) {
      const svg = shapeSVG(shape, w, h, mode);
      const file = `ram-glass-${name}-${mode === 'dark' ? 'for-dark-bg' : 'for-light-bg'}`;
      fs.writeFileSync(path.join(outShapes, file + '.svg'), svg);
      await p2.setViewportSize({ width: w + 4, height: h + 4 });
      await p2.setContent(page(w + 4, h + 4, svg, true));
      await p2.screenshot({ path: path.join(outShapes, file + '.png'), omitBackground: true });
    }
  }
  const sp = `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><path d="${sparkle(100, 100, 90)}" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round"/></svg>\n`;
  fs.writeFileSync(path.join(outShapes, 'ram-sparkle.svg'), sp);

  await browser.close();
  console.log('done');
})();
