/* Tiny complex-number + 1-qubit gate utilities used by the Bloch widget
   and other interactive components. Pure JS, no dependencies. */

const C = {
  // complex constructor
  c: (re, im = 0) => ({ re, im }),
  add: (a, b) => ({ re: a.re + b.re, im: a.im + b.im }),
  sub: (a, b) => ({ re: a.re - b.re, im: a.im - b.im }),
  mul: (a, b) => ({ re: a.re * b.re - a.im * b.im, im: a.re * b.im + a.im * b.re }),
  scale: (a, s) => ({ re: a.re * s, im: a.im * s }),
  conj: (a) => ({ re: a.re, im: -a.im }),
  abs: (a) => Math.hypot(a.re, a.im),
  abs2: (a) => a.re * a.re + a.im * a.im,
  arg: (a) => Math.atan2(a.im, a.re),
  expi: (theta) => ({ re: Math.cos(theta), im: Math.sin(theta) }),
  fmt: (a, digits = 3) => {
    const r = a.re.toFixed(digits);
    const i = a.im.toFixed(digits);
    if (Math.abs(a.im) < 1e-6) return r;
    if (Math.abs(a.re) < 1e-6) return i + "i";
    const sign = a.im >= 0 ? "+" : "-";
    return `${r}${sign}${Math.abs(a.im).toFixed(digits)}i`;
  },
};

// Single-qubit state |psi> = a|0> + b|1>
const Q = {
  init: () => ({ a: C.c(1, 0), b: C.c(0, 0) }),

  // Apply a 2x2 matrix [[m00, m01], [m10, m11]] (each entry is complex)
  apply2x2: (state, M) => {
    const a = C.add(C.mul(M[0][0], state.a), C.mul(M[0][1], state.b));
    const b = C.add(C.mul(M[1][0], state.a), C.mul(M[1][1], state.b));
    return { a, b };
  },

  // Pauli & friends
  H: (s) => {
    const inv = 1 / Math.sqrt(2);
    return Q.apply2x2(s, [
      [C.c(inv, 0), C.c(inv, 0)],
      [C.c(inv, 0), C.c(-inv, 0)],
    ]);
  },
  X: (s) => Q.apply2x2(s, [[C.c(0), C.c(1)], [C.c(1), C.c(0)]]),
  Y: (s) => Q.apply2x2(s, [[C.c(0), C.c(0, -1)], [C.c(0, 1), C.c(0)]]),
  Z: (s) => Q.apply2x2(s, [[C.c(1), C.c(0)], [C.c(0), C.c(-1)]]),
  S: (s) => Q.apply2x2(s, [[C.c(1), C.c(0)], [C.c(0), C.c(0, 1)]]),
  T: (s) => Q.apply2x2(s, [[C.c(1), C.c(0)], [C.c(0), C.expi(Math.PI / 4)]]),

  RX: (s, theta) => {
    const c = Math.cos(theta / 2), si = Math.sin(theta / 2);
    return Q.apply2x2(s, [
      [C.c(c), C.c(0, -si)],
      [C.c(0, -si), C.c(c)],
    ]);
  },
  RY: (s, theta) => {
    const c = Math.cos(theta / 2), si = Math.sin(theta / 2);
    return Q.apply2x2(s, [
      [C.c(c), C.c(-si)],
      [C.c(si), C.c(c)],
    ]);
  },
  RZ: (s, theta) => {
    return Q.apply2x2(s, [
      [C.expi(-theta / 2), C.c(0)],
      [C.c(0), C.expi(theta / 2)],
    ]);
  },

  // Convert (a, b) to Bloch vector (x, y, z)
  toBloch: (s) => {
    const a = s.a, b = s.b;
    // x = 2 Re(a* b),  y = 2 Im(a* b),  z = |a|^2 - |b|^2
    const conjA_b = C.mul(C.conj(a), b);
    return {
      x: 2 * conjA_b.re,
      y: 2 * conjA_b.im,
      z: C.abs2(a) - C.abs2(b),
    };
  },

  prob0: (s) => C.abs2(s.a),
  prob1: (s) => C.abs2(s.b),

  measure: (s) => (Math.random() < Q.prob0(s) ? 0 : 1),

  fmtState: (s, digits = 3) => {
    return `|psi> = (${C.fmt(s.a, digits)})|0> + (${C.fmt(s.b, digits)})|1>`;
  },
};

// Expose globally
window.C = C;
window.Q = Q;
