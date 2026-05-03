/* Bloch sphere visualisation + gate buttons.
   The sphere is rendered with simple isometric projection on a canvas.
   The state vector is a 3D arrow that smoothly tweens between gate
   applications. */

(function () {
  const canvas = document.getElementById("bloch-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const R = 130; // sphere radius

  // 3D rotation: rotate around the vertical (Y) axis a bit so we see depth
  let yaw = 0.6, pitch = -0.35;

  let state = Q.init();
  let animTarget = Q.toBloch(state); // current bloch vector being drawn
  let animCurrent = { ...animTarget };
  let history = ["|0>"];

  // Allow click+drag to rotate the sphere
  let dragging = false, lastX = 0, lastY = 0;
  canvas.addEventListener("mousedown", (e) => {
    dragging = true; lastX = e.offsetX; lastY = e.offsetY;
  });
  window.addEventListener("mouseup", () => (dragging = false));
  canvas.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    yaw   += (e.offsetX - lastX) * 0.01;
    pitch += (e.offsetY - lastY) * 0.01;
    pitch = Math.max(-1.4, Math.min(1.4, pitch));
    lastX = e.offsetX; lastY = e.offsetY;
    draw();
  });

  function project3D(p) {
    // Yaw rotates around Y, pitch rotates around X, then orthographic projection
    const cy_ = Math.cos(yaw), sy_ = Math.sin(yaw);
    const cp = Math.cos(pitch), sp = Math.sin(pitch);
    let x = cy_ * p.x + sy_ * p.z;
    let z = -sy_ * p.x + cy_ * p.z;
    let y = cp * p.y - sp * z;
    z = sp * p.y + cp * z;
    return { x: cx + x * R, y: cy - y * R, depth: z };
  }

  function draw() {
    ctx.fillStyle = "#0a0e1a";
    ctx.fillRect(0, 0, W, H);

    // Draw sphere outline
    ctx.strokeStyle = "rgba(180, 200, 255, 0.18)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.stroke();

    // Equator (XY plane = great circle, projected as ellipse)
    drawGreatCircle({ x: 1, y: 0, z: 0 }, { x: 0, y: 1, z: 0 }, "rgba(180,200,255,0.18)");
    // XZ plane (vertical, the meridian containing |+>, |->)
    drawGreatCircle({ x: 1, y: 0, z: 0 }, { x: 0, y: 0, z: 1 }, "rgba(180,200,255,0.10)");
    // YZ plane
    drawGreatCircle({ x: 0, y: 1, z: 0 }, { x: 0, y: 0, z: 1 }, "rgba(180,200,255,0.10)");

    // Axes
    drawAxis({ x: 1, y: 0, z: 0 }, "X", "#ff8080");
    drawAxis({ x: 0, y: 1, z: 0 }, "Y", "#80ff80");
    drawAxis({ x: 0, y: 0, z: 1 }, "Z", "#80a8ff");

    // Pole labels
    drawLabel({ x: 0, y: 0, z: 1.18 }, "|0>", "#80a8ff");
    drawLabel({ x: 0, y: 0, z: -1.2 }, "|1>", "#80a8ff");
    drawLabel({ x: 1.18, y: 0, z: 0 }, "|+>", "#ffb86b");
    drawLabel({ x: -1.18, y: 0, z: 0 }, "|->", "#ffb86b");
    drawLabel({ x: 0, y: 1.18, z: 0 }, "|+i>", "#80ff80");
    drawLabel({ x: 0, y: -1.2, z: 0 }, "|-i>", "#80ff80");

    // State arrow
    const v = animCurrent;
    const tip = project3D(v);
    const origin = project3D({ x: 0, y: 0, z: 0 });

    ctx.strokeStyle = "#6ad1ff";
    ctx.lineWidth = 3;
    ctx.shadowColor = "rgba(106, 209, 255, 0.7)";
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.moveTo(origin.x, origin.y);
    ctx.lineTo(tip.x, tip.y);
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Tip ball
    ctx.fillStyle = "#b48cff";
    ctx.beginPath();
    ctx.arc(tip.x, tip.y, 6, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawGreatCircle(u, w, color) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= 64; i++) {
      const t = (i / 64) * 2 * Math.PI;
      const p = {
        x: u.x * Math.cos(t) + w.x * Math.sin(t),
        y: u.y * Math.cos(t) + w.y * Math.sin(t),
        z: u.z * Math.cos(t) + w.z * Math.sin(t),
      };
      const q = project3D(p);
      if (i === 0) ctx.moveTo(q.x, q.y);
      else ctx.lineTo(q.x, q.y);
    }
    ctx.stroke();
  }

  function drawAxis(dir, label, color) {
    const a = project3D({ x: -dir.x, y: -dir.y, z: -dir.z });
    const b = project3D(dir);
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.2;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  function drawLabel(p, text, color) {
    const q = project3D(p);
    ctx.fillStyle = color;
    ctx.font = "12px Georgia, serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, q.x, q.y);
  }

  function animate() {
    const dx = animTarget.x - animCurrent.x;
    const dy = animTarget.y - animCurrent.y;
    const dz = animTarget.z - animCurrent.z;
    const dist = Math.hypot(dx, dy, dz);
    if (dist > 0.001) {
      animCurrent.x += dx * 0.18;
      animCurrent.y += dy * 0.18;
      animCurrent.z += dz * 0.18;
      draw();
      requestAnimationFrame(animate);
    } else {
      animCurrent = { ...animTarget };
      draw();
    }
  }

  function update() {
    animTarget = Q.toBloch(state);
    animate();
    document.getElementById("bloch-state-vector").textContent = Q.fmtState(state);
    const p0 = Q.prob0(state), p1 = Q.prob1(state);
    document.getElementById("p0-fill").style.width = (p0 * 100) + "%";
    document.getElementById("p1-fill").style.width = (p1 * 100) + "%";
    document.getElementById("p0-text").textContent = (p0 * 100).toFixed(1) + "%";
    document.getElementById("p1-text").textContent = (p1 * 100).toFixed(1) + "%";
    const histEl = document.getElementById("bloch-history");
    histEl.textContent = history.join(" -> ");
    histEl.scrollTop = histEl.scrollHeight;
  }

  function applyGate(name) {
    let label = name;
    switch (name) {
      case "H":  state = Q.H(state); break;
      case "X":  state = Q.X(state); break;
      case "Y":  state = Q.Y(state); break;
      case "Z":  state = Q.Z(state); break;
      case "S":  state = Q.S(state); break;
      case "T":  state = Q.T(state); break;
      case "RX": state = Q.RX(state, Math.PI / 4); label = "RX(pi/4)"; break;
      case "RY": state = Q.RY(state, Math.PI / 4); label = "RY(pi/4)"; break;
      case "RZ": state = Q.RZ(state, Math.PI / 4); label = "RZ(pi/4)"; break;
      case "MEASURE":
        const r = Q.measure(state);
        state = r === 0 ? { a: C.c(1), b: C.c(0) } : { a: C.c(0), b: C.c(1) };
        label = "M->" + r;
        break;
      case "RESET":
        state = Q.init();
        history = [];
        label = "reset";
        break;
    }
    history.push(label);
    if (history.length > 12) history = history.slice(history.length - 12);
    update();
  }

  document.querySelectorAll(".gate-buttons button[data-gate]").forEach((btn) => {
    btn.addEventListener("click", () => applyGate(btn.dataset.gate));
  });

  update();
})();
