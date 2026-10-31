"use strict";
// Claudecraft, the window's side (the eighteenth update): its own WebGL on a canvas laid over the view - the atlas of
// block faces painted in code (and the basalt and the gate's light, which moves), each chunk one buffer of its faces,
// fog, an outline round the block under the eye; the crosshair and the hotbar. The world is 64n-claudecraft.js, the
// gate in the town 61k-gate.js; the hands and feet are in 80-main.js. (v12.0: the gate's dialog - one hero goes - the
// hero's portrait, health, magic and the clock, the satchel's hotbar with its counts and its window (I), the crack
// that grows over a block being broken, and the glowing bundles left by a fall.)
const CC_VERT = "attribute vec3 pos; attribute vec2 uv; attribute float shade; uniform mat4 mvp; uniform vec3 eye; varying vec2 vUv; varying float vShade; varying float vDist; varying vec3 vPos; void main() { gl_Position = mvp * vec4(pos, 1.0); vUv = uv; vShade = shade; vDist = distance(pos, eye); vPos = pos; }";
const CC_FRAG = "precision mediump float; uniform sampler2D atlas; uniform vec3 fog; uniform float fogStart; uniform float fogEnd; uniform float lines; uniform float time; varying vec2 vUv; varying float vShade; varying float vDist; varying vec3 vPos;\n"
  + "void main() { if (lines > 1.5) { vec2 q = floor(vUv * 16.0); float r = fract(sin(dot(q, vec2(12.9898, 78.233))) * 43758.5453); vec2 d = (q + 0.5) / 16.0 - 0.5; float arm = min(abs(d.x - d.y * 0.6), min(abs(d.y + d.x * 0.4), abs(d.x + d.y))); float reach = length(d) * 1.1 + r * 0.25; if (arm > 0.045 + r * 0.03 + (lines - 2.0) * 0.06 || reach > (lines - 2.0) * 0.75) discard; gl_FragColor = vec4(0.06, 0.05, 0.04, 0.8); return; } if (lines > 0.5) { gl_FragColor = vec4(0.0, 0.0, 0.0, 0.85); return; } vec4 c = texture2D(atlas, vUv); if (c.a < 0.1) discard;\n"
  + "  vec3 rgb = c.rgb * min(vShade, 1.0);\n"
  + "  if (vShade > 2.5) { float k = min(1.0, vShade - 2.5), p2 = 0.5 + 0.5 * sin(time * 4.0 + vPos.y * 7.0); rgb = mix(vec3(0.85, 0.62, 0.18), vec3(1.0, 0.94, 0.62), p2) * (0.55 + 0.45 * k); c.a = 0.95; }\n"
  + "  else if (vShade > 1.5) { float w = sin(vPos.x * 3.1 + vPos.y * 2.3 + time * 2.7) * 0.5 + 0.5, w2 = sin(vPos.y * 4.0 - time * 3.9 + vPos.z) * 0.5 + 0.5; float band = smoothstep(0.92, 1.0, sin(vPos.y * 6.0 - time * 2.2 + sin(vPos.x * 2.0 + vPos.z * 2.0) * 1.5)); rgb = mix(mix(vec3(0.40, 0.18, 0.80), vec3(0.30, 0.85, 0.82), w * 0.6), vec3(1.0, 0.92, 0.70), band * 0.8 + w2 * 0.12) * min(1.0, vShade - 1.0); c.a = 0.8; }\n"
  + "  float f = clamp((vDist - fogStart) / (fogEnd - fogStart), 0.0, 1.0); gl_FragColor = vec4(mix(rgb, fog, vShade > 1.5 ? f * 0.4 : f), c.a); }";
Object.assign(CM.UI.prototype, {
  // the gate's dialog: who steps through (the rest wait in the Keep-yard)
  openCraftGate() {
    const g = this.game, box = this.$("#craft-who"), note = this.$("#craft-note"), K = g.craftStore();
    box.innerHTML = `${g.party.map((h, i) => { const S = K.satchels[CM.craftKey(h)], n = S ? S.reduce((t, x) => t + (x ? x.n : 0), 0) : 0, bun = K.bundles.filter((B) => B.hero === CM.craftKey(h)).length; return `<div class="recruit" style="grid-template-columns: 1fr auto"><div><b>${this.esc(h.name)}</b> the ${this.esc(h.cls)} <small>- ${h.hp} of ${h.max} health${n ? `, ${n} blocks in their satchel` : ""}${bun ? `, ${bun === 1 ? "a bundle" : `${bun} bundles`} left on the island` : ""}</small>${h.hp <= 0 ? "<br><small>Has fallen.</small>" : ""}</div><div class="hire"><button data-craft-hero="${i}" ${h.hp <= 0 ? "disabled" : ""}>Step through</button></div></div>`; }).join("")}
      <p class="small">An island of blocks. Hold the left button to break a block (stone is slow by hand; a pick from the bag makes it quicker) and it goes in your satchel; the right button places from it (1-9 pick the slot, I opens the satchel). A long fall hurts: a fall that would kill wakes you by the island's gate with a tenth of your health, and leaves what you carried in a bundle where you fell. The island keeps everything. Walk into the gate's light to come home.</p>`;
    for (const b of box.querySelectorAll("[data-craft-hero]")) b.addEventListener("click", () => { const why = g.enterCraft(Number(b.dataset.craftHero)); note.textContent = why || ""; if (!why) { this.closeDialogs(); this.refresh(); } });
    note.textContent = "";
    this.openDialog("#dlg-craftgate");
  },
  ccToggleSatchel() { this.ccSatchelOpen = !this.ccSatchelOpen; this.ccPick = null; if (this.ccSatchelOpen && document.pointerLockElement && document.exitPointerLock) document.exitPointerLock(); },
  // a click in the satchel's window: the first picks a slot up, the second puts it down (swapping)
  ccSatchelClick(e) {
    const cr = this.game.craft, h = this.$("#crafthud"); if (!cr || !h) return; const r = h.getBoundingClientRect(), x = (e.clientX - r.left) * (h.width / r.width), y = (e.clientY - r.top) * (h.height / r.height);
    const i = (this.ccSatRects || []).findIndex(([rx, ry, rw, rh]) => x >= rx && x < rx + rw && y >= ry && y < ry + rh);
    if (i < 0) { this.ccPick = null; return; }
    if (this.ccPick === null || this.ccPick === undefined) { if (cr.satchel.slots[i]) this.ccPick = i; return; }
    cr.satchel.swap(this.ccPick, i); this.ccPick = null; try { CM.audio.play("cardplace", 0.3, 0, 1.1); } catch (er) { /* */ }
  },
  ccTileOf(b) { const face = CM.CC.FACES[b][b === CM.CC.B.GRASS || b === CM.CC.B.LOG ? 1 : 0], t = CM.CC.TILE[face]; return [(t % CM.CC.ATLAS) * 16, Math.floor(t / CM.CC.ATLAS) * 16]; },
  ccDrawSlot(p, atlas, s, x, y, size, lit, picked) {
    p.fillStyle = lit ? "rgba(255,255,255,0.18)" : "rgba(0,0,0,0.35)"; p.fillRect(x, y, size, size);
    if (s) { const [tx, ty] = this.ccTileOf(s.b), m = Math.round(size * 0.14); p.globalAlpha = picked ? 0.4 : 1; p.drawImage(atlas, tx, ty, 16, 16, x + m, y + m, size - 2 * m, size - 2 * m); p.globalAlpha = 1;
      if (s.n > 1) { p.font = "bold 12px Tahoma, sans-serif"; p.textAlign = "right"; p.fillStyle = "#000"; p.fillText(String(s.n), x + size - 3, y + size - 3); p.fillStyle = "#FFF"; p.fillText(String(s.n), x + size - 4, y + size - 4); p.textAlign = "left"; } }
    p.strokeStyle = lit ? "#FFF" : picked ? "#F0D060" : "#808080"; p.lineWidth = lit || picked ? 3 : 1; p.strokeRect(x + 1, y + 1, size - 2, size - 2);
  },
  // the atlas, painted in code as world.py paints it (and two of our own: the basalt and the gate's light)
  ccAtlas() {
    if (this.ccAtlasC) return this.ccAtlasC;
    const c = document.createElement("canvas"); c.width = 16 * CM.CC.ATLAS; c.height = 16 * 4; const p = c.getContext("2d"), R = new CM.Random(7), u = (a, b) => a + (b - a) * R.next();
    const noisy = (ox, oy, hex, spread, alpha = 255) => { const n = parseInt(hex.slice(1), 16); for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) { const k = u(-spread, spread), f = (v) => Math.max(0, Math.min(255, Math.round(v + k))); p.fillStyle = `rgba(${f(n >> 16)},${f((n >> 8) & 255)},${f(n & 255)},${alpha / 255})`; p.fillRect(ox + x, oy + y, 1, 1); } };
    const at = (name) => { const i = CM.CC.TILE[name]; return [(i % CM.CC.ATLAS) * 16, Math.floor(i / CM.CC.ATLAS) * 16]; };
    let [x, y] = at("grass_top"); noisy(x, y, "#5FA33A", 22);
    [x, y] = at("dirt"); noisy(x, y, "#866043", 20);
    [x, y] = at("grass_side"); noisy(x, y, "#866043", 20); for (let i = 0; i < 16; i++) { const d = 3 + R.int(0, 2); for (let j = 0; j < d; j++) { p.fillStyle = `rgb(${Math.round(95 * (1 - R.next() * 0.2))},${Math.round(163 * (1 - R.next() * 0.2))},58)`; p.fillRect(x + i, y + j, 1, 1); } }
    [x, y] = at("stone"); noisy(x, y, "#7F7F7F", 18);
    [x, y] = at("sand"); noisy(x, y, "#DBCF95", 12);
    [x, y] = at("gravel"); noisy(x, y, "#8A8580", 30);
    [x, y] = at("snow"); noisy(x, y, "#F2F6FA", 6);
    [x, y] = at("log_side"); noisy(x, y, "#6B5233", 12); p.fillStyle = "#4E3B24"; for (const lx of [2, 6, 10, 13]) p.fillRect(x + lx, y, 1, 16);
    [x, y] = at("log_top"); noisy(x, y, "#A68A5A", 10); p.strokeStyle = "#6B5233"; p.strokeRect(x + 0.5, y + 0.5, 15, 15); p.strokeRect(x + 3.5, y + 3.5, 9, 9);
    [x, y] = at("leaves"); for (let j = 0; j < 16; j++) for (let i = 0; i < 16; i++) if (R.next() < 0.78) { const k = 0.9 + R.next() * 0.4; p.fillStyle = `rgb(${Math.round(62 / k)},${Math.round(122 / k)},${Math.round(38 / k)})`; p.fillRect(x + i, y + j, 1, 1); }
    [x, y] = at("planks"); noisy(x, y, "#B08D57", 10); p.fillStyle = "#7E6238"; for (const ly of [3, 7, 11, 15]) p.fillRect(x, y + ly, 16, 1);
    [x, y] = at("cobble"); noisy(x, y, "#7A7A7A", 26); p.strokeStyle = "#4F4F4F"; for (const [rx, ry, rw, rh] of [[0, 0, 7, 5], [8, 0, 7, 6], [0, 6, 5, 5], [6, 7, 9, 4], [0, 12, 9, 3], [10, 12, 5, 3]]) p.strokeRect(x + rx + 0.5, y + ry + 0.5, rw, rh);
    [x, y] = at("water"); noisy(x, y, "#3459C9", 10, 170);
    [x, y] = at("glass"); p.fillStyle = "rgba(200,230,255,0.16)"; p.fillRect(x, y, 16, 16); p.strokeStyle = "rgba(230,245,255,0.9)"; p.strokeRect(x + 0.5, y + 0.5, 15, 15); p.beginPath(); p.moveTo(x + 4, y + 4); p.lineTo(x + 7, y + 1); p.stroke();
    [x, y] = at("brick"); noisy(x, y, "#9B4A3A", 10); p.fillStyle = "#C9BFB0"; for (const ly of [3, 7, 11, 15]) p.fillRect(x, y + ly, 16, 1); [0, 4, 8, 12].forEach((ly, row) => { for (const lx of row % 2 ? [3, 11] : [7, 15]) p.fillRect(x + lx, y + ly, 1, 3); });
    [x, y] = at("bedrock"); noisy(x, y, "#3A3A3A", 40);
    [x, y] = at("basalt"); noisy(x, y, "#2E2C38", 8); p.fillStyle = "#C8A040"; p.fillRect(x, y, 16, 1); p.fillRect(x, y + 15, 16, 1); p.fillStyle = "#B070FF"; for (const [rx, ry] of [[7, 3], [7, 4], [7, 5], [7, 6], [7, 7], [7, 8], [7, 9], [7, 10], [7, 11], [7, 12], [5, 5], [6, 6], [8, 6], [9, 5], [5, 10], [9, 10]]) p.fillRect(x + rx, y + ry, 1, 1);   // (dark basalt, gold-edged, a carved rune glowing in it: the Keep-yard gate's own)
    [x, y] = at("gate"); noisy(x, y, "#8050D0", 24, 210); p.fillStyle = "rgba(120,240,230,0.6)"; for (let k = 0; k < 16; k += 4) p.fillRect(x, y + k, 16, 1);
    this.ccAtlasC = c; return c;
  },
  ccStart(world) {
    let c = this.$("#craftcanvas"); if (!c) { c = document.createElement("canvas"); c.id = "craftcanvas"; this.$("#view").appendChild(c); }
    const gl = this.ccGl = c.getContext("webgl", { antialias: false }) || c.getContext("experimental-webgl"); if (!gl) return false;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
    const prog = this.ccProg = gl.createProgram(); gl.attachShader(prog, sh(gl.VERTEX_SHADER, CC_VERT)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, CC_FRAG)); gl.bindAttribLocation(prog, 0, "pos"); gl.bindAttribLocation(prog, 1, "uv"); gl.bindAttribLocation(prog, 2, "shade"); gl.linkProgram(prog);
    const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, this.ccAtlas()); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    this.ccTex = tex; this.ccChunks = new Map(); this.ccLine = gl.createBuffer();
    const pcx = Math.floor(this.game.craft.walker.pos[0] / CM.CC.CHUNK), pcz = Math.floor(this.game.craft.walker.pos[2] / CM.CC.CHUNK);
    this.ccPending = []; for (let cx = 0; cx < CM.CC.CHUNKS; cx++) for (let cz = 0; cz < CM.CC.CHUNKS; cz++) this.ccPending.push([cx, cz]);
    this.ccPending.sort((a, b) => (a[0] - pcx) ** 2 + (a[1] - pcz) ** 2 - ((b[0] - pcx) ** 2 + (b[1] - pcz) ** 2));
    this.ccDirty = new Set(); this.ccSlot = 0;
    return true;
  },
  ccBuild(cx, cz) {
    const gl = this.ccGl, [op, wa] = this.game.craft.world.meshChunk(cx, cz), key = `${cx},${cz}`; let ch = this.ccChunks.get(key);
    if (!ch) { ch = { op: gl.createBuffer(), wa: gl.createBuffer() }; this.ccChunks.set(key, ch); }
    gl.bindBuffer(gl.ARRAY_BUFFER, ch.op); gl.bufferData(gl.ARRAY_BUFFER, op, gl.STATIC_DRAW); ch.nOp = op.length / 6;
    gl.bindBuffer(gl.ARRAY_BUFFER, ch.wa); gl.bufferData(gl.ARRAY_BUFFER, wa, gl.STATIC_DRAW); ch.nWa = wa.length / 6;
  },
  ccDirtyAt(x, z) { const C = CM.CC.CHUNK; for (const [dx, dz] of [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]]) { const cx = Math.floor((x + dx) / C), cz = Math.floor((z + dz) / C); if (cx >= 0 && cz >= 0 && cx < CM.CC.CHUNKS && cz < CM.CC.CHUNKS) this.ccDirty.add(`${cx},${cz}`); } },
  ccMvp(w, aspect) {
    const f = 1 / Math.tan((70 * Math.PI) / 360), n = 0.05, fa = 200, P = [f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (fa + n) / (n - fa), -1, 0, 0, (2 * fa * n) / (n - fa), 0];
    const mul = (a, b) => { const o = new Array(16).fill(0); for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) for (let k = 0; k < 4; k++) o[j * 4 + i] += a[k * 4 + i] * b[j * 4 + k]; return o; };
    const rx = (d) => { const a = (d * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, 0, 0, 0, 1]; }, ry = (d) => { const a = (d * Math.PI) / 180, c = Math.cos(a), s = Math.sin(a); return [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1]; };
    const e = w.eye(), T = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -e[0], -e[1], -e[2], 1];
    return mul(P, mul(rx(-w.pitch), mul(ry(-w.yaw), T)));
  },
  drawCraft(now, dt) {
    const g = this.game, cr = g.craft, w = cr.walker, c = this.$("#craftcanvas"), gl = this.ccGl; if (!gl) return;
    const r = c.getBoundingClientRect(); if (c.width !== Math.round(r.width) || c.height !== Math.round(r.height)) { c.width = Math.max(320, Math.round(r.width)); c.height = Math.max(200, Math.round(r.height)); }
    const t0 = performance.now(); while (this.ccPending.length && performance.now() - t0 < 12) this.ccBuild(...this.ccPending.shift());   // (the island built a few chunks a frame)
    for (const k of this.ccDirty) this.ccBuild(...k.split(",").map(Number)); this.ccDirty.clear();
    gl.viewport(0, 0, c.width, c.height); gl.clearColor(0.53, 0.71, 0.96, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); gl.enable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE);
    const P = this.ccProg; gl.useProgram(P); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, this.ccTex);
    const U = (n) => gl.getUniformLocation(P, n);
    gl.uniform1i(U("atlas"), 0); gl.uniformMatrix4fv(U("mvp"), false, new Float32Array(this.ccMvp(w, c.width / c.height))); gl.uniform3fv(U("eye"), w.eye()); gl.uniform3fv(U("fog"), [0.53, 0.71, 0.96]); gl.uniform1f(U("fogStart"), 40); gl.uniform1f(U("fogEnd"), 90); gl.uniform1f(U("lines"), 0); gl.uniform1f(U("time"), now / 1000);
    const draw = (buf, n, mode = gl.TRIANGLES) => { if (!n) return; gl.bindBuffer(gl.ARRAY_BUFFER, buf); for (const a of [0, 1, 2]) gl.enableVertexAttribArray(a); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 24, 0); gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 24, 12); gl.vertexAttribPointer(2, 1, gl.FLOAT, false, 24, 20); gl.drawArrays(mode, 0, n); };
    for (const ch of this.ccChunks.values()) draw(ch.op, ch.nOp);
    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false);
    for (const ch of this.ccChunks.values()) draw(ch.wa, ch.nWa);
    gl.depthMask(true);
    const hit = cr.target && cr.target[0];
    if (hit) { const [x, y, z] = hit, e = 0.003, C = [[x - e, y - e, z - e], [x + 1 + e, y - e, z - e], [x + 1 + e, y - e, z + 1 + e], [x - e, y - e, z + 1 + e], [x - e, y + 1 + e, z - e], [x + 1 + e, y + 1 + e, z - e], [x + 1 + e, y + 1 + e, z + 1 + e], [x - e, y + 1 + e, z + 1 + e]], out = [];
      for (const [a, b] of [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]]) out.push(...C[a], 0, 0, 1, ...C[b], 0, 0, 1);
      gl.uniform1f(U("lines"), 1); gl.bindBuffer(gl.ARRAY_BUFFER, this.ccLine); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(out), gl.DYNAMIC_DRAW); draw(this.ccLine, 24, gl.LINES); }
    if (hit && cr.dig && cr.dig.key === hit.join(",") && cr.dig.need < Infinity) {          // (the crack, growing with the dig)
      const [x, y, z] = hit, e2 = 0.004, out = [];
      for (const [, , corners] of CM.CC.FACE_DEFS) for (const [dx, dy, dz, u, v] of corners) out.push(x + (dx ? 1 + e2 : -e2), y + (dy ? 1 + e2 : -e2), z + (dz ? 1 + e2 : -e2), u, v, 1);
      if (!this.ccCrackBuf) this.ccCrackBuf = gl.createBuffer(); gl.uniform1f(U("lines"), 2 + Math.min(1, cr.dig.t / cr.dig.need) * 1.45); gl.bindBuffer(gl.ARRAY_BUFFER, this.ccCrackBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(out), gl.DYNAMIC_DRAW); draw(this.ccCrackBuf, out.length / 6); }
    if (cr.bundles.length) {                                                   // (the bundles: small glowing blocks, bobbing)
      const [tx, ty] = [(CM.CC.TILE.gate % CM.CC.ATLAS) / CM.CC.ATLAS, Math.floor(CM.CC.TILE.gate / CM.CC.ATLAS) / 4], out = [], s2 = 0.6;
      for (const B of cr.bundles) { const bob = Math.sin(now / 400 + B.x) * 0.15 + 0.45; for (const [nrm, sh, corners] of CM.CC.FACE_DEFS) for (const [dx, dy, dz, u, v] of corners) out.push(B.x - s2 / 2 + dx * s2, B.y + bob + dy * s2, B.z - s2 / 2 + dz * s2, tx + (u / CM.CC.ATLAS), ty + v / 4, 2.5 + sh); }
      if (!this.ccBundleBuf) this.ccBundleBuf = gl.createBuffer(); gl.uniform1f(U("lines"), 0); gl.bindBuffer(gl.ARRAY_BUFFER, this.ccBundleBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(out), gl.DYNAMIC_DRAW); draw(this.ccBundleBuf, out.length / 6); }
    gl.disable(gl.BLEND);
    this.ccHud(cr, now);
  },
  // the HUD on a 2D canvas over the GL one: the crosshair, the hotbar, where you stand, a word of help
  ccHud(cr, now) {
    let h = this.$("#crafthud"); if (!h) { h = document.createElement("canvas"); h.id = "crafthud"; this.$("#view").appendChild(h); }
    const r = h.getBoundingClientRect(); if (h.width !== Math.round(r.width) || h.height !== Math.round(r.height)) { h.width = Math.round(r.width); h.height = Math.round(r.height); }
    const p = h.getContext("2d"), W = h.width, H = h.height, w = cr.walker, atlas = this.ccAtlas(); p.clearRect(0, 0, W, H); p.imageSmoothingEnabled = false;
    if (this.ccPending.length) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, W, H); p.fillStyle = "#FFF"; p.font = "bold 18px Tahoma, sans-serif"; p.textAlign = "center"; p.fillText("Building the island", W / 2, H / 2 - 20); p.fillStyle = "#404040"; p.fillRect(W / 2 - 150, H / 2, 300, 8); p.fillStyle = "#7FD46A"; p.fillRect(W / 2 - 150, H / 2, 300 * (1 - this.ccPending.length / 100), 8); p.textAlign = "left"; return; }
    p.strokeStyle = "rgba(255,255,255,0.86)"; p.lineWidth = 2; p.beginPath(); p.moveTo(W / 2 - 9, H / 2); p.lineTo(W / 2 + 9, H / 2); p.moveTo(W / 2, H / 2 - 9); p.lineTo(W / 2, H / 2 + 9); p.stroke();
    if (this.ccHurtAt && now - this.ccHurtAt < 400) { p.fillStyle = `rgba(200,20,10,${0.35 * (1 - (now - this.ccHurtAt) / 400)})`; p.fillRect(0, 0, W, H); }
    if (this.ccDeadAt && now - this.ccDeadAt < 1500) { p.fillStyle = `rgba(0,0,0,${0.85 * (1 - (now - this.ccDeadAt) / 1500)})`; p.fillRect(0, 0, W, H); }
    if (cr.dig && cr.dig.need < Infinity) { p.strokeStyle = "rgba(255,255,255,0.9)"; p.lineWidth = 3; p.beginPath(); p.arc(W / 2, H / 2, 16, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI * Math.min(1, cr.dig.t / cr.dig.need)); p.stroke(); }
    const sw = 44, x0 = W / 2 - (sw * 9) / 2, y0 = H - sw - 10, S = cr.satchel.slots; p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(x0 - 4, y0 - 4, sw * 9 + 8, sw + 8);
    for (let i = 0; i < 9; i++) this.ccDrawSlot(p, atlas, S[i], x0 + i * sw, y0, sw, i === w.slot, false);
    p.font = "bold 13px Tahoma, sans-serif"; p.fillStyle = "#FFF"; p.textAlign = "center"; p.fillText(S[w.slot] ? `${CM.CC.NAMES[S[w.slot].b]} (${S[w.slot].n})` : "(empty - break something)", W / 2, y0 - 12);
    // the hero: portrait, health and magic, and the hour
    const hero = cr.hero, px = 10, py = 10; if (!this.ccPor || this.ccPor.cls !== hero.cls) { let c = null; try { c = CM.art.portraitDrawn(hero.cls, 56); } catch (er) { /* */ } this.ccPor = { cls: hero.cls, c }; }
    p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(px - 4, py - 4, 236, 64); if (this.ccPor.c) p.drawImage(this.ccPor.c, px, py, 56, 56);
    const bar = (y, v, m, col, label) => { p.fillStyle = "#202020"; p.fillRect(px + 62, y, 160, 12); p.fillStyle = col; p.fillRect(px + 62, y, 160 * Math.max(0, Math.min(1, m ? v / m : 0)), 12); p.font = "10px Tahoma, sans-serif"; p.fillStyle = "#FFF"; p.textAlign = "left"; p.fillText(label, px + 66, y + 10); };
    p.font = "bold 12px Tahoma, sans-serif"; p.fillStyle = "#FFF"; p.textAlign = "left"; p.fillText(`${hero.name} the ${hero.cls}`, px + 62, py + 10);
    bar(py + 16, hero.hp, hero.max, hero.hp < hero.max * 0.25 ? "#E04030" : "#C83030", `${Math.max(0, hero.hp)} / ${hero.max}`);
    if (hero.maxmp) bar(py + 31, hero.mp, hero.maxmp, "#3F7DE0", `${hero.mp} / ${hero.maxmp}`);
    let clock = ""; try { const m = CM.minuteOf(this.game), hh = Math.floor(m / 60), mm = m % 60; clock = `${hh}:${mm < 10 ? "0" : ""}${mm}, ${CM.hourWord(CM.hourOf(this.game))}`; } catch (er) { /* */ }
    p.font = "11px Tahoma, sans-serif"; p.fillText(clock, px + 62, py + 56);
    p.font = "11px Tahoma, sans-serif"; p.fillStyle = "rgba(255,255,255,0.9)"; p.textAlign = "right"; p.fillText(`XYZ ${w.pos[0].toFixed(0)} / ${w.pos[1].toFixed(0)} / ${w.pos[2].toFixed(0)}   broken ${cr.broken || 0}, placed ${cr.placed || 0}${cr.bundles.length ? `   bundles on the island: ${cr.bundles.length}` : ""}`, W - 8, 16);
    p.fillText("WASD walk - mouse look - Space jump - Shift sprint", W - 8, 32); p.fillText("hold left: break - right: place - 1-9 / wheel - I: satchel", W - 8, 46); p.fillText("walk into the gate's light to go home", W - 8, 60); p.textAlign = "left";
    if (this.ccSatchelOpen) {                                                   // (the satchel's window: 3 rows of 9, the hotbar the first)
      const ss = 46, gx = W / 2 - (ss * 9) / 2, gy = H / 2 - ss * 1.5 - 20; p.fillStyle = "rgba(20,16,12,0.88)"; p.fillRect(gx - 14, gy - 36, ss * 9 + 28, ss * 3 + 76); p.strokeStyle = "#C8A040"; p.lineWidth = 2; p.strokeRect(gx - 14, gy - 36, ss * 9 + 28, ss * 3 + 76);
      p.font = "bold 14px Tahoma, sans-serif"; p.fillStyle = "#F0E0B0"; p.fillText(`${hero.name}'s satchel`, gx, gy - 14); this.ccSatRects = [];
      for (let i = 0; i < CM.CC.SATCHEL; i++) { const r = Math.floor(i / 9), x = gx + (i % 9) * ss, y = gy + r * ss + (r ? 8 : 0); this.ccSatRects.push([x, y, ss, ss]); this.ccDrawSlot(p, atlas, S[i], x, y, ss, false, i === this.ccPick); }
      p.font = "11px Tahoma, sans-serif"; p.fillStyle = "#D8D0C0"; p.fillText("Click a stack, then a slot, to move it (the top row is the hotbar). I or E closes.", gx, gy + ss * 3 + 26);
    } else if (document.pointerLockElement !== this.$("#craftcanvas")) { p.font = "bold 15px Tahoma, sans-serif"; p.fillStyle = "#FFF"; p.textAlign = "center"; p.fillText("Click to play", W / 2, H / 2 + 34); p.textAlign = "left"; }
    const recent = (cr.says || []).filter(([t]) => now - t < 4000).slice(-3);
    recent.forEach(([t, msg], k) => { p.font = "bold 14px Tahoma, sans-serif"; p.textAlign = "center"; p.fillStyle = "rgba(0,0,0,0.6)"; p.fillText(msg, W / 2 + 1, H * 0.22 + k * 20 + 1); p.fillStyle = `rgba(255,240,200,${Math.min(1, (4000 - (now - t)) / 800)})`; p.fillText(msg, W / 2, H * 0.22 + k * 20); p.textAlign = "left"; });
  },
});
