"use strict";
// Claudecraft, the window's side (the eighteenth update): its own WebGL on a canvas laid over the view - the atlas of
// block faces painted in code (and the basalt and the gate's light, which moves), each chunk one buffer of its faces,
// fog, an outline round the block under the eye; the crosshair and the hotbar. The world is 64n-claudecraft.js, the
// gate in the town 61k-gate.js; the hands and feet are in 80-main.js. (v12.0: the gate's dialog - one hero goes - the
// hero's portrait, health, magic and the clock, the satchel's hotbar with its counts and its window (I), the crack
// that grows over a block being broken, and the glowing bundles left by a fall.)
const CC_VERT = "attribute vec3 pos; attribute vec2 uv; attribute float shade; attribute float sky; uniform mat4 mvp; uniform vec3 eye; varying vec2 vUv; varying float vShade; varying float vDist; varying vec3 vPos; varying float vSky; void main() { gl_Position = mvp * vec4(pos, 1.0); vUv = uv; vShade = shade; vDist = distance(pos, eye); vPos = pos; vSky = sky; }";
const CC_FRAG = "precision mediump float; uniform sampler2D atlas; uniform vec3 fog; uniform float fogStart; uniform float fogEnd; uniform float lines; uniform float time; uniform float lamp; uniform float daylight; varying vec2 vUv; varying float vShade; varying float vDist; varying vec3 vPos; varying float vSky;\n"
  + "void main() { if (lines > 1.5) { vec2 q = floor(vUv * 16.0); float r = fract(sin(dot(q, vec2(12.9898, 78.233))) * 43758.5453); vec2 d = (q + 0.5) / 16.0 - 0.5; float arm = min(abs(d.x - d.y * 0.6), min(abs(d.y + d.x * 0.4), abs(d.x + d.y))); float reach = length(d) * 1.1 + r * 0.25; if (arm > 0.045 + r * 0.03 + (lines - 2.0) * 0.06 || reach > (lines - 2.0) * 0.75) discard; gl_FragColor = vec4(0.06, 0.05, 0.04, 0.8); return; } if (lines > 0.5) { gl_FragColor = vec4(0.0, 0.0, 0.0, 0.85); return; } vec4 c = texture2D(atlas, vUv); if (c.a < 0.1) discard; if (vShade > 4.0) { gl_FragColor = vec4(c.rgb * (vShade > 4.6 ? 1.6 : 1.0), c.a); return; }\n"
  + "  float lv = floor(vSky + 0.5), sk = floor(lv / 16.0 + 0.01) / 15.0, tc = (lv - floor(lv / 16.0 + 0.01) * 16.0) / 15.0, skyLit = sk * daylight;\n"
  + "  float carried = clamp(1.0 - vDist / lamp, 0.0, 1.0); carried = (1.0 - (1.0 - carried) * (1.0 - carried)) * 0.92; float near = max(carried, tc); float lit = max(0.035, max(skyLit, near));\n"
  + "  vec3 rgb = c.rgb * min(vShade, 1.0) * lit * mix(vec3(1.0), vec3(1.0, 0.86, 0.66), near > skyLit ? 0.8 : 0.0);\n"
  + "  if (vShade > 2.5) { float k = min(1.0, vShade - 2.5), p2 = 0.5 + 0.5 * sin(time * 4.0 + vPos.y * 7.0); rgb = mix(vec3(0.85, 0.62, 0.18), vec3(1.0, 0.94, 0.62), p2) * (0.55 + 0.45 * k); c.a = 0.95; }\n"
  + "  else if (vShade > 1.5) { float w = sin(vPos.x * 3.1 + vPos.y * 2.3 + time * 2.7) * 0.5 + 0.5, w2 = sin(vPos.y * 4.0 - time * 3.9 + vPos.z) * 0.5 + 0.5; float band = smoothstep(0.92, 1.0, sin(vPos.y * 6.0 - time * 2.2 + sin(vPos.x * 2.0 + vPos.z * 2.0) * 1.5)); rgb = mix(mix(vec3(0.40, 0.18, 0.80), vec3(0.30, 0.85, 0.82), w * 0.6), vec3(1.0, 0.92, 0.70), band * 0.8 + w2 * 0.12) * min(1.0, vShade - 1.0); c.a = 0.8; }\n"
  + "  float f = clamp((vDist - fogStart) / (fogEnd - fogStart), 0.0, 1.0); gl_FragColor = vec4(mix(rgb, vShade > 1.5 ? fog : fog * sk, vShade > 1.5 ? f * 0.4 : f), c.a); }";
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
  ccToggleSatchel() { this.ccSatchelOpen = !this.ccSatchelOpen; this.ccChestKey = null; this.ccPick = null; this.ccScroll = 0; if (this.ccSatchelOpen && document.pointerLockElement && document.exitPointerLock) document.exitPointerLock(); },
  // (v12.6) a signpost's name, asked for when it is placed or right-clicked
  openSignName(key) { const g = this.game, K = g.craftStore(), s = (K.signs || []).find((q) => `${q.x},${q.y},${q.z}` === key); if (!s) return; if (document.pointerLockElement && document.exitPointerLock) document.exitPointerLock(); const inp = this.$("#sign-name"); inp.value = s.name; this.ccSignKey = key; this.openDialog("#dlg-sign"); setTimeout(() => { inp.focus(); inp.select(); }, 30); },
  ccOpenChest(key) { this.ccSatchelOpen = true; this.ccChestKey = key; this.ccPick = null; if (document.pointerLockElement && document.exitPointerLock) document.exitPointerLock(); },
  ccCloseWindow() { this.ccSatchelOpen = false; this.ccChestKey = null; this.ccPick = null; },
  // a click in the window: a recipe makes it; in a chest's window a stack moves across whole; in the satchel the first
  // click picks a slot up and the second puts it down (swapping)
  ccSatchelClick(e) {
    const g = this.game, cr = g.craft, h = this.$("#crafthud"); if (!cr || !h) return; const r = h.getBoundingClientRect(), x = (e.clientX - r.left) * (h.width / r.width), y = (e.clientY - r.top) * (h.height / r.height);
    const hit = (this.ccRects || []).find((q) => x >= q.x && x < q.x + q.w && y >= q.y && y < q.y + q.h);
    if (!hit) { this.ccPick = null; return; }
    const click = () => { try { CM.audio.play("cardplace", 0.3, 0, 1.1); } catch (er) { /* */ } };
    if (hit.kind === "recipe") { const why = g.craftMake(hit.id); if (why) g.craftSay(why); else { click(); try { CM.audio.play("grind", 0.35, 0, 1.2); } catch (er) { /* */ } } return; }
    if (this.ccChestKey) { if (g.craftChestMove(this.ccChestKey, hit.kind, hit.i)) click(); return; }
    if (this.ccPick === null || this.ccPick === undefined) { if (cr.satchel.slots[hit.i]) this.ccPick = hit.i; return; }
    cr.satchel.swap(this.ccPick, hit.i); this.ccPick = null; click();
  },
  // the window itself, drawn on the HUD
  ccWindow(p, atlas, cr, W, H) {
    const g = this.game, ss = Math.max(30, Math.min(40, Math.floor((W - 380) / 9))), chest = this.ccChestKey ? g.craftChest(this.ccChestKey) : null, gridW = ss * 9;
    const panelW = chest ? 0 : Math.min(300, W - gridW - 60), ww = gridW + (panelW ? panelW + 20 : 0) + 28, wh = Math.min(H - 30, chest ? ss * 6 + 110 : Math.max(ss * 3 + 90, 320));
    const wx = Math.max(6, W / 2 - ww / 2), wy = Math.max(6, H / 2 - wh / 2) - 10; this.ccRects = [];
    p.fillStyle = "rgba(20,16,12,0.92)"; p.fillRect(wx, wy, ww, wh); p.strokeStyle = "#C8A040"; p.lineWidth = 2; p.strokeRect(wx, wy, ww, wh);
    const grid = (title, store, kind, gx, gy, sep) => { p.font = "bold 13px Tahoma, sans-serif"; p.fillStyle = "#F0E0B0"; p.textAlign = "left"; p.fillText(title, gx, gy - 8);
      for (let i = 0; i < store.slots.length; i++) { const row = Math.floor(i / 9), x = gx + (i % 9) * ss, y = gy + row * ss + (sep && row ? 6 : 0); this.ccRects.push({ kind, i, x, y, w: ss, h: ss }); this.ccDrawSlot(p, atlas, store.slots[i], x, y, ss, false, kind === "satchel" && i === this.ccPick); } };
    const gx = wx + 14;
    if (chest) {
      grid("The chest (kept safe on the island)", chest, "chest", gx, wy + 30, false);
      grid(`${cr.hero.name}'s satchel`, cr.satchel, "satchel", gx, wy + 30 + ss * 3 + 30, true);
      p.font = "11px Tahoma, sans-serif"; p.fillStyle = "#D8D0C0"; p.fillText("Click a stack to move it across. I, E or Esc closes.", gx, wy + wh - 10);
      return;
    }
    grid(`${cr.hero.name}'s satchel`, cr.satchel, "satchel", gx, wy + 30, true);
    p.font = "11px Tahoma, sans-serif"; p.fillStyle = "#D8D0C0"; const tips = ["Click a stack, then a slot, to move it", "(the top row is the hotbar). I, E or Esc closes.", "Tools work from the satchel by themselves:", "the best pick, axe or sword is used."];
    tips.forEach((t, k) => p.fillText(t, gx, wy + 30 + ss * 3 + 26 + k * 14));
    // what can be made: by hand, and at a workbench or kiln within reach
    const px = gx + gridW + 20, st = g.craftStations(), rows = CM.CC.RECIPES.map((r) => ({ r, can: g.craftCan(r, st), here: !r.at || st[r.at] })).sort((a, b) => (b.can - a.can) || (b.here - a.here));
    p.font = "bold 13px Tahoma, sans-serif"; p.fillStyle = "#F0E0B0"; p.fillText(`Make${st.bench ? " - workbench" : ""}${st.kiln ? " - kiln" : ""}`, px, wy + 22);
    const rh = 22, top = wy + 32, fit = Math.max(3, Math.floor((wh - 48) / rh)); this.ccScroll = Math.max(0, Math.min(this.ccScroll || 0, rows.length - fit));
    rows.slice(this.ccScroll, this.ccScroll + fit).forEach(({ r, can, here }, k) => {
      const y = top + k * rh; p.fillStyle = can ? "rgba(120,180,90,0.22)" : "rgba(0,0,0,0.25)"; p.fillRect(px, y, panelW, rh - 2);
      const [tx, ty] = this.ccTileOf(r.makes[0]); p.globalAlpha = can ? 1 : 0.45; p.drawImage(atlas, tx, ty, 16, 16, px + 3, y + 2, 16, 16);
      p.font = "bold 11px Tahoma, sans-serif"; p.fillStyle = can ? "#FFF" : "#A09888"; p.fillText(`${r.makes[1] > 1 ? `${r.makes[1]} ` : ""}${CM.CC.NAMES[r.makes[0]]}${r.makes[1] > 1 && !/s$/.test(CM.CC.NAMES[r.makes[0]]) ? "s" : ""}`, px + 24, y + 14);
      p.font = "10px Tahoma, sans-serif"; p.textAlign = "right"; p.fillStyle = here ? (can ? "#D8F0C0" : "#C8B8A0") : "#E08060";
      p.fillText(here ? Object.entries(r.needs).map(([b, n]) => `${n} ${CM.CC.NAMES[b].toLowerCase().replace(" ore chunk", "")}`).join(", ") : `at a ${r.at === "bench" ? "workbench" : "kiln"}`, px + panelW - 4, y + 14);
      p.textAlign = "left"; p.globalAlpha = 1; this.ccRects.push({ kind: "recipe", id: r.id, x: px, y, w: panelW, h: rh - 2 });
    });
    if (rows.length > fit) { p.font = "10px Tahoma, sans-serif"; p.fillStyle = "#C8B8A0"; p.fillText(`the wheel scrolls (${this.ccScroll + 1}-${Math.min(rows.length, this.ccScroll + fit)} of ${rows.length})`, px, wy + wh - 6); }
  },
  ccTileOf(b) { if (CM.CC.isItem(b)) { const t = CM.CC.TILE[CM.CC.ITEM_TILE[b]]; return [(t % CM.CC.ATLAS) * 16, Math.floor(t / CM.CC.ATLAS) * 16]; } const face = CM.CC.FACES[b][b === CM.CC.B.GRASS || b === CM.CC.B.LOG ? 1 : 0], t = CM.CC.TILE[face]; return [(t % CM.CC.ATLAS) * 16, Math.floor(t / CM.CC.ATLAS) * 16]; },
  ccDrawSlot(p, atlas, s, x, y, size, lit, picked) {
    p.fillStyle = lit ? "rgba(255,255,255,0.18)" : "rgba(0,0,0,0.35)"; p.fillRect(x, y, size, size);
    if (s) { const [tx, ty] = this.ccTileOf(s.b), m = Math.round(size * 0.14); p.globalAlpha = picked ? 0.4 : 1; p.drawImage(atlas, tx, ty, 16, 16, x + m, y + m, size - 2 * m, size - 2 * m); p.globalAlpha = 1;
      if (s.d !== undefined && CM.CC.TOOLS[s.b]) { const f = s.d / CM.CC.TOOLS[s.b].uses; p.fillStyle = "#202020"; p.fillRect(x + 4, y + size - 6, size - 8, 3); p.fillStyle = f > 0.5 ? "#60D040" : f > 0.2 ? "#E0C040" : "#E04030"; p.fillRect(x + 4, y + size - 6, (size - 8) * f, 3); }
      if (s.n > 1) { p.font = "bold 12px Tahoma, sans-serif"; p.textAlign = "right"; p.fillStyle = "#000"; p.fillText(String(s.n), x + size - 3, y + size - 3); p.fillStyle = "#FFF"; p.fillText(String(s.n), x + size - 4, y + size - 4); p.textAlign = "left"; } }
    p.strokeStyle = lit ? "#FFF" : picked ? "#F0D060" : "#808080"; p.lineWidth = lit || picked ? 3 : 1; p.strokeRect(x + 1, y + 1, size - 2, size - 2);
  },
  // the atlas, painted in code as world.py paints it (and two of our own: the basalt and the gate's light)
  ccAtlas() {
    if (this.ccAtlasC) return this.ccAtlasC;
    const c = document.createElement("canvas"); c.width = 16 * CM.CC.ATLAS; c.height = 16 * CM.CC.ROWS; const p = c.getContext("2d"), R = new CM.Random(7), u = (a, b) => a + (b - a) * R.next();
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
    for (const [ore, col] of [["copper", "#D07A40"], ["iron", "#C8A890"], ["silver", "#E8ECF8"], ["gold", "#F0C838"], ["stariron", "#7A9AF0"], ["charstone", "#1A1A1A"]]) {   // (v12.1: ore in the stone)
      [x, y] = at(ore === "charstone" ? "charstone" : `ore_${ore}`); noisy(x, y, "#7F7F7F", 18); const r2 = new CM.Random(ore.length * 31 + 5);
      for (let k = 0; k < 6; k++) { const ox = r2.int(1, 12), oy = r2.int(1, 12); p.fillStyle = col; p.fillRect(x + ox, y + oy, 3, 2); p.fillRect(x + ox + 1, y + oy - 1, 1, 4); p.fillStyle = "rgba(255,255,255,0.35)"; if (ore !== "charstone") p.fillRect(x + ox, y + oy, 1, 1); }
      if (ore === "stariron") { p.fillStyle = "#FFFFFF"; for (const [sx, sy] of [[4, 4], [11, 9], [7, 13]]) p.fillRect(x + sx, y + sy, 1, 1); }
    }
    for (const [it, col, dark] of [["copper", "#D07A40", "#7A3A18"], ["iron", "#B8A090", "#5A4A40"], ["silver", "#E8ECF8", "#8A90A0"], ["gold", "#F0C838", "#9A7010"], ["stariron", "#8AA4F8", "#2A3A80"], ["charcoal", "#303030", "#101010"]]) {   // (the things in the satchel)
      [x, y] = at(`item_${it}`); p.fillStyle = dark; p.beginPath(); p.moveTo(x + 3, y + 10); p.lineTo(x + 5, y + 4); p.lineTo(x + 10, y + 2); p.lineTo(x + 14, y + 6); p.lineTo(x + 13, y + 12); p.lineTo(x + 7, y + 14); p.closePath(); p.fill();
      p.fillStyle = col; p.beginPath(); p.moveTo(x + 5, y + 9); p.lineTo(x + 6, y + 5); p.lineTo(x + 10, y + 4); p.lineTo(x + 12, y + 7); p.lineTo(x + 11, y + 11); p.lineTo(x + 7, y + 12); p.closePath(); p.fill();
      p.fillStyle = "rgba(255,255,255,0.55)"; p.fillRect(x + 7, y + 5, 2, 1); p.fillRect(x + 6, y + 6, 1, 1);
    }
    // (v12.2) the workbench, the kiln, the torch, the chest, the ladder, and the made things' icons
    [x, y] = at("workbench_top"); noisy(x, y, "#B08D57", 10); p.strokeStyle = "#6A4E28"; p.strokeRect(x + 0.5, y + 0.5, 15, 15); p.fillStyle = "#6A4E28"; p.fillRect(x + 8, y, 1, 16); p.fillRect(x, y + 8, 16, 1); p.fillStyle = "#909098"; p.fillRect(x + 2, y + 3, 4, 2); p.fillRect(x + 10, y + 10, 3, 3);
    [x, y] = at("workbench_side"); noisy(x, y, "#9A7848", 10); p.fillStyle = "#5A4020"; p.fillRect(x, y, 16, 3); p.fillRect(x + 1, y + 3, 3, 13); p.fillRect(x + 12, y + 3, 3, 13); p.fillStyle = "#808088"; p.fillRect(x + 6, y + 6, 4, 2);
    [x, y] = at("kiln_side"); noisy(x, y, "#7A7470", 22); p.fillStyle = "#1A1210"; p.fillRect(x + 4, y + 7, 8, 7); p.fillStyle = "#E07020"; p.fillRect(x + 5, y + 11, 6, 3); p.fillStyle = "#F0C040"; p.fillRect(x + 7, y + 12, 2, 2);
    [x, y] = at("kiln_top"); noisy(x, y, "#7A7470", 22); p.fillStyle = "#201814"; p.fillRect(x + 5, y + 5, 6, 6);
    [x, y] = at("torch"); p.clearRect(x, y, 16, 16); p.fillStyle = "#6B4A26"; p.fillRect(x + 7, y + 5, 2, 11); p.fillStyle = "#F0C040"; p.fillRect(x + 7, y + 2, 2, 3); p.fillStyle = "#E06020"; p.fillRect(x + 7, y + 4, 2, 1);
    [x, y] = at("chest_side"); noisy(x, y, "#9A6A34", 10); p.fillStyle = "#5A3A18"; p.fillRect(x, y, 16, 1); p.fillRect(x, y + 15, 16, 1); p.fillRect(x, y + 6, 16, 1); p.fillStyle = "#C8A040"; p.fillRect(x + 7, y + 5, 2, 4);
    [x, y] = at("chest_top"); noisy(x, y, "#9A6A34", 10); p.fillStyle = "#5A3A18"; p.strokeStyle = "#5A3A18"; p.strokeRect(x + 0.5, y + 0.5, 15, 15); p.fillStyle = "#C8A040"; p.fillRect(x + 7, y, 2, 16);
    [x, y] = at("ladder"); p.clearRect(x, y, 16, 16); p.fillStyle = "#7A5A30"; p.fillRect(x + 2, y, 2, 16); p.fillRect(x + 12, y, 2, 16); for (const ry of [2, 6, 10, 14]) p.fillRect(x + 2, y + ry, 12, 2);
    [x, y] = at("item_pole"); p.clearRect(x, y, 16, 16); p.strokeStyle = "#7A5A30"; p.lineWidth = 2; p.beginPath(); p.moveTo(x + 3, y + 13); p.lineTo(x + 13, y + 3); p.stroke(); p.lineWidth = 1;
    for (const [m, col, dark] of [["copper", "#D07A40", "#7A3A18"], ["iron", "#B8B0A8", "#5A5450"], ["silver", "#E8ECF8", "#8A90A0"], ["gold", "#F0C838", "#9A7010"], ["stariron", "#8AA4F8", "#2A3A80"]]) {
      [x, y] = at(`bar_${m}`); p.clearRect(x, y, 16, 16); p.fillStyle = dark; p.beginPath(); p.moveTo(x + 2, y + 12); p.lineTo(x + 5, y + 6); p.lineTo(x + 14, y + 6); p.lineTo(x + 14, y + 10); p.lineTo(x + 11, y + 13); p.closePath(); p.fill(); p.fillStyle = col; p.beginPath(); p.moveTo(x + 2, y + 12); p.lineTo(x + 5, y + 6); p.lineTo(x + 11, y + 6); p.lineTo(x + 11, y + 12); p.closePath(); p.fill(); p.fillStyle = "rgba(255,255,255,0.5)"; p.fillRect(x + 5, y + 7, 5, 1);
    }
    for (const [tier, col] of [["stone", "#8A8A8A"], ["copper", "#D07A40"], ["iron", "#D0D0D8"]]) {
      [x, y] = at(`pick_${tier}`); p.clearRect(x, y, 16, 16); p.strokeStyle = "#7A5A30"; p.lineWidth = 2; p.beginPath(); p.moveTo(x + 4, y + 14); p.lineTo(x + 11, y + 5); p.stroke(); p.strokeStyle = col; p.lineWidth = 2; p.beginPath(); p.moveTo(x + 4, y + 3); p.quadraticCurveTo(x + 11, y + 2, x + 14, y + 9); p.stroke(); p.lineWidth = 1;
      [x, y] = at(`axe_${tier}`); p.clearRect(x, y, 16, 16); p.strokeStyle = "#7A5A30"; p.lineWidth = 2; p.beginPath(); p.moveTo(x + 4, y + 14); p.lineTo(x + 11, y + 4); p.stroke(); p.lineWidth = 1; p.fillStyle = col; p.beginPath(); p.moveTo(x + 9, y + 2); p.lineTo(x + 14, y + 4); p.lineTo(x + 13, y + 9); p.lineTo(x + 10, y + 6); p.closePath(); p.fill();
      [x, y] = at(`sword_${tier}`); p.clearRect(x, y, 16, 16); p.strokeStyle = col; p.lineWidth = 2; p.beginPath(); p.moveTo(x + 6, y + 10); p.lineTo(x + 14, y + 2); p.stroke(); p.strokeStyle = "#7A5A30"; p.beginPath(); p.moveTo(x + 2, y + 14); p.lineTo(x + 6, y + 10); p.stroke(); p.strokeStyle = "#C8A040"; p.beginPath(); p.moveTo(x + 4, y + 8); p.lineTo(x + 8, y + 12); p.stroke(); p.lineWidth = 1;
    }
    // (v12.5) gems in the rock, the old chests, the lairs, and the gems' icons
    for (const [gname, col, hi] of [["ruby", "#D02838", "#FF8090"], ["sapphire", "#2850D0", "#90B0FF"], ["sunstone", "#E89820", "#FFE080"], ["diamond", "#C8F0FF", "#FFFFFF"]]) {
      [x, y] = at(`gem_${gname}`); noisy(x, y, "#5A5A62", 18); const r2 = new CM.Random(gname.length * 7 + 1);
      for (let k = 0; k < 4; k++) { const ox = r2.int(2, 11), oy = r2.int(2, 11); p.fillStyle = col; p.beginPath(); p.moveTo(x + ox + 1.5, y + oy); p.lineTo(x + ox + 3, y + oy + 2); p.lineTo(x + ox + 1.5, y + oy + 4); p.lineTo(x + ox, y + oy + 2); p.closePath(); p.fill(); p.fillStyle = hi; p.fillRect(x + ox + 1, y + oy + 1, 1, 1); }
      [x, y] = at(`item_${gname}`); p.clearRect(x, y, 16, 16); p.fillStyle = col; p.beginPath(); p.moveTo(x + 8, y + 2); p.lineTo(x + 14, y + 7); p.lineTo(x + 8, y + 14); p.lineTo(x + 2, y + 7); p.closePath(); p.fill(); p.fillStyle = hi; p.beginPath(); p.moveTo(x + 8, y + 3); p.lineTo(x + 11, y + 6); p.lineTo(x + 8, y + 8); p.lineTo(x + 5, y + 6); p.closePath(); p.fill();
    }
    [x, y] = at("treasure_side"); noisy(x, y, "#5A3A20", 10); p.fillStyle = "#3A3A40"; p.fillRect(x, y, 16, 2); p.fillRect(x, y + 14, 16, 2); p.fillRect(x, y + 7, 16, 2); p.fillRect(x + 2, y, 2, 16); p.fillRect(x + 12, y, 2, 16); p.fillStyle = "#E0B040"; p.fillRect(x + 7, y + 6, 2, 4);
    [x, y] = at("treasure_top"); noisy(x, y, "#5A3A20", 10); p.fillStyle = "#3A3A40"; p.fillRect(x, y + 3, 16, 2); p.fillRect(x, y + 11, 16, 2); p.fillStyle = "#E0B040"; p.fillRect(x + 7, y, 2, 16);
    [x, y] = at("lair"); noisy(x, y, "#241C22", 10); p.strokeStyle = "#C03020"; p.beginPath(); p.moveTo(x + 2, y + 3); p.lineTo(x + 7, y + 8); p.lineTo(x + 5, y + 13); p.moveTo(x + 7, y + 8); p.lineTo(x + 13, y + 6); p.moveTo(x + 10, y + 12); p.lineTo(x + 13, y + 14); p.stroke(); p.fillStyle = "#FF6030"; p.fillRect(x + 7, y + 7, 2, 2);
    // (v12.6) the bedroll, the door, the signpost's board
    [x, y] = at("bedroll"); noisy(x, y, "#4A7A3A", 14); p.fillStyle = "#6A4A2A"; p.fillRect(x, y + 3, 16, 2); p.fillRect(x, y + 11, 16, 2); p.fillStyle = "#C8B080"; p.fillRect(x + 1, y + 6, 4, 4);
    [x, y] = at("door"); noisy(x, y, "#8A6436", 8); p.fillStyle = "#5A3E1E"; p.fillRect(x, y, 16, 1); p.fillRect(x, y + 15, 16, 1); p.fillRect(x, y, 1, 16); p.fillRect(x + 15, y, 1, 16); p.fillRect(x + 7, y, 2, 16); p.fillStyle = "#C8A040"; p.fillRect(x + 11, y + 8, 2, 2);
    [x, y] = at("sign"); noisy(x, y, "#B08D57", 8); p.fillStyle = "#5A3E1E"; for (const ly of [4, 7, 10]) p.fillRect(x + 3, y + ly, 10, 1);
    this.ccAtlasC = c; return c;
  },
  ccStart(world) {
    let c = this.$("#craftcanvas"); if (!c) { c = document.createElement("canvas"); c.id = "craftcanvas"; this.$("#view").appendChild(c); }
    const gl = this.ccGl = c.getContext("webgl", { antialias: false }) || c.getContext("experimental-webgl"); if (!gl) return false;
    const sh = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
    const prog = this.ccProg = gl.createProgram(); gl.attachShader(prog, sh(gl.VERTEX_SHADER, CC_VERT)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, CC_FRAG)); gl.bindAttribLocation(prog, 0, "pos"); gl.bindAttribLocation(prog, 1, "uv"); gl.bindAttribLocation(prog, 2, "shade"); gl.bindAttribLocation(prog, 3, "sky"); gl.linkProgram(prog);
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
    gl.bindBuffer(gl.ARRAY_BUFFER, ch.op); gl.bufferData(gl.ARRAY_BUFFER, op, gl.STATIC_DRAW); ch.nOp = op.length / 7;
    gl.bindBuffer(gl.ARRAY_BUFFER, ch.wa); gl.bufferData(gl.ARRAY_BUFFER, wa, gl.STATIC_DRAW); ch.nWa = wa.length / 7;
  },
  ccDirtyAt(x, z, r = 1) { const C = CM.CC.CHUNK; for (const [dx, dz] of [[0, 0], [r, 0], [-r, 0], [0, r], [0, -r], [r, r], [-r, r], [r, -r], [-r, -r]]) { const cx = Math.floor((x + dx) / C), cz = Math.floor((z + dz) / C); if (cx >= 0 && cz >= 0 && cx < CM.CC.CHUNKS && cz < CM.CC.CHUNKS) this.ccDirty.add(`${cx},${cz}`); } },
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
    const day = CM.CL.daylight(g), skyCol = this.ccSkyColour(g, day);
    gl.viewport(0, 0, c.width, c.height); gl.clearColor(skyCol[0], skyCol[1], skyCol[2], 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); gl.enable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE);
    const P = this.ccProg; gl.useProgram(P); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, this.ccTex);
    const U = (n) => gl.getUniformLocation(P, n);
    gl.uniform1i(U("atlas"), 0); gl.uniformMatrix4fv(U("mvp"), false, new Float32Array(this.ccMvp(w, c.width / c.height))); gl.uniform3fv(U("eye"), w.eye()); gl.uniform3fv(U("fog"), skyCol); gl.uniform1f(U("daylight"), day); gl.uniform1f(U("fogStart"), 40); gl.uniform1f(U("fogEnd"), 90); gl.uniform1f(U("lines"), 0); gl.uniform1f(U("time"), now / 1000); gl.uniform1f(U("lamp"), g.craftLight());
    const draw = (buf, n, mode = gl.TRIANGLES) => { if (!n) return; gl.bindBuffer(gl.ARRAY_BUFFER, buf); for (const a of [0, 1, 2, 3]) gl.enableVertexAttribArray(a); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 28, 0); gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 28, 12); gl.vertexAttribPointer(2, 1, gl.FLOAT, false, 28, 20); gl.vertexAttribPointer(3, 1, gl.FLOAT, false, 28, 24); gl.drawArrays(mode, 0, n); };
    for (const ch of this.ccChunks.values()) draw(ch.op, ch.nOp);
    gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false);
    for (const ch of this.ccChunks.values()) draw(ch.wa, ch.nWa);
    gl.depthMask(true);
    const hit = cr.target && cr.target[0];
    if (hit) { const [x, y, z] = hit, e = 0.003, C = [[x - e, y - e, z - e], [x + 1 + e, y - e, z - e], [x + 1 + e, y - e, z + 1 + e], [x - e, y - e, z + 1 + e], [x - e, y + 1 + e, z - e], [x + 1 + e, y + 1 + e, z - e], [x + 1 + e, y + 1 + e, z + 1 + e], [x - e, y + 1 + e, z + 1 + e]], out = [];
      for (const [a, b] of [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]]) out.push(...C[a], 0, 0, 1, 255, ...C[b], 0, 0, 1, 255);
      gl.uniform1f(U("lines"), 1); gl.bindBuffer(gl.ARRAY_BUFFER, this.ccLine); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(out), gl.DYNAMIC_DRAW); draw(this.ccLine, 24, gl.LINES); }
    if (hit && cr.dig && cr.dig.key === hit.join(",") && cr.dig.need < Infinity) {          // (the crack, growing with the dig)
      const [x, y, z] = hit, e2 = 0.004, out = [];
      for (const [, , corners] of CM.CC.FACE_DEFS) for (const [dx, dy, dz, u, v] of corners) out.push(x + (dx ? 1 + e2 : -e2), y + (dy ? 1 + e2 : -e2), z + (dz ? 1 + e2 : -e2), u, v, 1, 255);
      if (!this.ccCrackBuf) this.ccCrackBuf = gl.createBuffer(); gl.uniform1f(U("lines"), 2 + Math.min(1, cr.dig.t / cr.dig.need) * 1.45); gl.bindBuffer(gl.ARRAY_BUFFER, this.ccCrackBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(out), gl.DYNAMIC_DRAW); draw(this.ccCrackBuf, out.length / 7); }
    if (cr.bundles.length) {                                                   // (the bundles: small glowing blocks, bobbing)
      const [tx, ty] = [(CM.CC.TILE.gate % CM.CC.ATLAS) / CM.CC.ATLAS, Math.floor(CM.CC.TILE.gate / CM.CC.ATLAS) / CM.CC.ROWS], out = [], s2 = 0.6;
      for (const B of cr.bundles) { const bob = Math.sin(now / 400 + B.x) * 0.15 + 0.45; for (const [nrm, sh, corners] of CM.CC.FACE_DEFS) for (const [dx, dy, dz, u, v] of corners) out.push(B.x - s2 / 2 + dx * s2, B.y + bob + dy * s2, B.z - s2 / 2 + dz * s2, tx + (u / CM.CC.ATLAS), ty + v / CM.CC.ROWS, 2.5 + sh, 255); }
      if (!this.ccBundleBuf) this.ccBundleBuf = gl.createBuffer(); gl.uniform1f(U("lines"), 0); gl.bindBuffer(gl.ARRAY_BUFFER, this.ccBundleBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(out), gl.DYNAMIC_DRAW); draw(this.ccBundleBuf, out.length / 7); }
    this.ccDrawLife(gl, U, draw, cr, now, w);
    gl.disable(gl.BLEND);
    this.ccHud(cr, now);
  },
  // (v12.3) the sky's colour by the hour: blue by day, gold at dawn and dusk, near black at night
  ccSkyColour(g, day) { const h = CM.hourOf(g), dusk = (h > 16 && h < 22) || (h > 4 && h < 8), warm = dusk ? Math.max(0, 1 - Math.abs(day - 0.5) * 2) : 0, base = [0.03 + 0.50 * day, 0.04 + 0.67 * day, 0.10 + 0.86 * day]; return [base[0] + warm * 0.45, base[1] + warm * 0.15, base[2] - warm * 0.2]; },
  // the creatures' pictures, the game's own monster drawings, on a sheet the GL draws from (and the sun and the moon)
  ccSprites() {
    if (this.ccSpr) return this.ccSpr; const kinds = [...new Set([...CM.CL.WILD, ...CM.CL.TOP, ...CM.CL.CAVE, ...CM.CL.DEEP, ...(CM.CL.EXTRA || [])])], cell = 128, cols = 8, rows = Math.ceil((kinds.length + 2) / cols);
    const c = document.createElement("canvas"); c.width = cell * cols; c.height = cell * rows; const p = c.getContext("2d"), at = {};
    kinds.forEach((k, i) => { const x = (i % cols) * cell, y = Math.floor(i / cols) * cell; try { const pic = CM.art.monster(CM.monsterKind(k) || (CM.CL.ART && CM.CL.ART[k])); p.drawImage(pic, x, y, cell, cell); } catch (e) { p.fillStyle = "#808080"; p.fillRect(x + 32, y + 32, 64, 96); } at[k] = i; });
    const sun = kinds.length, moon = kinds.length + 1;
    { const x = (sun % cols) * cell + 64, y = Math.floor(sun / cols) * cell + 64, gr = p.createRadialGradient(x, y, 10, x, y, 62); gr.addColorStop(0, "rgba(255,250,220,1)"); gr.addColorStop(0.45, "rgba(255,230,140,1)"); gr.addColorStop(0.55, "rgba(255,210,120,0.5)"); gr.addColorStop(1, "rgba(255,200,100,0)"); p.fillStyle = gr; p.fillRect(x - 64, y - 64, 128, 128); }
    { const x = (moon % cols) * cell + 64, y = Math.floor(moon / cols) * cell + 64; p.fillStyle = "#E8ECF4"; p.beginPath(); p.arc(x, y, 30, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C0C6D4"; for (const [dx, dy, r] of [[-10, -6, 7], [9, 8, 5], [4, -14, 4], [-6, 14, 4]]) { p.beginPath(); p.arc(x + dx, y + dy, r, 0, Math.PI * 2); p.fill(); } }
    at.sun = sun; at.moon = moon;
    const gl = this.ccGl, tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, c); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    this.ccSpr = { tex, at, cols, rows, canvas: c }; return this.ccSpr;
  },
  ccDrawLife(gl, U, draw, cr, now, w) {
    const g = this.game, L = cr.life, S = this.ccSprites(), yr = (w.yaw * Math.PI) / 180, right = [Math.cos(yr), 0, -Math.sin(yr)], out = [];
    const quad = (cx, by, cz, wd, ht, cell, shade, light, flip) => { const u0 = (cell % S.cols) / S.cols, v0 = Math.floor(cell / S.cols) / S.rows, du = 1 / S.cols, dv = 1 / S.rows, hx = right[0] * wd / 2, hz = right[2] * wd / 2;
      const P = [[cx - hx, by, cz - hz, flip ? u0 + du : u0, v0 + dv], [cx + hx, by, cz + hz, flip ? u0 : u0 + du, v0 + dv], [cx + hx, by + ht, cz + hz, flip ? u0 : u0 + du, v0], [cx - hx, by + ht, cz - hz, flip ? u0 + du : u0, v0]];
      for (const i of [0, 1, 2, 0, 2, 3]) out.push(P[i][0], P[i][1], P[i][2], P[i][3], P[i][4], shade, light); };
    // the sun and the moon, far off along the hour's arc
    const h = CM.hourOf(g), a = ((h - 6) / 12) * Math.PI, e = w.eye();
    for (const [cell, ang] of [[S.at.sun, a], [S.at.moon, a + Math.PI]]) { const dir = [Math.cos(ang) * 0.9, Math.sin(ang), 0.35], n = Math.hypot(...dir); if (dir[1] < -0.1) continue; const D = 150; const cx = e[0] + (dir[0] / n) * D, cy = e[1] + (dir[1] / n) * D, cz = e[2] + (dir[2] / n) * D; quad(cx, cy - 9, cz, 18, 18, cell, 4.5, 255); }
    if (L) for (const o of L.mobs) {
      const fell = o.fellAt !== null ? Math.min(1, (L.t - o.fellAt) / 0.6) : 0, hitNow = L.t - o.hitAt < 0.15, wd = Math.max(o.r * 2.6, o.h * 0.9), ht = o.h * (1 - fell * 0.85);
      const lx = Math.floor(o.w.pos[0]), ly = Math.floor(o.w.pos[1] + 0.5), lz = Math.floor(o.w.pos[2]), W = cr.world, light = CM.CC.packLight(W.skyAt(lx, ly, lz), W.torchAt(lx, ly, lz));
      const facing = Math.sin(((o.w.yaw - w.yaw) * Math.PI) / 180) > 0;
      quad(o.w.pos[0], o.w.pos[1] - 0.02, o.w.pos[2], wd, Math.max(0.1, ht), S.at[o.kind] || 0, hitNow ? 4.8 : 1.0, light, facing);
    }
    if (out.length) { if (!this.ccLifeBuf) this.ccLifeBuf = gl.createBuffer(); gl.bindTexture(gl.TEXTURE_2D, S.tex); gl.uniform1f(U("lines"), 0); gl.bindBuffer(gl.ARRAY_BUFFER, this.ccLifeBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(out), gl.DYNAMIC_DRAW); draw(this.ccLifeBuf, out.length / 7); gl.bindTexture(gl.TEXTURE_2D, this.ccTex); }
    // the shots: little glowing blocks (gold bolts, brown arrows)
    if (L && L.shots.length) { const [tx, ty] = [(CM.CC.TILE.gate % CM.CC.ATLAS) / CM.CC.ATLAS, Math.floor(CM.CC.TILE.gate / CM.CC.ATLAS) / CM.CC.ROWS], o2 = [];
      for (const s of L.shots) { const s2 = s.kind === "bolt" ? 0.22 : 0.12; for (const [, sh, corners] of CM.CC.FACE_DEFS) for (const [dx, dy, dz, u, v] of corners) o2.push(s.x - s2 / 2 + dx * s2, s.y - s2 / 2 + dy * s2, s.z - s2 / 2 + dz * s2, tx + u / CM.CC.ATLAS, ty + v / CM.CC.ROWS, s.kind === "bolt" ? 3.5 : 1.0 + sh * 0.3, 255); }
      if (!this.ccShotBuf) this.ccShotBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, this.ccShotBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(o2), gl.DYNAMIC_DRAW); draw(this.ccShotBuf, o2.length / 7); }
  },
  // (v12.5) the compass across the top: north, east, south and west, the gate, and the vault once the map is whole
  ccCompass(p, cr, W, H) {
    const g = this.game, w = cr.walker, cx = W / 2, top = H - 136, half = Math.min(170, W / 2 - 40); if (half < 60 || this.ccSatchelOpen) return;
    p.fillStyle = "rgba(0,0,0,0.45)"; p.fillRect(cx - half - 6, top, half * 2 + 12, 22); p.strokeStyle = "rgba(200,160,64,0.8)"; p.lineWidth = 1; p.strokeRect(cx - half - 6 + 0.5, top + 0.5, half * 2 + 11, 21);
    const at = (a) => { let rel = a - w.yaw; rel = ((rel + 540) % 360) - 180; return Math.abs(rel) > 90 ? null : cx - (rel / 90) * half; };
    p.font = "bold 11px Tahoma, sans-serif"; p.textAlign = "center";
    for (const [a, t] of [[0, "N"], [-90, "E"], [180, "S"], [90, "W"], [-45, "NE"], [-135, "SE"], [135, "SW"], [45, "NW"]]) { const x = at(a); if (x !== null) { p.fillStyle = t.length > 1 ? "rgba(255,255,255,0.45)" : "#FFF"; p.fillText(t, x, top + 15); } }
    const mark = (tx, tz, col, label) => { const a = (Math.atan2(-(tx - w.pos[0]), -(tz - w.pos[2])) * 180) / Math.PI, x = at(a); const d = Math.round(Math.hypot(tx - w.pos[0], tz - w.pos[2])); if (x === null) return; p.fillStyle = col; p.beginPath(); p.moveTo(x, top + 22); p.lineTo(x - 5, top + 30); p.lineTo(x + 5, top + 30); p.closePath(); p.fill(); p.font = "10px Tahoma, sans-serif"; p.fillText(`${label} ${d}`, x, top + 41); };
    const gt = cr.world.gate; mark(gt.x + 2, gt.z, "#B070FF", "gate");
    const v = g.craftMap && g.craftMap(); if (v) mark(v.x + 0.5, v.z + 0.5, "#F0C040", "the vault");
    for (const s of (g.craftStore().signs || [])) mark(s.x + 0.5, s.z + 0.5, "#E0E0E0", s.name);
    p.textAlign = "left";
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
    const hero = cr.hero, px = 10, py = 10, g2 = this.game; if (!this.ccPor || this.ccPor.cls !== hero.cls) { let c = null; try { c = CM.art.portraitDrawn(hero.cls, 56); } catch (er) { /* */ } this.ccPor = { cls: hero.cls, c }; }
    p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(px - 4, py - 4, 236, g2.craftLoad() ? 80 : 64); if (this.ccPor.c) p.drawImage(this.ccPor.c, px, py, 56, 56);
    const bar = (y, v, m, col, label) => { p.fillStyle = "#202020"; p.fillRect(px + 62, y, 160, 12); p.fillStyle = col; p.fillRect(px + 62, y, 160 * Math.max(0, Math.min(1, m ? v / m : 0)), 12); p.font = "10px Tahoma, sans-serif"; p.fillStyle = "#FFF"; p.textAlign = "left"; p.fillText(label, px + 66, y + 10); };
    p.font = "bold 12px Tahoma, sans-serif"; p.fillStyle = "#FFF"; p.textAlign = "left"; p.fillText(`${hero.name} the ${hero.cls}`, px + 62, py + 10);
    bar(py + 16, hero.hp, hero.max, hero.hp < hero.max * 0.25 ? "#E04030" : "#C83030", `${Math.max(0, hero.hp)} / ${hero.max}`);
    if (hero.maxmp) bar(py + 31, hero.mp, hero.maxmp, "#3F7DE0", `${hero.mp} / ${hero.maxmp}`);
    const load = g2.craftLoad(), cap = g2.craftCap(); if (load) { p.font = "11px Tahoma, sans-serif"; p.fillStyle = cr.walker.heavy ? "#FF9060" : "#E8D8B0"; p.fillText(`Ore and charcoal: ${load} of ${cap}${cr.walker.heavy ? " - heavy!" : ""}`, px + 62, py + 70); }
    let clock = ""; try { const m = CM.minuteOf(this.game), hh = Math.floor(m / 60), mm = m % 60; clock = `${hh}:${mm < 10 ? "0" : ""}${mm}, ${CM.hourWord(CM.hourOf(this.game))}`; } catch (er) { /* */ }
    const L = cr.life; p.font = "11px Tahoma, sans-serif"; p.fillText(`${clock}  -  level ${hero.level}${L && (L.gold || L.loot.length) ? `  -  ${L.gold} gold${L.loot.length ? `, ${L.loot.length} found` : ""}` : ""}`, px + 62, py + 56);
    p.font = "11px Tahoma, sans-serif"; p.fillStyle = "rgba(255,255,255,0.9)"; p.textAlign = "right"; p.fillText(`XYZ ${w.pos[0].toFixed(0)} / ${w.pos[1].toFixed(0)} / ${w.pos[2].toFixed(0)}   broken ${cr.broken || 0}, placed ${cr.placed || 0}${cr.bundles.length ? `   bundles on the island: ${cr.bundles.length}` : ""}`, W - 8, 16);
    p.fillText("WASD walk - mouse look - Space jump - Shift sprint", W - 8, 32); p.fillText("hold left: break (or strike) - F: shoot / strike - right: place / use - I: satchel", W - 8, 46); p.fillText(`Q drink (${this.game.potionCount ? this.game.potionCount() : 0} potions) - G eat - the gate's light: home`, W - 8, 60); p.textAlign = "left";
    if (this.ccSatchelOpen) { this.ccWindow(p, atlas, cr, W, H);
    } else if (document.pointerLockElement !== this.$("#craftcanvas")) { p.font = "bold 15px Tahoma, sans-serif"; p.fillStyle = "#FFF"; p.textAlign = "center"; p.fillText("Click to play", W / 2, H / 2 + 34); p.textAlign = "left"; }
    this.ccCompass(p, cr, W, H);
    const recent = (cr.says || []).filter(([t]) => now - t < 4000).slice(-3);
    recent.forEach(([t, msg], k) => { p.font = "bold 14px Tahoma, sans-serif"; p.textAlign = "center"; p.fillStyle = "rgba(0,0,0,0.6)"; p.fillText(msg, W / 2 + 1, H * 0.22 + k * 20 + 1); p.fillStyle = `rgba(255,240,200,${Math.min(1, (4000 - (now - t)) / 800)})`; p.fillText(msg, W / 2, H * 0.22 + k * 20); p.textAlign = "left"; });
  },
});
