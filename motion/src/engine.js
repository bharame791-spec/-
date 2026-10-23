// Deterministic timeline helpers: every frame is a pure function of time t.
(function () {
  const NS = 'http://www.w3.org/2000/svg';

  function el(tag, attrs, parent) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs || {}) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }

  function set(n, attrs) {
    for (const k in attrs) n.setAttribute(k, attrs[k]);
  }

  // CSS-style cubic-bezier — the "graph editor" curves.
  function bezier(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
    const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = (t) => ((ax * t + bx) * t + cx) * t;
    const sy = (t) => ((ay * t + by) * t + cy) * t;
    const dsx = (t) => (3 * ax * t + 2 * bx) * t + cx;
    return (x) => {
      if (x <= 0) return 0;
      if (x >= 1) return 1;
      let t = x;
      for (let i = 0; i < 8; i++) {
        const e = sx(t) - x, d = dsx(t);
        if (Math.abs(e) < 1e-6) return sy(t);
        if (Math.abs(d) < 1e-6) break;
        t -= e / d;
      }
      let lo = 0, hi = 1;
      t = x;
      for (let i = 0; i < 30; i++) {
        const v = sx(t);
        if (Math.abs(v - x) < 1e-6) break;
        if (v < x) lo = t; else hi = t;
        t = (lo + hi) / 2;
      }
      return sy(t);
    };
  }

  const E = {
    lin: (x) => x,
    out: bezier(0.16, 1, 0.3, 1),       // fast start, long luxurious settle
    inOut: bezier(0.65, 0, 0.35, 1),    // camera / travelling moves
    soft: bezier(0.45, 0.05, 0.2, 1),   // gentle in, long out
    in: bezier(0.55, 0, 0.85, 0.3),     // exits
    settle: bezier(0.22, 1.25, 0.36, 1), // tiny overshoot for landing pops
  };

  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, k) => a + (b - a) * k;

  // eased progress of t inside [t0, t1]
  function p(t, t0, t1, ease = E.inOut) {
    return ease(clamp((t - t0) / (t1 - t0)));
  }

  // keyframe track: [[time, value, easeIntoThisKey?], ...]; values may be arrays
  function track(keys) {
    return (t) => {
      if (t <= keys[0][0]) return keys[0][1];
      for (let i = 1; i < keys.length; i++) {
        const [t1, v1, ease] = keys[i];
        if (t <= t1) {
          const [t0, v0] = keys[i - 1];
          const k = (ease || E.inOut)((t - t0) / (t1 - t0));
          return Array.isArray(v0) ? v0.map((a, j) => lerp(a, v1[j], k)) : lerp(v0, v1, k);
        }
      }
      return keys[keys.length - 1][1];
    };
  }

  // trim paths: show the [a, b] fraction of a stroked path
  function trim(path, a, b) {
    let L = path.__len;
    if (L === undefined) L = path.__len = path.getTotalLength();
    a = clamp(a); b = clamp(b);
    // round caps would paint a dot for an empty dash, so hide instead
    path.style.visibility = b - a <= 0.0005 ? 'hidden' : '';
    path.setAttribute('stroke-dasharray', `${Math.max(0, (b - a) * L)} ${L + 1}`);
    path.setAttribute('stroke-dashoffset', -a * L);
  }

  function pointAt(path, f) {
    let L = path.__len;
    if (L === undefined) L = path.__len = path.getTotalLength();
    const d = clamp(f) * L;
    const a = path.getPointAtLength(d);
    const b = path.getPointAtLength(Math.min(L, d + 1));
    const c = path.getPointAtLength(Math.max(0, d - 1));
    return { x: a.x, y: a.y, angle: Math.atan2(b.y - c.y, b.x - c.x) * 180 / Math.PI };
  }

  function mixHex(a, b, k) {
    const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
    const ch = (s) => Math.round(lerp((pa >> s) & 255, (pb >> s) & 255, k));
    return `rgb(${ch(16)},${ch(8)},${ch(0)})`;
  }

  window.M = { el, set, bezier, E, clamp, lerp, p, track, trim, pointAt, mixHex, NS };
})();
