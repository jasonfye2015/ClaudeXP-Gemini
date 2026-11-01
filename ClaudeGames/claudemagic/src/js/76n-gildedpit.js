"use strict";
// The Gilded Pit, the window's side (the twenty-fourth big update): the room under the Joker in 3D, with its own
// small WebGL - a box of a room papered in green, a bare bulb that flickers on its cord, the Old Lucky against the far
// wall (its reels on a screen that spins, its lever that pulls down), the house's deposit box on the left wall with a
// chalk board of what is owed, a black telephone on the right wall that shakes when it rings, the door behind, the
// trapdoor under the stool. Drag to look about; click the lever (or the screen) to spin, the box to pay, the telephone
// to answer, the door to step out. A drop: the trapdoor swings and the room falls away. Rules: 64x-gildedpit.js.
CM.CG_TABLES.push(["pit", "The Gilded Pit"]);
CM.PIT_SYM_ART = { lemon: "#F0D030", cherry: "#D02030", clover: "#30A040", bell: "#E0A820", diamond: "#60D0F0", chest: "#8A5A28", seven: "#E02020", eye: "#8030C0" };
const PIT_VS = "attribute vec3 pos; attribute vec2 uv; attribute float shade; uniform mat4 mvp; varying vec2 vUv; varying float vShade; varying vec3 vPos; void main() { gl_Position = mvp * vec4(pos, 1.0); vUv = uv; vShade = shade; vPos = pos; }";
const PIT_FS = "precision mediump float; uniform sampler2D tex; uniform vec3 bulb; uniform float glow; varying vec2 vUv; varying float vShade; varying vec3 vPos; void main() { vec4 c = texture2D(tex, vUv); if (c.a < 0.1) discard; if (vShade > 1.5) { gl_FragColor = vec4(c.rgb * (vShade - 1.0), c.a); return; } float d = distance(vPos, bulb); float l = glow * clamp(1.7 - d / 1.9, 0.10, 1.25); gl_FragColor = vec4(c.rgb * vShade * l * vec3(1.0, 0.93, 0.8), c.a); }";
{ const floor0 = CM.UI.prototype.renderFloor;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "pit") return this.cgPit(box); return floor0.call(this, box); },
    cgPit(box) {
      const g = this.game, PT = CM.PT, P = g.pitStore(), R = g.pitRun() || (this.pitHold ? this.pitView : null), bet = this.cgBet === undefined ? 10 : this.cgBet;
      if (!R) {
        const last = P.last, book = PT.START.concat(PT.UNLOCK).map((c) => `<span class="${P.unlocked.includes(c) ? "" : "locked"}" title="${this.esc(PT.CHARMS[c][1])}">${P.unlocked.includes(c) ? PT.CHARMS[c][0] : "?"}</span>`).join("");
        box.innerHTML = `<div class="cgtable pitlobby"><h3>The Gilded Pit</h3><p class="lore">A narrow stair behind the bar, and at the bottom a door with a peephole. "One goes down," says the dealer. "The house lends the room, and the Old Lucky. The house wants paying. If it isn't..." She taps the floor with her heel.</p>
          <div class="list-title">Who goes down? (the stake goes with them, as coins)</div><div class="pitwho">${g.party.map((h, i) => `<button data-pith="${i}" class="${this.pitHero === i ? "primary" : ""}" ${h.hp <= 0 ? "disabled" : ""}>${this.esc(h.name)} the ${h.cls} <small>${h.hp}/${h.max}</small></button>`).join("")}</div>
          ${this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || (last ? (last.how === "dropped" ? `${last.hero} came up through the trapdoor with a tenth of their health.` : `${last.hero} stepped out with ${last.pay} gold.`) : "")}</div>
          <div class="row"><button class="primary" data-pitgo ${this.pitHero === undefined ? "disabled" : ""}>Go down</button><button data-leave>Leave</button></div>
          <div class="list-title">The telephone's charms (unlocked ${P.unlocked.length} of ${PT.START.length + PT.UNLOCK.length} - more as deeper deadlines are reached)</div><div class="pitbook">${book}</div>
          <div class="small">Five deadlines, each a debt to pay into the house's box within seven spins of the Old Lucky. Pay it and step out with what is left, or stay for the next. Miss one and the trapdoor drops the hero back to the party with a tenth of their health. Cards at the third and fifth deadlines, and for a full grid. Played ${P.plays}; deepest deadline ${P.best}.</div>${this.cgStats("pit")}</div>`;
        this.cgWireBet(box); box.querySelector("[data-leave]").addEventListener("click", () => this.closeDialogs());
        box.querySelectorAll("[data-pith]").forEach((b) => b.addEventListener("click", () => { this.pitHero = Number(b.dataset.pith); this.cgSfx("card", 0.3); this.renderCasino(); }));
        box.querySelector("[data-pitgo]").addEventListener("click", () => { const r = g.pitStart(this.pitHero, bet); if (r.error) { this.cgNote = r.error; this.renderCasino(); return; } this.cgNote = ""; this.pitMsg = `${g.party[this.pitHero].name} goes down. The door locks.`; this.cgSfx("door", 0.6); this.cgSfx("chain", 0.4); this.pitGrid = null; this.renderCasino(); });
        return;
      }
      const h = g.party[R.hero];
      box.innerHTML = `<div class="cgtable pitroom"><div class="pitstage"><div class="pitcv"></div>
        <div class="pithud top"><b>${this.esc(h ? h.name : "")}</b> in the Pit - deadline ${R.deadline} of ${PT.deadlines}<span class="pitmsg">${this.esc(this.pitMsg || "")}</span></div>
        <div class="pithud charms">${R.charms.map((c) => `<span title="${this.esc(PT.CHARMS[c][1])}">${PT.CHARMS[c][0]}</span>`).join("") || "<small>No charms yet</small>"}</div>
        ${this.pitShop && R.stage === "paid" ? `<div class="pitshop"><h4>The telephone</h4><p>A voice like a coin dropped down a well: "${R.offers.length ? "I have something for you. For tickets." : "Nothing more, today."}" - you have <b>${R.tickets}</b> ticket${R.tickets === 1 ? "" : "s"}.</p>${R.offers.map((c) => `<div class="offer"><b>${PT.CHARMS[c][0]}</b><small>${this.esc(PT.CHARMS[c][1])}</small><button data-pitbuy="${c}" ${R.tickets >= PT.CHARMS[c][2] ? "" : "disabled"}>${PT.CHARMS[c][2]} ticket${PT.CHARMS[c][2] > 1 ? "s" : ""}</button></div>`).join("")}<button data-pitshopclose>Hang up</button></div>` : ""}
        <div class="pithud bar"><button class="primary" data-pit="spin" ${R.stage === "spin" && R.spinsLeft > 0 ? "" : "disabled"}>Pull the lever (${R.cost()} coins)</button><button data-pit="pay" ${R.stage === "spin" && R.coins >= R.debt() ? "" : "disabled"}>Pay the debt (${R.debt()})</button>${R.stage === "paid" ? `<button data-pit="phone">Answer the telephone</button><button data-pit="next">Stay for deadline ${R.deadline + 1}</button><button data-pit="leave">Step out with ${R.coins} gold</button>` : ""}</div></div>
        <div class="small">Drag to look about the room; click the lever or the Old Lucky to spin, the box on the left wall to pay, the telephone to answer, the door to step out.</div></div>`;
      const q = (s) => box.querySelector(s);
      box.querySelectorAll("[data-pit]").forEach((b) => b.addEventListener("click", () => this.pitAct(b.dataset.pit)));
      box.querySelectorAll("[data-pitbuy]").forEach((b) => b.addEventListener("click", () => { if (g.pitBuy(b.dataset.pitbuy)) { this.cgSfx("coin", 0.5); this.cgSfx("spell", 0.4); this.pitMsg = `${PT.CHARMS[b.dataset.pitbuy][0]}: ${PT.CHARMS[b.dataset.pitbuy][1].toLowerCase()}.`; } this.renderCasino(); }));
      if (q("[data-pitshopclose]")) q("[data-pitshopclose]").addEventListener("click", () => { this.pitShop = false; this.cgSfx("cardplace", 0.4); this.renderCasino(); });
      // one canvas and one GL for the room, kept between redraws (a browser keeps only so many)
      if (!this.pitCanvasEl) { const c = document.createElement("canvas"); c.className = "pitcanvas"; c.width = 960; c.height = 540; this.pitCanvasEl = c; this.pitInit(c);
        c.addEventListener("mousedown", (e) => { this.pitDrag = [e.clientX, e.clientY, this.pitYaw, this.pitPitch, false]; });
        c.addEventListener("mousemove", (e) => { const d = this.pitDrag; if (!d) return; const dx = e.clientX - d[0], dy = e.clientY - d[1]; if (Math.abs(dx) + Math.abs(dy) > 4) d[4] = true; this.pitYaw = Math.max(-75, Math.min(75, d[2] - dx * 0.25)); this.pitPitch = Math.max(-35, Math.min(30, d[3] - dy * 0.25)); });
        c.addEventListener("mouseup", (e) => { const d = this.pitDrag; this.pitDrag = null; if (d && !d[4]) this.pitClick(e); });
        c.addEventListener("mouseleave", () => { this.pitDrag = null; }); }
      q(".pitcv").appendChild(this.pitCanvasEl); this.pitCanvas = this.pitCanvasEl;
      if (!this.pitLoop) { const loop = (now) => { if (!this.pitCanvas || !this.pitCanvas.isConnected || this.cgView !== "pit") { this.pitLoop = null; return; } this.pitFrame(now); this.pitLoop = requestAnimationFrame(loop); }; this.pitLoop = requestAnimationFrame(loop); }
    },
    pitAct(what) {
      const g = this.game, PT = CM.PT, R = g.pitRun(); if (!R || this.pitSpinning || this.pitFalling || this.pitHold) return;
      if (what === "spin") { this.pitView = R; const out = g.pitSpin(); if (out.dropped) this.pitHold = true; if (out.error) { this.pitMsg = out.error; this.cgSfx("miss", 0.3); this.renderCasino(); return; } this.pitLever = performance.now(); this.pitSpinning = { out, at: performance.now() }; this.cgSfx("hinge", 0.5, 0.8); this.renderCasino(); return; }
      if (what === "pay") { const out = g.pitPay(); if (!out) return; this.cgSfx("coin", 0.6); this.cgSfx("chest", 0.4);
        this.pitMsg = `The box takes the debt for deadline ${out.deadline}.${out.unlocked ? ` A new charm is unlocked: ${PT.CHARMS[out.unlocked][0]}${out.unlocked2 ? ` and ${PT.CHARMS[out.unlocked2][0]}` : ""}.` : ""}${out.card ? " A card falls out of the slot!" : ""}`;
        if (out.card) { this.cgSfx("cardwin", 0.5); this.pitCard = out.card; } if (out.end) { this.cgNote = `Every debt paid: ${out.end.hero} walks out free with ${out.end.pay} gold.`; this.cgSfx("victory", 0.6); this.renderCasino(); this.cgCoins(this.$("#casino-body"), 20); return; }
        this.pitRing = performance.now(); this.renderCasino(); return; }
      if (what === "phone") { this.pitShop = true; this.cgSfx("tablebell", 0.5); this.renderCasino(); return; }
      if (what === "next") { g.pitNext(); this.pitShop = false; this.pitMsg = `Deadline ${R.deadline}: the house wants ${R.debt()}.`; this.cgSfx("chain", 0.4); this.renderCasino(); return; }
      if (what === "leave") { const r = g.pitEnd("leave"); if (r) { this.cgNote = `${r.hero} steps out with ${r.pay} gold.`; this.cgSfx("door", 0.6); this.cgSfx("coin", 0.5); this.pitShop = false; this.renderCasino(); this.cgCoins(this.$("#casino-body"), 14); } }
    },
    // ---- the room's GL ----
    pitInit(cv) {
      const gl = cv.getContext("webgl", { antialias: true }); this.pitGl = gl; if (!gl) return; this.pitYaw = this.pitYaw || 0; this.pitPitch = this.pitPitch === undefined ? -6 : this.pitPitch;
      const sh = (t, s) => { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); return o; }, pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, PIT_VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, PIT_FS)); gl.bindAttribLocation(pr, 0, "pos"); gl.bindAttribLocation(pr, 1, "uv"); gl.bindAttribLocation(pr, 2, "shade"); gl.linkProgram(pr); this.pitProg = pr;
      const tex = (canvas, smooth) => { const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, canvas); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, smooth ? gl.LINEAR : gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, smooth ? gl.LINEAR : gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE); return t; };
      this.pitAtlasTex = tex(this.pitAtlas(), true); this.pitScreenC = document.createElement("canvas"); this.pitScreenC.width = 512; this.pitScreenC.height = 320; this.pitScreenTex = tex(this.pitScreenC, true);
      this.pitBoardC = document.createElement("canvas"); this.pitBoardC.width = 256; this.pitBoardC.height = 256; this.pitBoardTex = tex(this.pitBoardC, true);
      const st = this.pitStatic(); this.pitBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, this.pitBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(st), gl.STATIC_DRAW); this.pitN = st.length / 6; this.pitDyn = gl.createBuffer();
    },
    // the atlas: 8 x 4 tiles of 128, painted in code
    pitAtlas() {
      const c = document.createElement("canvas"); c.width = 1024; c.height = 512; const p = c.getContext("2d"), R = new CM.Random(31), at = (i) => [(i % 8) * 128, Math.floor(i / 8) * 128];
      const noise = (x, y, col, k) => { p.fillStyle = col; p.fillRect(x, y, 128, 128); for (let n = 0; n < 900; n++) { p.fillStyle = `rgba(0,0,0,${R.next() * k})`; p.fillRect(x + R.int(0, 127), y + R.int(0, 127), 2, 2); } };
      let [x, y] = at(0); noise(x, y, "#244A30", 0.12); p.strokeStyle = "rgba(200,170,90,0.25)"; for (let k = 0; k < 4; k++) for (let j = 0; j < 4; j++) { p.beginPath(); p.ellipse(x + 16 + k * 32, y + 16 + j * 32, 9, 13, 0, 0, Math.PI * 2); p.stroke(); }
      [x, y] = at(1); noise(x, y, "#4A3220", 0.18); p.fillStyle = "rgba(0,0,0,0.35)"; for (let k = 0; k < 128; k += 32) p.fillRect(x, y + k, 128, 2);
      [x, y] = at(2); noise(x, y, "#2A2420", 0.15);
      [x, y] = at(3); noise(x, y, "#8A1A1A", 0.1); p.strokeStyle = "#E0B040"; p.lineWidth = 6; p.strokeRect(x + 4, y + 4, 120, 120); p.fillStyle = "#E0B040"; for (let k = 0; k < 6; k++) p.fillRect(x + 12 + k * 20, y + 112, 8, 8);
      [x, y] = at(4); noise(x, y, "#5A1010", 0.12); p.fillStyle = "#C89030"; p.fillRect(x, y, 128, 6); p.fillRect(x, y + 122, 128, 6);
      [x, y] = at(5); p.fillStyle = "#1A0A08"; p.fillRect(x, y, 128, 128); p.fillStyle = "#FFD060"; p.font = "bold 22px Georgia, serif"; p.textAlign = "center"; p.fillText("THE OLD", x + 64, y + 52); p.fillText("LUCKY", x + 64, y + 84); for (let k = 0; k < 10; k++) { p.fillStyle = k % 2 ? "#FF6040" : "#FFE080"; p.beginPath(); p.arc(x + 8 + k * 12.5, y + 10, 4, 0, Math.PI * 2); p.fill(); p.beginPath(); p.arc(x + 8 + k * 12.5, y + 118, 4, 0, Math.PI * 2); p.fill(); }
      [x, y] = at(6); noise(x, y, "#3A3A40", 0.2); p.fillStyle = "#101010"; p.fillRect(x + 34, y + 56, 60, 10); p.fillStyle = "#C8A040"; p.font = "bold 16px Georgia, serif"; p.textAlign = "center"; p.fillText("THE HOUSE", x + 64, y + 36); p.font = "11px Georgia, serif"; p.fillText("deposits", x + 64, y + 90);
      [x, y] = at(7); noise(x, y, "#4A4A52", 0.25);
      [x, y] = at(8); noise(x, y, "#141414", 0.1); p.strokeStyle = "#C8C0B0"; p.lineWidth = 3; p.beginPath(); p.arc(x + 64, y + 70, 30, 0, Math.PI * 2); p.stroke(); for (let k = 0; k < 10; k++) { const a = k * 0.55 - 1.2; p.beginPath(); p.arc(x + 64 + Math.cos(a) * 20, y + 70 + Math.sin(a) * 20, 4, 0, Math.PI * 2); p.stroke(); }
      [x, y] = at(9); noise(x, y, "#5A3A1E", 0.2); p.strokeStyle = "#2A1A0A"; p.lineWidth = 4; p.strokeRect(x + 12, y + 10, 104, 108); p.fillStyle = "#C8A040"; p.beginPath(); p.arc(x + 100, y + 70, 5, 0, Math.PI * 2); p.fill(); p.fillStyle = "#101010"; p.beginPath(); p.arc(x + 64, y + 40, 6, 0, Math.PI * 2); p.fill();
      [x, y] = at(10); noise(x, y, "#2A2A2E", 0.2); p.strokeStyle = "#6A6A70"; p.lineWidth = 4; for (let k = 8; k < 128; k += 16) { p.beginPath(); p.moveTo(x + k, y); p.lineTo(x + k, y + 128); p.stroke(); }
      [x, y] = at(11); p.fillStyle = "#C81818"; p.fillRect(x, y, 128, 128); p.fillStyle = "rgba(255,255,255,0.4)"; p.beginPath(); p.arc(x + 44, y + 40, 22, 0, Math.PI * 2); p.fill();
      [x, y] = at(12); p.fillStyle = "#FFF4C0"; p.fillRect(x, y, 128, 128);
      [x, y] = at(13); noise(x, y, "#3A2414", 0.15); p.fillStyle = "#C8A040"; p.fillRect(x, y + 60, 128, 6);
      [x, y] = at(14); noise(x, y, "#5A2A18", 0.15);
      [x, y] = at(15); p.fillStyle = "#000"; p.fillRect(x, y, 128, 128);
      return c;
    },
    // a box's six faces, a tile each (or a front tile): x, y, z, u, v, shade
    pitBox(out, x0, y0, z0, x1, y1, z1, tile, front, opts = {}) {
      const uv = (t) => { const u0 = (t % 8) / 8, v0 = Math.floor(t / 8) / 4; return [u0 + 0.002, v0 + 0.002, u0 + 1 / 8 - 0.002, v0 + 1 / 4 - 0.002]; };
      const quad = (a, b, c2, d, t, s) => { const [u0, v0, u1, v1] = uv(t); for (const [P, U, V] of [[a, u0, v1], [b, u1, v1], [c2, u1, v0], [a, u0, v1], [c2, u1, v0], [d, u0, v0]]) out.push(P[0], P[1], P[2], U, V, s); };
      const f = front === undefined ? tile : front, E = opts.emissive || 0;
      quad([x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], f, E || 0.95);        // (the front, toward +z)
      quad([x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0], tile, 0.7);
      quad([x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0], opts.left === undefined ? tile : opts.left, 0.8);
      quad([x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1], opts.right === undefined ? tile : opts.right, 0.8);
      quad([x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0], opts.top === undefined ? tile : opts.top, 1.0);
      quad([x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1], tile, 0.6);
    },
    // the room: walls, floor, ceiling inward; the Old Lucky, the box, the telephone, the door, the trapdoor's frame
    pitStatic() {
      const o = [], B = (...a) => this.pitBox(o, ...a), quad = (pts, t, s) => { const u0 = (t % 8) / 8, v0 = Math.floor(t / 8) / 4, [a, b, c2, d] = pts; for (const [P, U, V] of [[a, u0, v0 + 0.25], [b, u0 + 0.125, v0 + 0.25], [c2, u0 + 0.125, v0], [a, u0, v0 + 0.25], [c2, u0 + 0.125, v0], [d, u0, v0]]) o.push(P[0], P[1], P[2], U, V, s); };
      const X = 1.6, Z0 = -2.2, Z1 = 1.8, H = 2.6;
      for (let i = 0; i < 8; i++) for (let j = 0; j < 10; j++) { const x = -X + i * 0.4, z = Z0 + j * 0.4; if (!(i >= 3 && i <= 4 && j >= 7 && j <= 8)) quad([[x, 0, z + 0.4], [x + 0.4, 0, z + 0.4], [x + 0.4, 0, z], [x, 0, z]], 1, 0.9); quad([[x, H, z], [x + 0.4, H, z], [x + 0.4, H, z + 0.4], [x, H, z + 0.4]], 2, 0.6); }
      for (let x = -X; x < X; x += 0.8) for (let y = 0; y < H; y += 0.65) { quad([[x, y, Z0], [x + 0.8, y, Z0], [x + 0.8, y + 0.65, Z0], [x, y + 0.65, Z0]], 0, 0.85); quad([[x + 0.8, y, Z1], [x, y, Z1], [x, y + 0.65, Z1], [x + 0.8, y + 0.65, Z1]], 0, 0.85); }
      for (let z = Z0; z < Z1; z += 0.8) for (let y = 0; y < H; y += 0.65) { quad([[-X, y, z + 0.8], [-X, y, z], [-X, y + 0.65, z], [-X, y + 0.65, z + 0.8]], 0, 0.8); quad([[X, y, z], [X, y, z + 0.8], [X, y + 0.65, z + 0.8], [X, y + 0.65, z]], 0, 0.8); }
      // the Old Lucky
      B(-0.62, 0, -2.18, 0.62, 1.75, -1.5, 4, 3, { top: 4 }); B(-0.66, 1.75, -2.18, 0.66, 2.1, -1.6, 4, 5, { emissive: 1.9 }); B(-0.7, 0.62, -1.7, 0.7, 0.7, -1.3, 13, 13);
      // the deposit box (left wall), the telephone (right wall), the door (behind), the stool
      B(-X, 0.75, -1.05, -X + 0.22, 1.35, -0.45, 7, 7, { right: 6 }); B(X - 0.12, 1.0, -0.8, X, 1.35, -0.45, 8, 8, { left: 8 });
      B(-0.55, 0, Z1 - 0.06, 0.55, 2.05, Z1, 9, 9); B(-0.22, 0.5, 0.82, 0.22, 0.56, 1.18, 14, 14);
      return o;
    },
    pitMvp(aspect, eye) {
      const f = 1 / Math.tan((68 * Math.PI) / 360), n = 0.05, fa = 30, P = [f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (fa + n) / (n - fa), -1, 0, 0, (2 * fa * n) / (n - fa), 0];
      const mul = (a, b) => { const o = new Array(16).fill(0); for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) for (let k = 0; k < 4; k++) o[j * 4 + i] += a[k * 4 + i] * b[j * 4 + k]; return o; };
      const rx = (d) => { const a = (d * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, 0, 0, 0, 1]; }, ry = (d) => { const a = (d * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a); return [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1]; };
      return mul(P, mul(rx(-this.pitPitch), mul(ry(-this.pitYaw), [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -eye[0], -eye[1], -eye[2], 1])));
    },
    pitEye(now) { const fall = this.pitFalling ? Math.min(1, (now - this.pitFalling) / 1400) : 0; return [Math.sin(now / 2300) * 0.01, 1.18 + Math.sin(now / 1700) * 0.008 - fall * fall * 4, 1.0]; },
    // a click: which thing in the room the ray meets first
    pitClick(e) {
      const cv = this.pitCanvas, r = cv.getBoundingClientRect(), nx = ((e.clientX - r.left) / r.width) * 2 - 1, ny = 1 - ((e.clientY - r.top) / r.height) * 2, t = Math.tan((68 * Math.PI) / 360), aspect = cv.width / cv.height;
      const yr = (this.pitYaw * Math.PI) / 180, pr = (this.pitPitch * Math.PI) / 180, fwd = [-Math.sin(yr) * Math.cos(pr), Math.sin(pr), -Math.cos(yr) * Math.cos(pr)], right = [Math.cos(yr), 0, -Math.sin(yr)], up = [right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0]];
      const d = [0, 1, 2].map((i) => fwd[i] + right[i] * nx * t * aspect + up[i] * ny * t), e0 = this.pitEye(performance.now());
      const things = [["lever", [0.6, 0.8, -1.76], [0.8, 1.6, -1.5]], ["spin", [-0.62, 0, -2.18], [0.62, 2.1, -1.5]], ["pay", [-1.6, 0.75, -1.05], [-1.38, 1.35, -0.45]], ["phone", [1.48, 1.0, -0.8], [1.6, 1.35, -0.45]], ["door", [-0.55, 0, 1.74], [0.55, 2.05, 1.8]]];
      let best = null, bt = 99; for (const [name, lo, hi] of things) { let t0 = 0, t1 = 99, ok = true; for (let i = 0; i < 3 && ok; i++) { if (Math.abs(d[i]) < 1e-9) { if (e0[i] < lo[i] || e0[i] > hi[i]) ok = false; continue; } let a = (lo[i] - e0[i]) / d[i], b = (hi[i] - e0[i]) / d[i]; if (a > b) [a, b] = [b, a]; t0 = Math.max(t0, a); t1 = Math.min(t1, b); if (t0 > t1) ok = false; } if (ok && t0 < bt) { bt = t0; best = name; } }
      const R = this.game.pitRun(); if (!best || !R) return;
      if (best === "lever" || best === "spin") this.pitAct("spin"); else if (best === "pay") { if (R.stage === "spin" && R.coins >= R.debt()) this.pitAct("pay"); else { this.pitMsg = `The box wants ${R.debt()}; you have ${R.coins}.`; this.renderCasino(); } }
      else if (best === "phone") { if (R.stage === "paid") this.pitAct("phone"); else { this.pitMsg = "The telephone is silent. It rings when a debt is paid."; this.renderCasino(); } }
      else if (best === "door") { if (R.stage === "paid") this.pitAct("leave"); else { this.pitMsg = "Locked. It opens when the debt is paid."; this.cgSfx("hinge", 0.3, 0.6); this.renderCasino(); } }
    },
    // the screen of the Old Lucky: five reels by three, spinning and stopping, the lines that pay lit
    pitScreen(now) {
      const p = this.pitScreenC.getContext("2d"), PT = CM.PT, S = this.pitSpinning, cw = 96, ch = 96, ox = 16, oy = 16; p.fillStyle = "#0A0806"; p.fillRect(0, 0, 512, 320);
      const grid = (S && S.out.grid) || this.pitGrid || [["seven", "bell", "clover", "cherry", "lemon"], ["lemon", "seven", "bell", "clover", "cherry"], ["cherry", "lemon", "seven", "bell", "clover"]], syms = Object.keys(PT.SYMS);
      for (let c = 0; c < 5; c++) { const stopAt = S ? S.at + 500 + c * 260 : 0, spinning = S && now < stopAt;
        for (let r = 0; r < 3; r++) { const x = ox + c * cw, y = oy + r * ch; p.fillStyle = "#F4EEDC"; p.fillRect(x + 3, y + 3, cw - 6, ch - 6); const s = spinning ? syms[Math.floor(now / 50 + c * 3 + r) % syms.length] : grid[r][c]; this.pitSym(p, s, x + cw / 2, y + ch / 2 + (spinning ? ((now / 3) % 30) - 15 : 0), spinning); } }
      p.fillStyle = "rgba(0,0,0,0.25)"; p.fillRect(ox, oy, 480, 12); p.fillRect(ox, oy + 276, 480, 12); { const gs = p.createLinearGradient(0, oy, 0, oy + 288); gs.addColorStop(0, "rgba(255,255,255,0.10)"); gs.addColorStop(0.45, "rgba(255,255,255,0)"); gs.addColorStop(0.55, "rgba(0,0,0,0)"); gs.addColorStop(1, "rgba(0,0,0,0.18)"); p.fillStyle = gs; p.fillRect(ox, oy, 480, 288); }
      if (S && now > S.at + 500 + 4 * 260) {
        if (!S.done) { S.done = true; this.pitGrid = S.out.grid; this.pitAfterSpin(S.out); }
        for (const L of S.out.lines) { p.strokeStyle = L.kind === "eyes" ? "#B040FF" : "#FFE040"; p.lineWidth = 5 + 2 * Math.sin(now / 90); p.shadowColor = p.strokeStyle; p.shadowBlur = 10 + 8 * Math.sin(now / 90); p.beginPath();
          if (L.kind === "row") { p.moveTo(ox + L.c * cw + 10, oy + L.r * ch + ch / 2); p.lineTo(ox + (L.c + L.len) * cw - 10, oy + L.r * ch + ch / 2); }
          else if (L.kind === "col") { p.moveTo(ox + L.c * cw + cw / 2, oy + 8); p.lineTo(ox + L.c * cw + cw / 2, oy + 3 * ch - 8); }
          else if (L.kind === "diag") { const r0 = L.dir > 0 ? 0 : 2; p.moveTo(ox + L.c * cw + cw / 2, oy + r0 * ch + ch / 2); p.lineTo(ox + (L.c + 2) * cw + cw / 2, oy + (r0 + 2 * L.dir) * ch + ch / 2); }
          else if (L.kind === "grid" || L.kind === "eyes") { p.rect(ox + 4, oy + 4, 472, 280); }
          p.stroke(); p.shadowBlur = 0; }
        if (S.out.won) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(150, 130, 212, 52); p.fillStyle = "#FFE060"; p.font = "bold 34px Georgia, serif"; p.textAlign = "center"; p.fillText(`+${S.out.won}`, 256, 168); p.textAlign = "left"; }
        if (now > S.at + 3200) this.pitSpinning = null;
      }
    },
    pitSym(p, s, x, y, blur) {
      const col = CM.PIT_SYM_ART[s] || "#888"; p.save(); p.translate(x, y); if (blur) p.globalAlpha = 0.6; p.fillStyle = col;
      if (s === "lemon") { p.beginPath(); p.ellipse(0, 0, 28, 20, 0.3, 0, Math.PI * 2); p.fill(); }
      else if (s === "cherry") { p.strokeStyle = "#2A7A20"; p.lineWidth = 4; p.beginPath(); p.moveTo(-10, 6); p.quadraticCurveTo(0, -30, 12, -26); p.moveTo(12, 6); p.lineTo(12, -26); p.stroke(); p.beginPath(); p.arc(-12, 10, 13, 0, Math.PI * 2); p.arc(14, 10, 13, 0, Math.PI * 2); p.fill(); }
      else if (s === "clover") { for (const [a, b] of [[-11, -11], [11, -11], [-11, 11], [11, 11]]) { p.beginPath(); p.arc(a, b, 13, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#1A6A20"; p.fillRect(-2, 8, 4, 24); }
      else if (s === "bell") { p.beginPath(); p.moveTo(-26, 18); p.quadraticCurveTo(-24, -30, 0, -30); p.quadraticCurveTo(24, -30, 26, 18); p.closePath(); p.fill(); p.beginPath(); p.arc(0, 24, 7, 0, Math.PI * 2); p.fill(); }
      else if (s === "diamond") { p.beginPath(); p.moveTo(0, -30); p.lineTo(26, -6); p.lineTo(0, 30); p.lineTo(-26, -6); p.closePath(); p.fill(); p.fillStyle = "rgba(255,255,255,0.5)"; p.beginPath(); p.moveTo(0, -30); p.lineTo(10, -6); p.lineTo(-10, -6); p.closePath(); p.fill(); }
      else if (s === "chest") { p.fillRect(-28, -14, 56, 36); p.fillStyle = "#E0B040"; p.fillRect(-28, -4, 56, 6); p.fillRect(-5, -6, 10, 14); p.fillStyle = "#6A4018"; p.fillRect(-28, -24, 56, 12); }
      else if (s === "seven") { p.font = "bold 70px Georgia, serif"; p.textAlign = "center"; p.fillText("7", 0, 26); }
      else if (s === "eye") { p.beginPath(); p.ellipse(0, 0, 30, 16, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F0E8FF"; p.beginPath(); p.arc(0, 0, 10, 0, Math.PI * 2); p.fill(); p.fillStyle = "#200830"; p.beginPath(); p.arc(0, 0, 5, 0, Math.PI * 2); p.fill(); }
      p.restore();
    },
    pitAfterSpin(out) {
      const g = this.game;
      if (out.lines.some((l) => l.kind === "eyes")) { this.cgSfx("monster", 0.5); this.pitMsg = "Three of the Pit's eyes look back at you. Nothing."; }
      else if (out.won) { this.cgSfx(out.won >= out.cost * 4 ? "victory" : "coin", 0.55); this.pitMsg = `${out.lines.length} line${out.lines.length > 1 ? "s" : ""}: +${out.won} coins.`; }
      else { this.cgSfx("cardplace", 0.3, 0.7); this.pitMsg = "Nothing on the reels."; }
      if (out.card) { this.cgSfx("cardwin", 0.6); this.pitCard = out.card; this.pitMsg += " A full grid! A card drops into the tray."; }
      if (out.dropped) { this.pitFalling = performance.now(); this.cgSfx("hinge", 0.7, 0.5); setTimeout(() => this.cgSfx("fall", 0.7), 500); setTimeout(() => { this.pitFalling = null; this.pitHold = false; const L = g.pitStore().last; this.cgNote = `The trapdoor! ${L.hero} falls, and comes up again by the bar with a tenth of their health.`; this.renderCasino(); }, 1900); return; }
      this.renderCasino();
    },
    pitBoard(R) {
      const p = this.pitBoardC.getContext("2d"); p.fillStyle = "#1E2A22"; p.fillRect(0, 0, 256, 256); p.strokeStyle = "#7A5A30"; p.lineWidth = 12; p.strokeRect(0, 0, 256, 256);
      p.fillStyle = "#E8E4D8"; p.font = "bold 22px Georgia, serif"; p.textAlign = "center"; p.fillText(`DEADLINE ${R.deadline}/${CM.PT.deadlines}`, 128, 44); p.font = "20px Georgia, serif";
      p.fillText(`OWED  ${R.debt()}`, 128, 90); p.fillText(`COINS  ${R.coins}`, 128, 130); p.fillText(`SPINS  ${R.spinsLeft}`, 128, 170); p.fillText(`TICKETS  ${R.tickets}`, 128, 210); p.textAlign = "left";
    },
    pitFrame(now) {
      const gl = this.pitGl, R = this.game.pitRun() || (this.pitHold ? this.pitView : null), cv = this.pitCanvas; if (!gl || !R) return;
      const gl2 = gl; this.pitScreen(now); this.pitBoard(R);
      gl2.bindTexture(gl2.TEXTURE_2D, this.pitScreenTex); gl2.texImage2D(gl2.TEXTURE_2D, 0, gl2.RGBA, gl2.RGBA, gl2.UNSIGNED_BYTE, this.pitScreenC); gl2.bindTexture(gl2.TEXTURE_2D, this.pitBoardTex); gl2.texImage2D(gl2.TEXTURE_2D, 0, gl2.RGBA, gl2.RGBA, gl2.UNSIGNED_BYTE, this.pitBoardC);
      gl.viewport(0, 0, cv.width, cv.height); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); gl.enable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE); gl.useProgram(this.pitProg);
      const U = (n) => gl.getUniformLocation(this.pitProg, n), flick = 0.92 + 0.06 * Math.sin(now / 70) * Math.sin(now / 311) + (Math.random() < 0.01 ? -0.3 : 0), bulb = [Math.sin(now / 1300) * 0.05, 2.15, -0.5];
      gl.uniformMatrix4fv(U("mvp"), false, new Float32Array(this.pitMvp(cv.width / cv.height, this.pitEye(now)))); gl.uniform3fv(U("bulb"), bulb); gl.uniform1f(U("glow"), this.pitFalling ? Math.max(0, 1 - (now - this.pitFalling) / 1200) : flick); gl.uniform1i(U("tex"), 0); gl.activeTexture(gl.TEXTURE0);
      const draw = (buf, n) => { gl.bindBuffer(gl.ARRAY_BUFFER, buf); for (const a of [0, 1, 2]) gl.enableVertexAttribArray(a); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 24, 0); gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 24, 12); gl.vertexAttribPointer(2, 1, gl.FLOAT, false, 24, 20); gl.drawArrays(gl.TRIANGLES, 0, n); };
      gl.bindTexture(gl.TEXTURE_2D, this.pitAtlasTex); draw(this.pitBuf, this.pitN);
      // the moving things: the lever, the telephone, the bulb and its cord, the trapdoor
      const dyn = [], B = (...a) => this.pitBox(dyn, ...a), pull = this.pitLever ? Math.max(0, 1 - Math.abs((now - this.pitLever) / 250 - 1)) : 0, ring = this.pitRing && R.stage === "paid" && !this.pitShop ? Math.sin(now / 30) * 0.012 * (Math.floor(now / 600) % 2) : 0;
      B(0.62, 0.95 - pull * 0.35, -1.68, 0.68, 1.45 - pull * 0.35, -1.62, 7); B(0.58, 1.42 - pull * 0.35, -1.72, 0.74, 1.56 - pull * 0.35, -1.56, 11);
      B(1.48 + ring, 1.12, -0.74, 1.56 + ring, 1.3, -0.5, 8);
      B(bulb[0] - 0.005, 2.25, bulb[2] - 0.005, bulb[0] + 0.005, 2.6, bulb[2] + 0.005, 15); B(bulb[0] - 0.05, 2.12, bulb[2] - 0.05, bulb[0] + 0.05, 2.25, bulb[2] + 0.05, 12, 12, { emissive: 2.0, top: 12 });
      const open = this.pitFalling ? Math.min(1, (now - this.pitFalling) / 400) : 0; if (open < 1) { const y = -open * 0.8; B(-0.4, y - 0.02, 0.6, 0.4, y, 1.4, 10, 10, { top: 10 }); } B(-0.4, -3, 0.6, 0.4, -2.99, 1.4, 15);
      gl.bindBuffer(gl.ARRAY_BUFFER, this.pitDyn); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(dyn), gl.DYNAMIC_DRAW); draw(this.pitDyn, dyn.length / 6);
      // the screen and the board, lit from within
      const scr = [], quad = (out, a, b, c2, d, s) => { for (const [P, U2, V] of [[a, 0, 1], [b, 1, 1], [c2, 1, 0], [a, 0, 1], [c2, 1, 0], [d, 0, 0]]) out.push(P[0], P[1], P[2], U2, V, s); };
      quad(scr, [-0.5, 0.82, -1.499], [0.5, 0.82, -1.499], [0.5, 1.45, -1.499], [-0.5, 1.45, -1.499], 1.95); gl.bindTexture(gl.TEXTURE_2D, this.pitScreenTex); gl.bindBuffer(gl.ARRAY_BUFFER, this.pitDyn); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(scr), gl.DYNAMIC_DRAW); draw(this.pitDyn, 6);
      const brd = []; quad(brd, [-1.599, 1.45, 0.3], [-1.599, 1.45, -0.4], [-1.599, 2.15, -0.4], [-1.599, 2.15, 0.3], 0.95); gl.bindTexture(gl.TEXTURE_2D, this.pitBoardTex); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(brd), gl.DYNAMIC_DRAW); draw(this.pitDyn, 6);
      if (this.pitFalling) { const k = Math.min(1, (now - this.pitFalling) / 1500); cv.style.filter = `brightness(${1 - k})`; } else cv.style.filter = "";
    },
  });
}
