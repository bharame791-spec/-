// أشكال الزجاج لهوية رام — كل شكل مضلّع بزوايا مستديرة يُحوَّل إلى مسار SVG.
// الإحداثيات بالبكسل ضمن صندوق w×h.

function roundedPath(points, r) {
  const n = points.length;
  const seg = [];
  for (let i = 0; i < n; i++) {
    const P = points[i], A = points[(i - 1 + n) % n], B = points[(i + 1) % n];
    const da = Math.hypot(A[0] - P[0], A[1] - P[1]);
    const db = Math.hypot(B[0] - P[0], B[1] - P[1]);
    const rr = Math.min(r, da / 2, db / 2);
    const p1 = [P[0] + (A[0] - P[0]) * rr / da, P[1] + (A[1] - P[1]) * rr / da];
    const p2 = [P[0] + (B[0] - P[0]) * rr / db, P[1] + (B[1] - P[1]) * rr / db];
    seg.push({ p1, P, p2 });
  }
  const f = (v) => v.toFixed(1);
  let d = `M${f(seg[0].p2[0])} ${f(seg[0].p2[1])}`;
  for (let i = 1; i <= n; i++) {
    const s = seg[i % n];
    d += ` L${f(s.p1[0])} ${f(s.p1[1])} Q${f(s.P[0])} ${f(s.P[1])} ${f(s.p2[0])} ${f(s.p2[1])}`;
  }
  return d + ' Z';
}

const SHAPES = {
  // لوحة بدرجة مائلة على جانبها الأيسر (بطاقة المتحدث)
  notchPanel: (w, h) => roundedPath([[w * 0.22, 0], [w, 0], [w, h], [0, h], [0, h * 0.6], [w * 0.22, h * 0.4]], 38),
  // فقاعة اقتباس بذيل في الأسفل
  quoteBubble: (w, h) => roundedPath([[0, 0], [w, 0], [w, h * 0.86], [w * 0.9, h * 0.86], [w * 0.93, h], [w * 0.78, h * 0.86], [0, h * 0.86]], 40),
  // إطار صورة بزاوية مشطوفة
  photoFrame: (w, h) => roundedPath([[0, 0], [w, 0], [w, h], [w * 0.2, h], [0, h - w * 0.2]], 34),
  // شريط سفلي بلسان علوي (لعنوان الخبر ووسم «عاجل»)
  tabBanner: (w, h) => roundedPath([[0, h * 0.26], [w * 0.6, h * 0.26], [w * 0.66, 0], [w, 0], [w, h], [0, h]], 32),
  // كبسولة لوسوم التصنيف والتاريخ
  pill: (w, h) => roundedPath([[0, 0], [w, 0], [w, h], [0, h]], h / 2),
  // مربع أيقونة / رقم
  tile: (w, h) => roundedPath([[0, 0], [w, 0], [w, h], [0, h]], Math.min(w, h) * 0.22),
  // معيّن مستلهم من رأس الميم في الرمز
  rhombus: (w, h) => roundedPath([[w / 2, 0], [w, h / 2], [w / 2, h], [0, h / 2]], Math.min(w, h) * 0.12),
};

// نجمة رباعية (لمعة)
function sparkle(cx, cy, s) {
  const k = s * 0.16;
  return `M${cx} ${cy - s} C${cx + k} ${cy - k} ${cx + k} ${cy - k} ${cx + s} ${cy} C${cx + k} ${cy + k} ${cx + k} ${cy + k} ${cx} ${cy + s} C${cx - k} ${cy + k} ${cx - k} ${cy + k} ${cx - s} ${cy} C${cx - k} ${cy - k} ${cx - k} ${cy - k} ${cx} ${cy - s} Z`;
}

module.exports = { SHAPES, roundedPath, sparkle };
