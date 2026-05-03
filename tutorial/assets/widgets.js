/* All non-Bloch interactive widgets for the tutorial.
   Each widget is a self-contained IIFE that bails if its DOM root is
   missing. Pure vanilla JS, no dependencies. */

// ============================================================
// 3.  Single-qubit measurement simulator
// ============================================================
(function () {
  const slider = document.getElementById("theta-slider");
  if (!slider) return;
  const thetaVal   = document.getElementById("theta-value");
  const theoryP0   = document.getElementById("theory-p0");
  const theoryP1   = document.getElementById("theory-p1");
  const numShots   = document.getElementById("num-shots");
  const runBtn     = document.getElementById("run-shots-btn");
  const resetBtn   = document.getElementById("reset-shots-btn");
  const bar0       = document.getElementById("hist-bar-0");
  const bar1       = document.getElementById("hist-bar-1");
  const cnt0       = document.getElementById("hist-count-0");
  const cnt1       = document.getElementById("hist-count-1");

  let counts = { 0: 0, 1: 0 };

  function updateTheory() {
    const theta = parseFloat(slider.value);
    thetaVal.textContent = theta.toFixed(4);
    const p0 = Math.cos(theta / 2) ** 2;
    theoryP0.textContent = (p0 * 100).toFixed(1) + "%";
    theoryP1.textContent = ((1 - p0) * 100).toFixed(1) + "%";
  }

  function refreshBars() {
    const total = counts[0] + counts[1] || 1;
    const f0 = counts[0] / total, f1 = counts[1] / total;
    bar0.style.width = (f0 * 100) + "%";
    bar1.style.width = (f1 * 100) + "%";
    cnt0.textContent = counts[0] + " (" + (f0 * 100).toFixed(1) + "%)";
    cnt1.textContent = counts[1] + " (" + (f1 * 100).toFixed(1) + "%)";
  }

  slider.addEventListener("input", updateTheory);
  runBtn.addEventListener("click", () => {
    const theta = parseFloat(slider.value);
    const N = Math.max(1, Math.min(100000, parseInt(numShots.value) || 1000));
    const p0 = Math.cos(theta / 2) ** 2;
    for (let i = 0; i < N; i++) counts[Math.random() < p0 ? 0 : 1]++;
    refreshBars();
  });
  resetBtn.addEventListener("click", () => {
    counts = { 0: 0, 1: 0 };
    refreshBars();
  });

  updateTheory();
  refreshBars();
})();


// ============================================================
// 5.  Bell-pair correlation simulator
// ============================================================
(function () {
  const runBtn = document.getElementById("bell-run");
  if (!runBtn) return;
  const run100 = document.getElementById("bell-run-100");
  const reset  = document.getElementById("bell-reset");
  const totals = { "00": 0, "01": 0, "10": 0, "11": 0 };

  function step() {
    const r = Math.random();
    return r < 0.5 ? "00" : "11"; // perfect correlation
  }
  function refresh() {
    const total = Object.values(totals).reduce((a, b) => a + b, 0) || 1;
    for (const k of ["00", "01", "10", "11"]) {
      document.getElementById("bell-" + k).textContent = totals[k];
      document.getElementById("bell-" + k + "-pct").textContent =
        (totals[k] / total * 100).toFixed(1) + "%";
    }
  }
  runBtn.addEventListener("click", () => { totals[step()]++; refresh(); });
  run100.addEventListener("click", () => {
    for (let i = 0; i < 100; i++) totals[step()]++;
    refresh();
  });
  reset.addEventListener("click", () => {
    for (const k in totals) totals[k] = 0;
    refresh();
  });
  refresh();
})();


// ============================================================
// 6.  PCA variance-retained slider
// ============================================================
(function () {
  const k = document.getElementById("pca-k");
  if (!k) return;
  const kVal = document.getElementById("pca-k-value");
  const kDisp = document.getElementById("pca-k-display");
  const retained = document.getElementById("pca-variance-retained");
  const lost = document.getElementById("pca-variance-lost");
  const nVqc = document.getElementById("pca-vqc-params");
  const barsEl = document.getElementById("pca-bars");

  // Representative variance ratios for the 29-component PCA on the
  // ULB credit-card dataset (truncated geometric falloff). The actual
  // values vary slightly run-to-run; these are illustrative.
  const variances = [];
  let s = 1.0;
  for (let i = 0; i < 29; i++) {
    variances.push(s * (0.18 - i * 0.0048));
    s *= 0.96;
  }
  // normalise
  const totalV = variances.reduce((a, b) => a + b, 0);
  for (let i = 0; i < variances.length; i++) variances[i] /= totalV;

  // Build bars
  for (let i = 0; i < 29; i++) {
    const b = document.createElement("div");
    b.className = "pca-bar";
    b.style.height = (variances[i] * 600).toFixed(1) + "%";
    b.title = "PC" + (i + 1) + ": " + (variances[i] * 100).toFixed(2) + "% var";
    barsEl.appendChild(b);
  }

  function update() {
    const kk = parseInt(k.value);
    kVal.textContent = kk;
    kDisp.textContent = kk;
    const sum = variances.slice(0, kk).reduce((a, b) => a + b, 0);
    retained.textContent = (sum * 100).toFixed(1) + "%";
    lost.textContent = ((1 - sum) * 100).toFixed(1) + "%";
    nVqc.textContent = ((2 * 3 + 1) * kk) + " (with reps=3)";
    barsEl.querySelectorAll(".pca-bar").forEach((el, i) => {
      if (i < kk) el.classList.remove("dim");
      else el.classList.add("dim");
    });
  }
  k.addEventListener("input", update);
  update();
})();


// ============================================================
// 7.  ZZFeatureMap interactive circuit diagram (SVG)
// ============================================================
(function () {
  const svg = document.getElementById("zzfm-svg");
  if (!svg) return;
  const nIn = document.getElementById("zzfm-n");
  const repsIn = document.getElementById("zzfm-reps");
  const entIn = document.getElementById("zzfm-ent");
  const nVal = document.getElementById("zzfm-n-val");
  const repsVal = document.getElementById("zzfm-reps-val");
  const gateCount = document.getElementById("zzfm-gate-count");
  const depthEl = document.getElementById("zzfm-depth");

  const SVG_NS = "http://www.w3.org/2000/svg";

  function entanglerPairs(n, mode) {
    const pairs = [];
    if (mode === "linear") {
      for (let i = 0; i < n - 1; i++) pairs.push([i, i + 1]);
    } else if (mode === "circular") {
      for (let i = 0; i < n; i++) pairs.push([i, (i + 1) % n]);
    } else if (mode === "full") {
      for (let i = 0; i < n; i++)
        for (let j = i + 1; j < n; j++) pairs.push([i, j]);
    }
    return pairs;
  }

  function el(tag, attrs, text) {
    const e = document.createElementNS(SVG_NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }

  function box(x, y, w, h, fill, label, sub) {
    const g = document.createElementNS(SVG_NS, "g");
    g.appendChild(el("rect", { x, y, width: w, height: h, rx: 4, ry: 4, fill, stroke: "#6ad1ff", "stroke-width": 1, opacity: 0.85 }));
    g.appendChild(el("text", { x: x + w / 2, y: y + h / 2 + 4, "text-anchor": "middle", fill: "#0a0e1a", "font-size": 11, "font-family": "Georgia, serif", "font-weight": 600 }, label));
    if (sub) g.appendChild(el("text", { x: x + w / 2, y: y + h - 3, "text-anchor": "middle", fill: "#0a0e1a", "font-size": 8, "font-family": "monospace" }, sub));
    return g;
  }

  function rzzGate(x, y1, y2, label) {
    const g = document.createElementNS(SVG_NS, "g");
    g.appendChild(el("line", { x1: x, y1: y1, x2: x, y2: y2, stroke: "#b48cff", "stroke-width": 2 }));
    g.appendChild(el("circle", { cx: x, cy: y1, r: 4, fill: "#b48cff" }));
    g.appendChild(el("circle", { cx: x, cy: y2, r: 4, fill: "#b48cff" }));
    g.appendChild(el("rect", { x: x - 22, y: (y1 + y2) / 2 - 8, width: 44, height: 16, fill: "#1a2238", stroke: "#b48cff", rx: 3 }));
    g.appendChild(el("text", { x, y: (y1 + y2) / 2 + 4, "text-anchor": "middle", fill: "#b48cff", "font-size": 9 }, label));
    return g;
  }

  function render() {
    const n = parseInt(nIn.value);
    const reps = parseInt(repsIn.value);
    const ent = entIn.value;
    nVal.textContent = n;
    repsVal.textContent = reps;

    while (svg.firstChild) svg.removeChild(svg.firstChild);
    const pairs = entanglerPairs(n, ent);

    const rowH = 50;
    const leftPad = 70;
    const colW = 60;
    // per rep: 1 H column + 1 RZ column + pairs.length entangler columns
    const colsPerRep = 2 + pairs.length;
    const totalCols = colsPerRep * reps;
    const width = leftPad + totalCols * colW + 40;
    const height = n * rowH + 30;

    svg.setAttribute("width", width);
    svg.setAttribute("height", height);
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    // Wire lines
    for (let q = 0; q < n; q++) {
      const y = 25 + q * rowH;
      svg.appendChild(el("text", { x: 4, y: y + 4, fill: "#aab5c4", "font-size": 11, "font-family": "monospace" }, `q${q}`));
      svg.appendChild(el("line", { x1: 30, y1: y, x2: width - 10, y2: y, stroke: "#3a455e", "stroke-width": 1 }));
    }

    // Build columns
    let col = 0;
    let gateTotal = 0;
    for (let r = 0; r < reps; r++) {
      // H layer
      for (let q = 0; q < n; q++) {
        const x = leftPad + col * colW;
        const y = 25 + q * rowH;
        svg.appendChild(box(x - 14, y - 14, 28, 28, "#6ad1ff", "H"));
        gateTotal++;
      }
      col++;

      // RZ(2x_i) layer
      for (let q = 0; q < n; q++) {
        const x = leftPad + col * colW;
        const y = 25 + q * rowH;
        svg.appendChild(box(x - 22, y - 14, 44, 28, "#ffb86b", "RZ", `2x${q}`));
        gateTotal++;
      }
      col++;

      // Entangler pairs (RZZ)
      for (const [i, j] of pairs) {
        const x = leftPad + col * colW;
        const y1 = 25 + i * rowH;
        const y2 = 25 + j * rowH;
        svg.appendChild(rzzGate(x, y1, y2, `RZZ(${i},${j})`));
        gateTotal++;
        col++;
      }
    }

    gateCount.textContent = gateTotal;
    depthEl.textContent = totalCols + " layers";
  }

  [nIn, repsIn, entIn].forEach((c) => c.addEventListener("input", render));
  render();
})();


// ============================================================
// 8.  EfficientSU2 parameter counter
// ============================================================
(function () {
  const nIn = document.getElementById("su2-n");
  if (!nIn) return;
  const repsIn = document.getElementById("su2-reps");
  const nVal = document.getElementById("su2-n-val");
  const repsVal = document.getElementById("su2-reps-val");
  const params = document.getElementById("su2-params");
  const oneQ = document.getElementById("su2-1q");
  const twoQ = document.getElementById("su2-2q");
  const depth = document.getElementById("su2-depth");

  function update() {
    const n = parseInt(nIn.value);
    const r = parseInt(repsIn.value);
    nVal.textContent = n;
    repsVal.textContent = r;
    const nParams = (2 * r + 1) * n;       // RY+RZ per rep + final RY+RZ -> wait, formula in repo is (2r+1)*n which assumes 2 layers per rep + 1 final RY/RZ pair counts as 1 layer.
    const nOneQ   = nParams;                // each parameter is one rotation gate
    const nTwoQ   = (n - 1) * r;            // linear entanglement: n-1 CX per rep
    const dep     = 2 * r + 1 + r;          // rough: rotations + entanglers
    params.textContent = nParams;
    oneQ.textContent = nOneQ;
    twoQ.textContent = nTwoQ;
    depth.textContent = dep;
  }
  [nIn, repsIn].forEach((c) => c.addEventListener("input", update));
  update();
})();


// ============================================================
// 9.  SPSA optimizer toy
// ============================================================
(function () {
  const canvas = document.getElementById("spsa-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const optSel = document.getElementById("spsa-opt");
  const noiseIn = document.getElementById("spsa-noise");
  const noiseVal = document.getElementById("spsa-noise-val");
  const stepBtn = document.getElementById("spsa-step");
  const run10Btn = document.getElementById("spsa-run10");
  const resetBtn = document.getElementById("spsa-reset");
  const iterEl = document.getElementById("spsa-iter");
  const thetaEl = document.getElementById("spsa-theta");
  const lossEl = document.getElementById("spsa-loss");

  const range = [-Math.PI, Math.PI];
  function loss_clean(t) { return (Math.cos(3 * t) + 0.5) ** 2 + 0.05 * t * t; }
  function loss_noisy(t) {
    const sigma = parseFloat(noiseIn.value);
    return loss_clean(t) + (Math.random() - 0.5) * 2 * sigma;
  }
  // Analytic gradient (clean)
  function grad_clean(t) { return 2 * (Math.cos(3 * t) + 0.5) * (-3 * Math.sin(3 * t)) + 0.1 * t; }

  let theta = -2.5, iter = 0;
  let pathPoints = [];
  // For COBYLA-style we keep a tiny simplex (a, b)
  let cobylaSimplex = null;

  function reset() {
    theta = (Math.random() - 0.5) * 5;
    iter = 0;
    pathPoints = [{ t: theta, l: loss_clean(theta) }];
    cobylaSimplex = null;
    draw();
    refresh();
  }
  function refresh() {
    iterEl.textContent = iter;
    thetaEl.textContent = theta.toFixed(3);
    lossEl.textContent = loss_clean(theta).toFixed(4);
  }

  function step() {
    const opt = optSel.value;
    if (opt === "spsa") {
      const c = 0.2 / Math.sqrt(iter + 1);
      const a = 0.4 / Math.pow(iter + 1, 0.602);
      const delta = Math.random() < 0.5 ? -1 : 1;
      const fp = loss_noisy(theta + c * delta);
      const fm = loss_noisy(theta - c * delta);
      const g = (fp - fm) / (2 * c * delta);
      theta -= a * g;
    } else if (opt === "cobyla") {
      // toy: probe theta +/- 0.3, build a quadratic, jump to its min
      if (!cobylaSimplex) cobylaSimplex = { a: theta - 0.3, b: theta + 0.3 };
      const fa = loss_noisy(cobylaSimplex.a);
      const fb = loss_noisy(cobylaSimplex.b);
      const fc = loss_noisy(theta);
      // fit a parabola through 3 points and step to min
      const xa = cobylaSimplex.a, xb = cobylaSimplex.b, xc = theta;
      const denom = (xa - xb) * (xa - xc) * (xb - xc);
      let A = (xc * (fb - fa) + xb * (fa - fc) + xa * (fc - fb)) / denom;
      let B = (xc * xc * (fa - fb) + xb * xb * (fc - fa) + xa * xa * (fb - fc)) / denom;
      if (Math.abs(A) > 1e-6) {
        const xmin = -B / (2 * A);
        theta = Math.max(range[0], Math.min(range[1], xmin));
      } else {
        theta -= 0.05 * grad_clean(theta);
      }
      cobylaSimplex = { a: theta - 0.2, b: theta + 0.2 };
    } else {
      // vanilla GD
      theta -= 0.05 * grad_clean(theta);
    }
    theta = Math.max(range[0], Math.min(range[1], theta));
    iter++;
    pathPoints.push({ t: theta, l: loss_clean(theta) });
    draw();
    refresh();
  }

  function tx(t) { return ((t - range[0]) / (range[1] - range[0])) * (W - 40) + 20; }
  function ty(l, lmin, lmax) { return H - 20 - ((l - lmin) / (lmax - lmin)) * (H - 40); }

  function draw() {
    ctx.fillStyle = "#0f1422";
    ctx.fillRect(0, 0, W, H);

    // sample loss curve
    let lmin = Infinity, lmax = -Infinity;
    const samples = [];
    for (let i = 0; i <= 200; i++) {
      const t = range[0] + (i / 200) * (range[1] - range[0]);
      const l = loss_clean(t);
      samples.push({ t, l });
      if (l < lmin) lmin = l;
      if (l > lmax) lmax = l;
    }

    // axes
    ctx.strokeStyle = "#243049";
    ctx.beginPath();
    ctx.moveTo(20, H - 20); ctx.lineTo(W - 20, H - 20);
    ctx.moveTo(20, 10);     ctx.lineTo(20, H - 20);
    ctx.stroke();
    ctx.fillStyle = "#6f7d92";
    ctx.font = "11px monospace";
    ctx.fillText("theta", W - 50, H - 5);
    ctx.fillText("L(theta)", 22, 14);

    // loss curve
    ctx.strokeStyle = "#6ad1ff";
    ctx.lineWidth = 2;
    ctx.beginPath();
    samples.forEach((p, i) => {
      const x = tx(p.t), y = ty(p.l, lmin, lmax);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // path
    if (pathPoints.length > 1) {
      ctx.strokeStyle = "#ffb86b";
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      pathPoints.forEach((p, i) => {
        const x = tx(p.t), y = ty(p.l, lmin, lmax);
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();

      pathPoints.forEach((p) => {
        ctx.fillStyle = "#ffb86b";
        ctx.beginPath();
        ctx.arc(tx(p.t), ty(p.l, lmin, lmax), 2.5, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    // current point
    ctx.fillStyle = "#b48cff";
    ctx.shadowColor = "#b48cff";
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(tx(theta), ty(loss_clean(theta), lmin, lmax), 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  noiseIn.addEventListener("input", () => { noiseVal.textContent = noiseIn.value; });
  stepBtn.addEventListener("click", step);
  run10Btn.addEventListener("click", () => { for (let i = 0; i < 10; i++) step(); });
  resetBtn.addEventListener("click", reset);
  optSel.addEventListener("change", reset);

  reset();
})();


// ============================================================
// 10. Quantum kernel sandbox
// ============================================================
(function () {
  const canvas = document.getElementById("kernel-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const kindSel = document.getElementById("kernel-type");
  const classSel = document.getElementById("kernel-class");
  const clearBtn = document.getElementById("kernel-clear");
  const spiralBtn = document.getElementById("kernel-load-spirals");
  const xorBtn = document.getElementById("kernel-load-xor");
  const nEl = document.getElementById("kernel-n");
  const accEl = document.getElementById("kernel-acc");
  const costEl = document.getElementById("kernel-cost");

  let points = []; // {x, y, c}

  function px2data(px, py) {
    return { x: (px / W) * 2 - 1, y: 1 - (py / H) * 2 };
  }
  function data2px(x, y) {
    return { px: ((x + 1) / 2) * W, py: ((1 - y) / 2) * H };
  }

  function rbf(a, b, gamma = 4) {
    const d2 = (a.x - b.x) ** 2 + (a.y - b.y) ** 2;
    return Math.exp(-gamma * d2);
  }
  function linear(a, b) { return a.x * b.x + a.y * b.y; }

  // Simulated 2-qubit ZZFeatureMap fidelity kernel:
  //   |<phi(a)|phi(b)>|^2  with  phi(x) = (Hadamard then RZ(2x_i)
  //   then RZZ on pair (0,1)) repeated twice.
  // Computed analytically below for n=2 reps=2.
  function quantumZZ(a, b) {
    // phase difference per feature
    const da = 2 * Math.PI * a.x; // simulate scaled to ~[-2pi, 2pi]
    const db = 2 * Math.PI * b.x;
    const ea = 2 * Math.PI * a.y;
    const eb = 2 * Math.PI * b.y;
    const piMa = Math.PI - Math.PI * a.x;
    const piMb = Math.PI - Math.PI * b.x;
    const piMa2 = Math.PI - Math.PI * a.y;
    const piMb2 = Math.PI - Math.PI * b.y;
    // approximation: kernel ~ cos((da-db)/2)^2 * cos((ea-eb)/2)^2 * cos((piMa*piMa2 - piMb*piMb2)/2)^2  (reps=2)
    const k1 = Math.cos((da - db) / 2) ** 2;
    const k2 = Math.cos((ea - eb) / 2) ** 2;
    const k3 = Math.cos((piMa * piMa2 - piMb * piMb2) / 2) ** 2;
    return Math.max(0, Math.min(1, k1 * k2 * k3));
  }

  function getKernel() {
    const k = kindSel.value;
    if (k === "linear") return linear;
    if (k === "rbf") return rbf;
    return quantumZZ;
  }

  // Naive kernel-perceptron (Parzen-window classifier): score(x) =
  // sum_i (2*c_i - 1) * K(x_i, x).  Threshold at 0 -> class 1 vs 0.
  function score(p, kernel) {
    let s = 0;
    for (const q of points) s += (q.c === 1 ? 1 : -1) * kernel(p, q);
    return s;
  }

  function classify(p, kernel) { return score(p, kernel) > 0 ? 1 : 0; }

  function draw() {
    ctx.fillStyle = "#0f1422";
    ctx.fillRect(0, 0, W, H);

    if (points.length >= 2) {
      const kernel = getKernel();
      // Color the background according to score
      const stride = 6;
      const img = ctx.createImageData(W, H);
      // We'll do a coarse grid then blit
      for (let py = 0; py < H; py += stride) {
        for (let px = 0; px < W; px += stride) {
          const p = px2data(px, py);
          const s = score(p, kernel);
          const intensity = Math.tanh(s * 1.5); // -1 .. 1
          const r = intensity > 0 ? 200 + Math.round(40 * intensity) : 30;
          const b = intensity < 0 ? 200 - Math.round(40 * intensity) : 30;
          const g = 30;
          const a = 110;
          for (let dy = 0; dy < stride; dy++) {
            for (let dx = 0; dx < stride; dx++) {
              const idx = ((py + dy) * W + (px + dx)) * 4;
              if (idx + 3 < img.data.length) {
                img.data[idx]     = r;
                img.data[idx + 1] = g;
                img.data[idx + 2] = b;
                img.data[idx + 3] = a;
              }
            }
          }
        }
      }
      ctx.putImageData(img, 0, 0);
      // Draw decision boundary (zero contour) by sampling
      ctx.strokeStyle = "rgba(255,255,255,0.5)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let py = 0; py < H; py += 4) {
        let prevSign = null;
        for (let px = 0; px < W; px += 4) {
          const p = px2data(px, py);
          const s = score(p, kernel);
          const sgn = Math.sign(s);
          if (prevSign != null && sgn !== prevSign && sgn !== 0) {
            ctx.moveTo(px - 2, py);
            ctx.lineTo(px, py);
          }
          prevSign = sgn;
        }
      }
      ctx.stroke();
    } else {
      ctx.fillStyle = "#3a455e";
      ctx.font = "14px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Click to add points (2+ needed for a decision boundary)", W / 2, H / 2);
    }

    // Draw points
    for (const p of points) {
      const { px, py } = data2px(p.x, p.y);
      ctx.fillStyle = p.c === 1 ? "#ff6b8a" : "#3aaaff";
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(px, py, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }
  }

  function refreshStats() {
    nEl.textContent = points.length;
    if (points.length < 2) {
      accEl.textContent = "--";
      costEl.textContent = "--";
      return;
    }
    const kernel = getKernel();
    let correct = 0;
    let cost = 0;
    for (const p of points) {
      const s = score(p, kernel);
      const pred = s > 0 ? 1 : 0;
      if (pred === p.c) correct++;
      // hinge-like cost
      const margin = (p.c === 1 ? 1 : -1) * s;
      cost += Math.max(0, 1 - margin);
    }
    accEl.textContent = ((correct / points.length) * 100).toFixed(0) + "%";
    costEl.textContent = (cost / points.length).toFixed(2);
  }

  canvas.addEventListener("click", (e) => {
    const rect = canvas.getBoundingClientRect();
    const px = (e.clientX - rect.left) * (W / rect.width);
    const py = (e.clientY - rect.top) * (H / rect.height);
    const { x, y } = px2data(px, py);
    const c = e.shiftKey ? 1 : parseInt(classSel.value);
    points.push({ x, y, c });
    draw(); refreshStats();
  });

  clearBtn.addEventListener("click", () => { points = []; draw(); refreshStats(); });

  spiralBtn.addEventListener("click", () => {
    points = [];
    for (let i = 0; i < 30; i++) {
      const t = (i / 30) * 4 * Math.PI;
      const r = 0.05 + (i / 30) * 0.7;
      points.push({ x: r * Math.cos(t),     y: r * Math.sin(t),     c: 0 });
      points.push({ x: r * Math.cos(t + Math.PI), y: r * Math.sin(t + Math.PI), c: 1 });
    }
    draw(); refreshStats();
  });
  xorBtn.addEventListener("click", () => {
    points = [];
    for (let i = 0; i < 20; i++) {
      points.push({ x:  0.4 + Math.random() * 0.3, y:  0.4 + Math.random() * 0.3, c: 0 });
      points.push({ x: -0.4 - Math.random() * 0.3, y: -0.4 - Math.random() * 0.3, c: 0 });
      points.push({ x:  0.4 + Math.random() * 0.3, y: -0.4 - Math.random() * 0.3, c: 1 });
      points.push({ x: -0.4 - Math.random() * 0.3, y:  0.4 + Math.random() * 0.3, c: 1 });
    }
    draw(); refreshStats();
  });

  kindSel.addEventListener("change", () => { draw(); refreshStats(); });

  draw(); refreshStats();
})();
