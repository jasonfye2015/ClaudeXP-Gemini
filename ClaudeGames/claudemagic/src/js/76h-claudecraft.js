"use strict";
// Claudecraft, the window's side (the eighteenth update): its own WebGL on a canvas laid over the view - the atlas of
// block faces painted in code (and the basalt and the gate's light, which moves), each chunk one buffer of its faces,
// fog, an outline round the block under the eye; the crosshair and the hotbar. The world is 64n-claudecraft.js, the
// gate in the town 61k-gate.js; the hands and feet are in 80-main.js.
const CC_VERT = "attribute vec3 pos; attribute vec2 uv; attribute float shade; uniform mat4 mvp; uniform vec3 eye; varying vec2 vUv; varying float vShade; varying float vDist; varying vec3 vPos; void main() { gl_Position = mvp * vec4(pos, 1.0); vUv = uv; vShade = shade; vDist = distance(pos, eye); vPos = pos; }";
const CC_FRAG = "precision mediump float; uniform sampler2D atlas; uniform vec3 fog; uniform float fogStart; uniform float fogEnd; uniform float lines; uniform float time; varying vec2 vUv; varying float vShade; varying float vDist; varying vec3 vPos;\n"
  + "void main() { if (lines > 0.5) { gl_FragColor = vec4(0.0, 0.0, 0.0, 0.85); return; } vec4 c = texture2D(atlas, vUv); if (c.a < 0.1) discard;\n"
  + "  vec3 rgb = c.rgb * min(vShade, 1.0);\n"
  + "  if (vShade > 1.5) { float w = sin(vPos.x * 3.1 + vPos.y * 2.3 + time * 2.7) * 0.5 + 0.5, w2 = sin(vPos.y * 4.0 - time * 3.9 + vPos.z) * 0.5 + 0.5; float band = smoothstep(0.92, 1.0, sin(vPos.y * 6.0 - time * 2.2 + sin(vPos.x * 2.0 + vPos.z * 2.0) * 1.5)); rgb = mix(mix(vec3(0.40, 0.18, 0.80), vec3(0.30, 0.85, 0.82), w * 0.6), vec3(1.0, 0.92, 0.70), band * 0.8 + w2 * 0.12); c.a = 0.8; }\n"
  + "  float f = clamp((vDist - fogStart) / (fogEnd - fogStart), 0.0, 1.0); gl_FragColor = vec4(mix(rgb, fog, vShade > 1.5 ? f * 0.4 : f), c.a); }";
Object.assign(CM.UI.prototype, {
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
    const sw = 44, x0 = W / 2 - (sw * CM.CC.HOTBAR.length) / 2, y0 = H - sw - 10; p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(x0 - 4, y0 - 4, sw * CM.CC.HOTBAR.length + 8, sw + 8);
    CM.CC.HOTBAR.forEach((b, i) => { const face = CM.CC.FACES[b][b === CM.CC.B.GRASS || b === CM.CC.B.LOG ? 1 : 0], t = CM.CC.TILE[face]; p.drawImage(atlas, (t % CM.CC.ATLAS) * 16, Math.floor(t / CM.CC.ATLAS) * 16, 16, 16, x0 + i * sw + 6, y0 + 6, 32, 32); p.strokeStyle = i === w.slot ? "#FFF" : "#808080"; p.lineWidth = i === w.slot ? 3 : 1; p.strokeRect(x0 + i * sw + 1, y0 + 1, sw - 2, sw - 2); });
    p.font = "bold 13px Tahoma, sans-serif"; p.fillStyle = "#FFF"; p.textAlign = "center"; p.fillText(CM.CC.NAMES[CM.CC.HOTBAR[w.slot]], W / 2, y0 - 12);
    p.textAlign = "left"; p.font = "11px Tahoma, sans-serif"; p.fillStyle = "rgba(255,255,255,0.9)"; p.fillText(`Claudecraft   XYZ ${w.pos[0].toFixed(1)} / ${w.pos[1].toFixed(1)} / ${w.pos[2].toFixed(1)}${w.flying ? "   (flying)" : ""}   broken ${cr.broken || 0}, placed ${cr.placed || 0}`, 8, 16);
    p.fillText("WASD walk - mouse look (click to capture) - Space jump (twice: fly) - Shift sprint (down, flying) - left click break - right click place - 1-9 or the wheel - walk into the gate's light to go home", 8, 32);
    if (document.pointerLockElement !== this.$("#craftcanvas")) { p.font = "bold 15px Tahoma, sans-serif"; p.textAlign = "center"; p.fillText("Click to play", W / 2, H / 2 + 34); p.textAlign = "left"; }
    for (const [t, msg] of cr.says || []) if (now - t < 4000) { p.font = "bold 14px Tahoma, sans-serif"; p.textAlign = "center"; p.fillStyle = `rgba(255,240,200,${Math.min(1, (4000 - (now - t)) / 800)})`; p.fillText(msg, W / 2, H * 0.25); p.textAlign = "left"; }
  },
});
