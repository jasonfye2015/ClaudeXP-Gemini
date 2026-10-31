"use strict";
// Claudeita's cave, the window's side (the thirteenth update): the mouth's dialog (who goes in, and which wands from the
// rack), and the cave itself drawn on a canvas laid over the view - the world's own pixels, the hero, the creatures, the
// spells in flight, the dark of the deep lit around the hero, the HUD, and Tab's wand editor - as Claudeita draws them.
// The run is 64i-claudeita.js; the rules for going in and coming out 61g-cavemouth.js; the frame loop 80-main.js.
const CAVE_KIND_COLOUR = { proj: "#4A90E2", mod: "#4FC36A", multi: "#F0A030" };
Object.assign(CM.UI.prototype, {
  // ---- the mouth: who goes in ----
  openClaudeita() {
    const g = this.game, K = g.caveStore(), box = this.$("#claudeita-who"), note = this.$("#claudeita-note"), picks = this.cavePicks = (this.cavePicks || []).filter((k) => K.wands[k]);
    const rack = K.wands.length ? K.wands.map((w, k) => `<label class="cwand"><input type="checkbox" data-rack="${k}" ${picks.includes(k) ? "checked" : ""}><span class="wdot" style="background:${this.esc(w.colour)}"></span><b>${this.esc(w.name)}</b> <small>${w.slots.map((s) => (s ? this.esc(s) : "-")).join(", ")} - mana ${w.mana_max}</small></label>`).join("") : `<small>The rack is empty. Wands carried out of a won run are kept here.</small>`;
    box.innerHTML = `<div class="list-title">Who goes in</div>${g.caveChoices().map((c) => `<div class="recruit" style="grid-template-columns: 1fr auto"><div><b>${this.esc(c.name)}</b> the ${this.esc(c.cls)}${c.why ? `<br><small>${this.esc(c.why)}</small>` : ""}</div><div class="hire"><button data-cave-hero="${c.i}" ${c.why ? "disabled" : ""}>Go in</button></div></div>`).join("")}
      <div class="list-title">The rack (take up to ${CM.CAVE_RACK.carry} besides the Apprentice's Wand and the Miner's Rod)</div><div class="crack">${rack}</div>
      <p class="small">Runs ${K.runs}, won ${K.wins}, deepest ${K.deepest} m. Die and you wake here with a tenth of your health and nothing the cave gave but the experience; climb out by a sanctuary's rope, or undo the Unmaker, and the gold, the things and the wands are yours.</p>`;
    for (const c of box.querySelectorAll("[data-rack]")) c.addEventListener("change", () => { const k = Number(c.dataset.rack); this.cavePicks = c.checked ? [...new Set(this.cavePicks.concat(k))] : this.cavePicks.filter((n) => n !== k); if (this.cavePicks.length > CM.CAVE_RACK.carry) { this.cavePicks.shift(); this.openClaudeita(); } });
    for (const b of box.querySelectorAll("[data-cave-hero]")) b.addEventListener("click", () => { const why = g.enterClaudeita(Number(b.dataset.caveHero), this.cavePicks); note.textContent = why || ""; if (!why) { this.closeDialogs(); this.refresh(); } });
    note.textContent = "";
    this.openDialog("#dlg-claudeita");
  },
  // ---- the canvas ----
  caveCanvas() {
    let c = this.$("#cavecanvas");
    if (!c) { c = document.createElement("canvas"); c.id = "cavecanvas"; this.$("#view").appendChild(c); }
    const r = c.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1), w = Math.max(320, Math.round(r.width * dpr)), h = Math.max(200, Math.round(r.height * dpr));
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    return c;
  },
  caveStart() { this.caveEdit = false; this.cavePick = null; this.cavePaused = false; this.caveIcons = this.caveIcons || {}; this.caveCanvas(); },
  // the view's corner in cells: the camera, kept inside the world, with the shake
  caveOrigin(run, c) {
    const C = CM.CV, s = c.width / C.VIEW_W, vw = C.VIEW_W, vh = c.height / s;
    const cx = Math.max(vw / 2, Math.min(C.W - vw / 2, run.cam[0])), cy = Math.max(vh / 2, Math.min(C.H - vh / 2, run.cam[1]));
    const j = run.shake > 0.3 ? run.shake : 0, jx = j ? (Math.random() * 2 - 1) * j : 0, jy = j ? (Math.random() * 2 - 1) * j : 0;
    return { ox: cx - vw / 2 + jx * 0.3, oy: cy - vh / 2 + jy * 0.3, s, vw, vh };
  },
  caveAim(run) { const c = this.$("#cavecanvas"), m = this.caveMouse; if (!c || !m || !this.caveView) return null; const { ox, oy, s } = this.caveView; return [ox + m[0] / s, oy + m[1] / s]; },
  spellIcon(name, size) {
    const k = `${name}:${size}`; if (this.caveIcons[k]) return this.caveIcons[k];
    const S = CM.WAND_SPELLS[name], c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), border = CAVE_KIND_COLOUR[S.kind];
    p.fillStyle = "#1A1420"; p.strokeStyle = border; p.lineWidth = 1.5; p.beginPath(); p.roundRect ? p.roundRect(1, 1, size - 2, size - 2, 3) : p.rect(1, 1, size - 2, size - 2); p.fill(); p.stroke();
    if (S.kind === "proj") { const gr = p.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size * 0.35); gr.addColorStop(0, "#FFFFFF"); gr.addColorStop(0.35, S.colour || border); gr.addColorStop(1, S.colour || border); p.fillStyle = gr; p.beginPath(); p.arc(size / 2, size / 2, size * 0.28, 0, Math.PI * 2); p.fill(); }
    else { p.fillStyle = "#FFFFFF"; p.font = `bold ${Math.round(size * 0.36)}px Tahoma, sans-serif`; p.textAlign = "center"; p.textBaseline = "middle"; p.fillText(name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase(), size / 2, size / 2 + 1); }
    return (this.caveIcons[k] = c);
  },
  // a frame of the cave
  drawCave(run) {
    const c = this.caveCanvas(), p = c.getContext("2d"), C = CM.CV, V = this.caveView = this.caveOrigin(run, c), { ox, oy, s, vw, vh } = V, W = C.W, world = run.world;
    // the world's own pixels, the camera's part of them, into a small picture the size of the view in cells
    const ix = Math.max(0, Math.min(W - vw - 1, Math.floor(ox))), iy = Math.max(0, Math.floor(oy)), cw = vw + 1, ch = Math.min(C.H - iy, Math.ceil(vh) + 1);
    if (!this.caveBuf || this.caveBuf.width !== cw || this.caveBuf.height !== ch) { this.caveBuf = document.createElement("canvas"); this.caveBuf.width = cw; this.caveBuf.height = ch; this.caveImg = this.caveBuf.getContext("2d").createImageData(cw, ch); this.caveU32 = new Uint32Array(this.caveImg.data.buffer); }
    const U = this.caveU32; for (let r = 0; r < ch; r++) { const y = iy + r; if (y < world.made) U.set(world.pix.subarray(y * W + ix, y * W + ix + cw), r * cw); else U.fill(0xFF000000, r * cw, (r + 1) * cw); }
    this.caveBuf.getContext("2d").putImageData(this.caveImg, 0, 0);
    p.setTransform(1, 0, 0, 1, 0, 0); p.imageSmoothingEnabled = false; p.fillStyle = "#000"; p.fillRect(0, 0, c.width, c.height);
    p.drawImage(this.caveBuf, (ix - ox) * s, (iy - oy) * s, cw * s, ch * s);
    p.setTransform(s, 0, 0, s, -ox * s, -oy * s);
    for (const k of run.pickups) if (Math.abs(k.x - ox - vw / 2) < vw && Math.abs(k.y - oy - vh / 2) < vh) this.cavePickup(p, k);
    for (const e of run.enemies) if (e.x > ox - 30 && e.x < ox + vw + 30 && e.y > oy - 40 && e.y < oy + vh + 40) this.caveEnemy(p, e, run);
    this.caveHero(p, run);
    for (const sh of run.shots) {
      const r = sh.size * 2.2, gr = p.createRadialGradient(sh.x, sh.y, 0, sh.x, sh.y, r); gr.addColorStop(0, "rgba(255,255,255,0.9)"); gr.addColorStop(0.3, sh.colour); gr.addColorStop(1, "rgba(0,0,0,0)");
      p.fillStyle = gr; p.beginPath(); p.arc(sh.x, sh.y, r, 0, Math.PI * 2); p.fill(); p.fillStyle = sh.colour; p.beginPath(); p.arc(sh.x, sh.y, sh.size * 0.7, 0, Math.PI * 2); p.fill();
    }
    p.strokeStyle = "rgba(230,240,255,0.86)"; p.lineWidth = 1.2;
    for (const [[x0, y0], [x1, y1]] of run.bolts) { p.beginPath(); p.moveTo(x0, y0); for (let i = 1; i < 6; i++) p.lineTo(x0 + (x1 - x0) * (i / 6) + (Math.random() * 6 - 3), y0 + (y1 - y0) * (i / 6) + (Math.random() * 6 - 3)); p.lineTo(x1, y1); p.stroke(); }
    for (const [x, y, , , life, col] of run.particles) { p.globalAlpha = Math.min(1, life * 14 / 255); p.fillStyle = col; p.fillRect(x, y, 1, 1); }
    p.globalAlpha = 1; p.font = "bold 5px Tahoma, sans-serif"; p.textAlign = "left";
    for (const [x, y, text, , col] of run.texts) { p.fillStyle = col; p.fillText(text, x - 4, y); }
    p.setTransform(1, 0, 0, 1, 0, 0);
    // the dark of the deep, lit around the hero (darker the deeper)
    const pl = run.player, hx = (pl.x - ox) * s, hy = (pl.y - pl.h / 2 - oy) * s, depth = Math.max(0, Math.min(1, (pl.y - C.SURFACE) / 600)), R = c.width * (0.55 - depth * 0.18);
    const lg = p.createRadialGradient(hx, hy, 0, hx, hy, R); lg.addColorStop(0, "rgba(0,0,0,0)"); lg.addColorStop(0.55, `rgba(0,0,0,${(40 * depth) / 255})`); lg.addColorStop(1, `rgba(0,0,0,${(120 + 70 * depth) / 255})`);
    p.fillStyle = lg; p.fillRect(0, 0, c.width, c.height);
    this.caveHud(p, c, run);
    if (this.caveEdit) this.caveEditor(p, c, run);
    else if (run.over) this.caveOver(p, c, run);
    else if (this.cavePaused) this.caveCentre(p, c, "PAUSED", "Esc to carry on");
  },
  caveHero(p, run) {
    const pl = run.player; if (pl.hurt && Math.floor(pl.hurt / 3) % 2) return;
    const x = pl.x, y = pl.y;
    p.fillStyle = "#D97757"; p.beginPath(); p.moveTo(x - 3, y); p.lineTo(x + 3, y); p.lineTo(x + 2, y - 7); p.lineTo(x - 2, y - 7); p.closePath(); p.fill();   // (the robe, the face, the hat)
    p.fillStyle = "#F2C9A0"; p.beginPath(); p.arc(x, y - 8.5, 1.8, 0, Math.PI * 2); p.fill();
    p.fillStyle = "#4B2E83"; p.beginPath(); p.moveTo(x - 3, y - 9.5); p.lineTo(x + 3, y - 9.5); p.lineTo(x - pl.facing * 1.5, y - 14); p.closePath(); p.fill();
    const aim = this.caveAim(run), w = run.wand;
    if (aim && w) {
      const ang = Math.atan2(aim[1] - (y - 6.6), aim[0] - x), ex = x + Math.cos(ang) * 6, ey = y - 6.6 + Math.sin(ang) * 6;
      p.strokeStyle = w.colour; p.lineWidth = 1; p.beginPath(); p.moveTo(x, y - 6.6); p.lineTo(ex, ey); p.stroke();
      p.fillStyle = w.recharging ? "#55606A" : "#9EE6FF"; p.beginPath(); p.arc(ex, ey, 0.9, 0, Math.PI * 2); p.fill();
    }
  },
  caveEnemy(p, e, run) {
    const x = e.x, y = e.y;
    if (e.boss) { this.caveBoss(p, e, run); return; }
    p.globalAlpha = e.move === "ghost" ? 0.6 : 1; p.fillStyle = e.colour;
    if (e.kind === "bat") { const flap = Math.sin(e.t * 18) * 2; p.beginPath(); p.arc(x, y - 3, 2, 0, Math.PI * 2); p.fill(); p.beginPath(); p.moveTo(x - 1, y - 3); p.lineTo(x - 5, y - 4 - flap); p.lineTo(x - 2, y - 2); p.fill(); p.beginPath(); p.moveTo(x + 1, y - 3); p.lineTo(x + 5, y - 4 - flap); p.lineTo(x + 2, y - 2); p.fill(); }
    else if (e.kind === "worm") for (let i = 0; i < 4; i++) { p.beginPath(); p.arc(x - e.vx * i * 3, y - 3 - e.vy * i * 3, 3 - i * 0.4, 0, Math.PI * 2); p.fill(); }
    else { p.beginPath(); p.roundRect ? p.roundRect(x - e.w / 2, y - e.h, e.w, e.h, 2) : p.rect(x - e.w / 2, y - e.h, e.w, e.h); p.fill(); }
    p.globalAlpha = 1; p.fillStyle = e.kind !== "ghost" ? "#FFFFFF" : "#3A2A5A"; p.beginPath(); p.arc(x + e.facing * e.w * 0.2, y - e.h * 0.7, 0.8, 0, Math.PI * 2); p.fill();
    if (e.hp < e.hpMax) { p.fillStyle = "rgba(40,0,0,0.8)"; p.fillRect(x - 4, y - e.h - 3, 8, 1); p.fillStyle = "#E53935"; p.fillRect(x - 4, y - e.h - 3, 8 * Math.max(0, e.hp) / e.hpMax, 1); }
  },
  caveBoss(p, e, run) {
    const x = e.x, y = e.y, i = e.index, disc = (cx, cy, r) => { p.beginPath(); p.arc(cx, cy, r, 0, Math.PI * 2); p.fill(); };
    if (i === 0) { const n = e.segments.length; e.segments.slice().reverse().forEach(([sx, sy], j) => { const k = 1 - (n - j) * 0.03; p.fillStyle = `rgb(${Math.round(192 * k)},${Math.round(122 * k)},${Math.round(106 * k)})`; disc(sx, sy - 6, 4 + (j / n) * 4); }); p.fillStyle = "#FFE36E"; disc(x + e.vx, y - 7, 1.5); }
    else if (i === 1) { const gr = p.createRadialGradient(x, y - 8, 0, x, y - 8, 14); gr.addColorStop(0, "#FFFFFF"); gr.addColorStop(0.5, e.colour); gr.addColorStop(1, "rgba(150,200,255,0)"); p.fillStyle = gr; disc(x, y - 8, 14); p.fillStyle = "#2A4A6A"; disc(x - 2, y - 9, 1.4); disc(x + 2, y - 9, 1.4); }
    else if (i === 2) { p.fillStyle = "#E9D7B8"; p.fillRect(x - 4, y - 10, 8, 10); p.fillStyle = e.colour; p.beginPath(); p.moveTo(x - 14, y - 9); p.quadraticCurveTo(x, y - 30 - Math.sin(e.t * 2) * 2, x + 14, y - 9); p.closePath(); p.fill(); p.fillStyle = "#F5E6FF"; for (const [dx, dy] of [[-7, -14], [2, -20], [8, -13], [-2, -12]]) disc(x + dx, y + dy, 1.6); }
    else if (i === 3) { p.fillStyle = "#2A1A16"; p.fillRect(x - 10, y - 28, 20, 28); p.fillStyle = e.colour; for (let k = 0; k < 5; k++) p.fillRect(x - 8 + ((k * 7) % 14), y - 26 + k * 5, 4, 2); p.fillStyle = "#FFE36E"; disc(x - 3, y - 22, 1.5); disc(x + 3, y - 22, 1.5); }
    else {
      const gr = p.createRadialGradient(x, y - 11, 0, x, y - 11, 22); gr.addColorStop(0, "#FFFFFF"); gr.addColorStop(0.3, "#C9B8FF"); gr.addColorStop(0.7, "rgba(60,20,90,0.8)"); gr.addColorStop(1, "rgba(0,0,0,0)"); p.fillStyle = gr; disc(x, y - 11, 22);
      for (let j = 0; j < 3; j++) { const a = e.t * 0.8 + (j * Math.PI * 2) / 3, ex = x + Math.cos(a) * 6, ey = y - 11 + Math.sin(a) * 6; p.fillStyle = "#FFFFFF"; disc(ex, ey, 2.4); p.fillStyle = "#1A0A2A"; disc(ex + Math.max(-1, Math.min(1, run.player.x - ex)), ey, 1.1); }   // (three eyes, watching)
    }
  },
  cavePickup(p, k) {
    const x = k.x, y = k.y, bob = Math.sin(k.t * 3) * 0.8, disc = (cx, cy, r) => { p.beginPath(); p.arc(cx, cy, r, 0, Math.PI * 2); p.fill(); };
    if (k.kind === "gold") { p.fillStyle = "#F2C230"; disc(x, y - 1.5, 1.4); }
    else if (k.kind === "heart") { p.fillStyle = "#E53935"; disc(x - 1.2, y - 4 + bob, 1.6); disc(x + 1.2, y - 4 + bob, 1.6); p.beginPath(); p.moveTo(x - 2.8, y - 3.6 + bob); p.lineTo(x + 2.8, y - 3.6 + bob); p.lineTo(x, y - 0.5 + bob); p.fill(); }
    else if (k.kind === "fountain") { p.fillStyle = "#6A6A7A"; p.fillRect(x - 5, y - 4, 10, 4); p.fillStyle = "rgba(110,190,255,0.8)"; p.beginPath(); p.ellipse(x, y - 6 + bob, 2.5, 3, 0, 0, Math.PI * 2); p.fill(); }
    else if (k.kind === "rope") { p.strokeStyle = "#C8A060"; p.lineWidth = 0.8; p.beginPath(); p.moveTo(x, y); for (let j = 1; j <= 12; j++) p.lineTo(x + Math.sin(k.t * 2 + j) * 0.6, y - j * 5); p.stroke(); p.fillStyle = "rgba(255,240,200,0.25)"; p.fillRect(x - 3, y - 60, 6, 60); }   // (the rope up, and daylight down it)
    else if (k.kind === "wand") { p.strokeStyle = k.value.colour; p.lineWidth = 1.2; p.beginPath(); p.moveTo(x - 3, y - 1 + bob); p.lineTo(x + 3, y - 5 + bob); p.stroke(); p.fillStyle = "#9EE6FF"; disc(x + 3, y - 5 + bob, 1); }
    else if (k.kind === "spell") { p.fillStyle = CAVE_KIND_COLOUR[CM.WAND_SPELLS[k.value].kind]; p.fillRect(x - 2.5, y - 6 + bob, 5, 5); }
    if (k.price) { p.font = "4px Tahoma, sans-serif"; p.textAlign = "center"; p.fillStyle = "#F2C230"; p.fillText(`${k.price}g`, x, y + 5); p.textAlign = "left"; }
  },
  caveHud(p, c, run) {
    const pl = run.player, u = c.width / 960 > 1 ? c.width / 960 : 1, F = (px, bold) => `${bold ? "bold " : ""}${Math.round(px * u)}px Tahoma, sans-serif`;
    p.save(); p.scale(u, u); const Wd = c.width / u, Ht = c.height / u;
    const bar = (y, frac, col, label) => { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(12, y, 180, 12); p.fillStyle = col; p.fillRect(13, y + 1, 178 * Math.max(0, Math.min(1, frac)), 10); p.fillStyle = "#FFFFFF"; p.font = F(12, true); p.fillText(label, 198, y + 11); };
    p.font = F(12, true); p.textBaseline = "alphabetic";
    bar(12, pl.hp / pl.hpMax, "#D9363E", `${Math.round(pl.hp)} / ${Math.round(pl.hpMax)}`); bar(28, pl.lev / 100, "#E8C547", "Levitation");
    const w = run.wand; if (w) bar(44, w.mana / w.mana_max, "#3F8DF0", `${Math.round(w.mana)} mana${w.recharging ? "  recharging" : ""}`);
    p.textAlign = "right"; p.fillStyle = "#F2C230"; p.fillText(`Gold ${pl.gold}`, Wd - 12, 24);
    const b = pl.y > CM.CV.SURFACE ? CM.cvBiomeAt(Math.floor(pl.y)) : -1; p.fillStyle = "#E0E0E0"; p.fillText(`${b >= 0 ? CM.CV_BIOMES[b].name : "The cave's mouth"}   ${run.depth()} m`, Wd - 12, 42);
    p.fillStyle = "#B8B0C8"; p.font = F(11); p.fillText(`${pl.name}   experience ${Math.round(run.xp)}   kills ${pl.kills}`, Wd - 12, 58); p.textAlign = "left";
    pl.wands.forEach((wd, i) => {                                       // the wands, bottom left
      const x = 12 + i * 40, y = Ht - 46; p.fillStyle = "rgba(0,0,0,0.63)"; p.strokeStyle = i === pl.current ? "#F2C230" : "#555060"; p.lineWidth = 2; p.fillRect(x, y, 34, 34); p.strokeRect(x, y, 34, 34);
      p.strokeStyle = wd.colour; p.lineWidth = 3; p.beginPath(); p.moveTo(x + 8, y + 26); p.lineTo(x + 24, y + 10); p.stroke(); p.fillStyle = "#FFFFFF"; p.font = F(11, true); p.fillText(String(i + 1), x + 3, y + 11);
    });
    if (w) { const x0 = 12 + 4 * 40 + 10; w.slots.forEach((name, j) => { const x = x0 + j * 24, y = Ht - 40; p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(x, y, 22, 22); p.strokeStyle = j === w.cursor ? "#F2C230" : "#3A3440"; p.lineWidth = 1; p.strokeRect(x, y, 22, 22); if (name) p.drawImage(this.spellIcon(name, 22), x, y); }); }
    const item = run.nearestItem();
    if (item) { p.textAlign = "center"; p.fillStyle = "#FFFFFF"; p.font = F(13, true); p.fillText(item.kind === "rope" ? "E - climb the rope out, with what you carry" : `E - ${item.price ? "buy" : "take"} ${item.kind === "wand" ? item.value.name : item.value}${item.price ? ` (${item.price} gold)` : ""}`, Wd / 2, Ht * 0.62); p.textAlign = "left"; }
    if (run.boss && run.enemies.includes(run.boss)) { const bw = Wd * 0.5, x = (Wd - bw) / 2, by = 74; p.fillStyle = "rgba(0,0,0,0.67)"; p.fillRect(x, by, bw, 14); p.fillStyle = "#9C2BD6"; p.fillRect(x + 1, by + 1, (bw - 2) * Math.max(0, run.boss.hp) / run.boss.hpMax, 12); p.fillStyle = "#FFFFFF"; p.textAlign = "center"; p.font = F(12, true); p.fillText(run.boss.kind, Wd / 2, by + 30); p.textAlign = "left"; }   // (under the hero's bars)
    if (run.banner[1]) { p.textAlign = "center"; p.font = `italic ${Math.round(30 * u)}px Georgia, serif`; p.fillStyle = `rgba(242,230,200,${Math.min(1, run.banner[1] * 6 / 255)})`; p.fillText(run.banner[0], Wd / 2, Ht * 0.22 + 30); p.textAlign = "left"; }
    p.fillStyle = "rgba(220,210,240,0.55)"; p.font = F(11); p.textAlign = "right"; p.fillText("A D move - W or Space jump (hold: levitate) - mouse aims, click casts - 1-4 or the wheel: wands - E take - Tab wands - Esc pause", Wd - 12, Ht - 8); p.textAlign = "left";
    p.restore();
  },
  caveCentre(p, c, big, small) {
    p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, c.width, c.height); p.textAlign = "center"; p.fillStyle = "#F2E6C8";
    const u = Math.max(1, c.width / 960); p.font = `${Math.round(40 * u)}px Georgia, serif`; p.fillText(big, c.width / 2, c.height * 0.36);
    p.font = `${Math.round(15 * u)}px Georgia, serif`; small.split("\n").forEach((line, i) => p.fillText(line, c.width / 2, c.height * 0.36 + (40 + i * 22) * u)); p.textAlign = "left";
  },
  caveOver(p, c, run) {
    const pl = run.player, stats = `Depth ${run.depth()} m   Kills ${pl.kills}   Gold ${pl.gold}   Experience ${Math.round(run.xp)}`;
    if (run.over === "won") this.caveCentre(p, c, "The Unmaker is undone", `The deep is quiet.\n\n${stats}`);
    else if (run.over === "out") this.caveCentre(p, c, "Up the rope, into the light", `Everything carried comes out with you.\n\n${stats}`);
    else this.caveCentre(p, c, "You have died", `The cave takes back what it gave. The experience is yours.\n\n${stats}`);
  },
  // ---- Tab: the wand editor (Claudeita's own: click a spell, then where it goes; right-click a wand's to the bag) ----
  caveLayout(run) {
    const out = [], x0 = 40, y0 = 70, u = this.caveU || 1;
    run.player.wands.forEach((w, i) => w.slots.forEach((n, j) => out.push([["wand", i, j], [(x0 + 190 + j * 34) * u, (y0 + i * 70 + 18) * u, 30 * u, 30 * u]])));
    for (let k = 0; k < 16; k++) out.push([["bag", k], [(x0 + (k % 8) * 38) * u, (y0 + 4 * 70 + 30 + Math.floor(k / 8) * 38) * u, 34 * u, 34 * u]]);
    return out;
  },
  caveSlot(run, key) { const pl = run.player; return key[0] === "wand" ? pl.wands[key[1]].slots[key[2]] : pl.spells[key[1]] || null; },
  caveSlotSet(run, key, name) {
    const pl = run.player;
    if (key[0] === "wand") { pl.wands[key[1]].slots[key[2]] = name; pl.wands[key[1]].cursor = 0; return; }
    const k = key[1]; if (name === null) { if (k < pl.spells.length) pl.spells.splice(k, 1); } else if (k < pl.spells.length) pl.spells[k] = name; else pl.spells.push(name);
  },
  caveEditorClick(run, x, y, right) {
    const same = (a, b) => a && b && a.join() === b.join();
    for (const [key, [rx, ry, rw, rh]] of this.caveLayout(run)) {
      if (x < rx || x > rx + rw || y < ry || y > ry + rh) continue;
      const here = this.caveSlot(run, key);
      if (right && key[0] === "wand" && here) { if (run.player.spells.length < 16) { this.caveSlotSet(run, key, null); run.player.spells.push(here); } this.cavePick = null; return; }   // (back into the bag)
      if (this.cavePick === null) { if (here) this.cavePick = key; return; }
      if (same(this.cavePick, key)) { this.cavePick = null; return; }
      const src = this.cavePick, moving = this.caveSlot(run, src); this.cavePick = null;
      if (src[0] === "bag" && key[0] === "bag") return;
      if (src[0] === "bag") { this.caveSlotSet(run, key, moving); this.caveSlotSet(run, src, here); }             // bag to wand: what was there back into the bag
      else if (key[0] === "bag") { this.caveSlotSet(run, src, here); if (here === null) run.player.spells.push(moving); else this.caveSlotSet(run, key, moving); }
      else { this.caveSlotSet(run, key, moving); this.caveSlotSet(run, src, here); }
      try { CM.audio.play("card", 0.3); } catch (e) { /* quiet */ }
      return;
    }
    this.cavePick = null;
  },
  caveEditor(p, c, run) {
    const pl = run.player, u = this.caveU = Math.max(1, c.width / 960), m = this.caveMouse || [-1, -1];
    p.fillStyle = "rgba(8,6,14,0.86)"; p.fillRect(0, 0, c.width, c.height);
    p.fillStyle = "#F2E6C8"; p.font = `${Math.round(22 * u)}px Georgia, serif`; p.fillText("Wands and Spells", 40 * u, 46 * u);
    p.font = `${Math.round(11 * u)}px Tahoma, sans-serif`; p.fillStyle = "#B8B0C8"; p.textAlign = "right"; p.fillText("Click a spell, then click where it goes. Right-click a wand's spell to put it in the bag. Tab to close.", c.width - 40 * u, 44 * u); p.textAlign = "left";
    pl.wands.forEach((w, i) => {
      const y = (70 + i * 70) * u; p.fillStyle = i === pl.current ? "#F2C230" : "#E0D8F0"; p.font = `${Math.round(12 * u)}px Tahoma, sans-serif`; p.fillText(`${i + 1}. ${w.name}${w.given ? " (given)" : w.own ? " (yours)" : ""}`, 40 * u, y + 12 * u);
      p.fillStyle = "#9A92AE"; p.font = `${Math.round(11 * u)}px Tahoma, sans-serif`; [`Mana ${w.mana_max} (+${w.charge}/s)`, `Delay ${w.delay}s  Recharge ${w.recharge}s`, `Spread ${w.spread}°`].forEach((t, k) => p.fillText(t, 40 * u, y + (28 + k * 13) * u));
    });
    let hover = null;
    for (const [key, [x, y, w, h]] of this.caveLayout(run)) {
      const here = this.caveSlot(run, key), sel = this.cavePick && this.cavePick.join() === key.join();
      p.fillStyle = "#14101C"; p.fillRect(x, y, w, h); p.strokeStyle = sel ? "#F2C230" : "#3A3440"; p.lineWidth = sel ? 2 : 1; p.strokeRect(x, y, w, h);
      if (here) { const sz = Math.round(26 * u); p.drawImage(this.spellIcon(here, sz), x + (w - sz) / 2, y + (h - sz) / 2); if (m[0] >= x && m[0] <= x + w && m[1] >= y && m[1] <= y + h) hover = here; }
    }
    p.fillStyle = "#E0D8F0"; p.font = `${Math.round(12 * u)}px Tahoma, sans-serif`; p.fillText(`Spell bag (${pl.spells.length}/16)`, 40 * u, (70 + 4 * 70 + 22) * u);
    if (hover) {
      const S = CM.WAND_SPELLS[hover]; p.fillStyle = "#FFFFFF"; p.font = `bold ${Math.round(13 * u)}px Tahoma, sans-serif`;
      p.fillText(`${hover}  (${{ proj: "Projectile", mod: "Modifier", multi: "Multicast" }[S.kind]})${S.dmg ? `   Damage ${S.dmg}` : ""}   Mana ${S.mana}`, 40 * u, c.height - 56 * u);
      p.fillStyle = "#C8C0D8"; p.font = `${Math.round(11 * u)}px Tahoma, sans-serif`; p.fillText(S.desc, 40 * u, c.height - 36 * u);
    }
  },
});
