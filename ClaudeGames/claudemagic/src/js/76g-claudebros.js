"use strict";
// Super Claude Bros, the window's side (the seventeenth update): the pipe's dialog, and the levels drawn side-on on a
// canvas over the view - each level's own sky and far scenery, its tiles painted in code, the coins spinning, the foes
// in the game's own monster pictures, the hero as a little figure in their calling's colours with their weapon, the
// card that names each level, and a HUD of coins, health and experience. The run is 64m-claudebros.js; the rules
// 61j-pipe.js; the frame loop 80-main.js.
const BR_WARDEN_ART = { name: "The Brass Warden", colour: "#B08A3A", body: "tall", head: "helm", eyes: "#FF6020", extras: ["sword", "shield"], speed: 9 };
const BR_HERO_COLOURS = { Knight: ["#9AA0AC", "#7A1A1A", "helm"], Paladin: ["#D8D8E0", "#2A4A9A", "helm"], Rogue: ["#3E5A2E", "#2A2018", "hood"], Ranger: ["#4A6A30", "#5A3A1E", "hood"], Monk: ["#C8822A", "#6A3A10", "band"], Cleric: ["#E8E4DA", "#C8A040", "bare"],
  Mage: ["#2A3A8A", "#C8A040", "wizard"], Druid: ["#3A6A3A", "#6A4A2A", "hood"], Bard: ["#8A2A6A", "#E8C040", "cap"], Necromancer: ["#2A2230", "#6A2A8A", "hood"], Artificer: ["#6A4A30", "#C87A30", "goggles"] };
Object.assign(CM.UI.prototype, {
  openBrosPipe() {
    const g = this.game, box = this.$("#bros-who"), note = this.$("#bros-note");
    box.innerHTML = `${g.party.map((h, i) => `<div class="recruit" style="grid-template-columns: 1fr auto"><div><b>${this.esc(h.name)}</b> the ${this.esc(h.cls)} <small>- ${CM.brArms(h).ranged ? (CM.brArms(h).shot === "arrow" ? "arrows" : "bolts") : "a blade"}, and their boots</small>${h.hp <= 0 ? "<br><small>Has fallen.</small>" : ""}</div><div class="hire"><button data-bros-hero="${i}" ${h.hp <= 0 ? "disabled" : ""}>Climb in</button></div></div>`).join("")}
      <p class="small">Four levels, 1-1 to 1-4: run and jump to the banner pole at the end of each. Land on foes, or use your weapon. Coins are gold (${CM.BR.coinGold} each), foes are experience - and you keep both even if you fall, though you come back up with a tenth of your health.</p>`;
    for (const b of box.querySelectorAll("[data-bros-hero]")) b.addEventListener("click", () => { const why = g.enterBros(Number(b.dataset.brosHero)); note.textContent = why || ""; if (!why) { this.closeDialogs(); this.refresh(); } });
    note.textContent = "";
    this.openDialog("#dlg-bros");
  },
  brosStart(run) { this.brPics = this.brPics || {}; this.brCardAt = performance.now(); this.brCanvas(); },
  brCanvas() {
    let c = this.$("#broscanvas");
    if (!c) { c = document.createElement("canvas"); c.id = "broscanvas"; this.$("#view").appendChild(c); }
    const r = c.getBoundingClientRect(), w = Math.max(480, Math.round(r.width)), h = Math.max(300, Math.round(r.height));
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    return c;
  },
  brPic(key, make) { if (!(key in this.brPics)) { try { this.brPics[key] = make(); } catch (e) { this.brPics[key] = null; } } return this.brPics[key]; },
  // a level's tiles drawn once onto a long strip (crates knocked and coins taken are drawn over it as the run goes)
  brStrip(run) {
    const key = `${run.li}`; if (this.brStripC && this.brStripC.key === key) return this.brStripC.canvas;
    const T = 32, H = CM.BR.H, c = document.createElement("canvas"); c.width = run.w * T; c.height = H * T; const p = c.getContext("2d"), L = run.L, rnd = new CM.Random(77 + run.li);
    const G = run.grid, PAL = { meadow: ["#5A8A2A", "#7A5230", "#4A7A22"], cave: ["#5A4A40", "#3A2E28", "#6A5A4E"], trees: ["#6A8A3A", "#6A4A2A", "#5A7A30"], keep: ["#5A5458", "#3A3438", "#6A6468"] }[L.ground];
    for (let y = 0; y < H; y++) for (let x = 0; x < run.w; x++) {
      const ch = G[y][x], X = x * T, Y = y * T; if (ch === " " || ch === "o") continue;
      if (ch === "#") { const top = !G[y - 1] || !CM.BR_SOLID.has(G[y - 1][x]); p.fillStyle = PAL[1]; p.fillRect(X, Y, T, T); p.fillStyle = "rgba(0,0,0,0.12)"; for (let k = 0; k < 4; k++) p.fillRect(X + rnd.int(0, 28), Y + rnd.int(4, 28), 4, 3); if (top) { p.fillStyle = PAL[0]; p.fillRect(X, Y, T, 9); p.fillStyle = PAL[2]; for (let k = 0; k < 5; k++) p.fillRect(X + k * 7, Y + 7, 3, 4); } }
      else if (ch === "W") { p.fillStyle = PAL[1]; p.fillRect(X, Y, T, T); p.strokeStyle = "rgba(0,0,0,0.35)"; p.strokeRect(X + 0.5, Y + 0.5, T - 1, T / 2); p.strokeRect(X + T / 2 + 0.5, Y + T / 2 + 0.5, T / 2 - 1, T / 2 - 1); }
      else if (ch === "B") { p.fillStyle = "#A0522D"; p.fillRect(X, Y, T, T); p.strokeStyle = "#5A2A14"; p.lineWidth = 2; p.strokeRect(X + 1, Y + 1, T - 2, T - 2); p.beginPath(); p.moveTo(X, Y + T / 2); p.lineTo(X + T, Y + T / 2); p.moveTo(X + T / 2, Y); p.lineTo(X + T / 2, Y + T / 2); p.moveTo(X + T / 4, Y + T / 2); p.lineTo(X + T / 4, Y + T); p.moveTo(X + (3 * T) / 4, Y + T / 2); p.lineTo(X + (3 * T) / 4, Y + T); p.stroke(); p.lineWidth = 1; }
      else if (ch === "=") { p.fillStyle = L.ground === "trees" ? "#7A5230" : "#8A8478"; p.fillRect(X, Y, T, T * 0.5); p.fillStyle = L.ground === "trees" ? "#5A8A2A" : "#A8A298"; p.fillRect(X, Y, T, 5); p.fillStyle = "rgba(0,0,0,0.25)"; p.fillRect(X, Y + T * 0.5 - 3, T, 3); }
      else if (ch === "S") { p.fillStyle = "#8A8478"; p.fillRect(X, Y, T, T); p.fillStyle = "#A8A298"; p.fillRect(X, Y, T, 4); p.fillRect(X, Y, 4, T); p.fillStyle = "#5A5650"; p.fillRect(X, Y + T - 4, T, 4); p.fillRect(X + T - 4, Y, 4, T); }
      else if (ch === "T") { p.fillStyle = "#5A3A1E"; p.fillRect(X + 9, Y, T - 18, T); p.fillStyle = "rgba(0,0,0,0.2)"; p.fillRect(X + 9, Y, 4, T); }
      else if (ch === "L") { const g2 = p.createLinearGradient(0, Y, 0, Y + T); g2.addColorStop(0, "#FFB030"); g2.addColorStop(1, "#C02810"); p.fillStyle = g2; p.fillRect(X, Y, T, T); }
      else if (ch === "J") { p.fillStyle = "#3A3438"; p.fillRect(X, Y, T, T); p.fillStyle = "#1A1416"; p.fillRect(X + 10, Y, T - 20, 8); p.fillStyle = "#6A6468"; p.fillRect(X, Y + T - 6, T, 6); }
      else if (ch === "|") { p.fillStyle = "#C8C0A8"; p.fillRect(X + 14, Y, 4, T); }
      else if (ch === "F") { p.fillStyle = "#E8C040"; p.beginPath(); p.arc(X + 16, Y + 22, 6, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C8C0A8"; p.fillRect(X + 14, Y + 26, 4, 6); }
    }
    this.brStripC = { key, canvas: c }; return c;
  },
  brScenery(p, c, run, camX, T) {
    const L = run.L, g = p.createLinearGradient(0, 0, 0, c.height); g.addColorStop(0, L.sky[0]); g.addColorStop(1, L.sky[1]); p.fillStyle = g; p.fillRect(0, 0, c.width, c.height);
    const far = (k, colour, y0, amp, step) => { p.fillStyle = colour; p.beginPath(); p.moveTo(0, c.height); for (let x = 0; x <= c.width + step; x += step) { const wx = x + camX * T * k; p.lineTo(x, y0 + Math.sin(wx / 170) * amp + Math.sin(wx / 61) * amp * 0.3); } p.lineTo(c.width, c.height); p.closePath(); p.fill(); };
    if (L.ground === "meadow") { for (let i = 0; i < 6; i++) { const x = ((i * 260 - camX * T * 0.2) % (c.width + 300) + c.width + 300) % (c.width + 300) - 150, y = 40 + (i % 3) * 30; p.fillStyle = "rgba(255,255,255,0.85)"; p.beginPath(); p.ellipse(x, y, 46, 14, 0, 0, Math.PI * 2); p.ellipse(x + 26, y - 8, 30, 14, 0, 0, Math.PI * 2); p.fill(); } far(0.3, "#8EC06A", c.height * 0.62, 26, 12); far(0.55, "#6AA048", c.height * 0.72, 18, 12); }
    else if (L.ground === "cave") { far(0.3, "#1E1620", c.height * 0.4, 40, 16); p.fillStyle = "rgba(255,200,120,0.06)"; for (let i = 0; i < 12; i++) { const x = ((i * 137 - camX * T * 0.3) % c.width + c.width) % c.width; p.beginPath(); p.arc(x, 90 + (i % 4) * 40, 2, 0, Math.PI * 2); p.fill(); } }
    else if (L.ground === "trees") { far(0.2, "#D88A58", c.height * 0.55, 30, 14); far(0.45, "#4A6A30", c.height * 0.7, 24, 10); p.fillStyle = "rgba(255,240,200,0.7)"; p.beginPath(); p.arc(c.width * 0.8, 70, 34, 0, Math.PI * 2); p.fill(); }
    else { far(0.3, "#2A1414", c.height * 0.5, 10, 40); p.fillStyle = "rgba(255,120,40,0.18)"; p.fillRect(0, c.height * 0.85, c.width, c.height * 0.15); for (let i = 0; i < 6; i++) { const x = ((i * 220 - camX * T * 0.4) % (c.width + 200) + c.width + 200) % (c.width + 200) - 100; p.fillStyle = "#3A1A16"; p.fillRect(x, c.height * 0.25, 40, c.height * 0.6); p.fillStyle = "#FFB040"; p.fillRect(x + 14, c.height * 0.35, 12, 18); } }
  },
  // the hero: an original little figure in their calling's colours, with their weapon
  brHero(p, run, sx, sy, T) {
    const pl = run.p, h = run.hero, [body, trim, head] = BR_HERO_COLOURS[h.cls] || ["#8A8A94", "#7A1A1A", "helm"], s = T / 32, f = pl.face, moving = Math.abs(pl.vx) > 0.5 && pl.onGround, step = moving ? Math.sin(run.t * 18) : 0;
    if (pl.inv > 0 && Math.floor(run.t * 12) % 2) return;
    p.save(); p.translate(sx, sy); p.scale(f * s, s);
    p.fillStyle = "rgba(0,0,0,0.25)"; p.beginPath(); p.ellipse(0, 0, 10, 3, 0, 0, Math.PI * 2); p.fill();
    p.fillStyle = "#3A2A20"; p.fillRect(-7, -14 + Math.max(0, step) * 2, 6, 14 - Math.max(0, step) * 2); p.fillRect(1, -14 + Math.max(0, -step) * 2, 6, 14 - Math.max(0, -step) * 2);   // (legs)
    p.fillStyle = body; p.fillRect(-9, -34, 18, 21); p.fillStyle = trim; p.fillRect(-9, -18, 18, 3); p.fillRect(-2, -34, 4, 16);
    p.fillStyle = "#F0C8A0"; p.beginPath(); p.arc(0, -42, 8, 0, Math.PI * 2); p.fill(); p.fillStyle = "#2A1A10"; p.fillRect(3, -44, 2, 3);
    p.fillStyle = trim;
    if (head === "helm") { p.fillStyle = "#9A9AA4"; p.beginPath(); p.arc(0, -43, 9, Math.PI, 0); p.fill(); p.fillRect(-9, -43, 18, 3); }
    else if (head === "hood") { p.fillStyle = body; p.beginPath(); p.arc(-1, -43, 10, Math.PI * 0.9, Math.PI * 2.1); p.fill(); }
    else if (head === "wizard") { p.fillStyle = body; p.beginPath(); p.moveTo(-11, -46); p.lineTo(11, -46); p.lineTo(-3, -66); p.closePath(); p.fill(); p.fillStyle = trim; p.fillRect(-11, -47, 22, 3); }
    else if (head === "cap") { p.fillStyle = body; p.fillRect(-9, -52, 16, 6); p.fillStyle = trim; p.fillRect(4, -58, 2, 8); }
    else if (head === "band") { p.fillStyle = trim; p.fillRect(-8, -48, 16, 3); }
    else if (head === "goggles") { p.fillStyle = "#3A2A20"; p.fillRect(-8, -47, 16, 3); p.fillStyle = "#80C0E0"; p.fillRect(1, -48, 6, 5); }
    const swing = run.t - pl.swingAt < 0.18, A = run.arms;
    if (!A.ranged) { p.save(); p.translate(8, -26); p.rotate(swing ? -0.2 + ((run.t - pl.swingAt) / 0.18) * 2.2 : -0.9); p.fillStyle = "#D8D8E0"; p.fillRect(0, -3, 22, 4); p.fillStyle = "#8A6A30"; p.fillRect(-4, -5, 4, 8); p.restore(); if (swing) { p.strokeStyle = "rgba(255,255,240,0.7)"; p.lineWidth = 3; p.beginPath(); p.arc(8, -26, 26, -1.0, 1.1); p.stroke(); } }
    else if (A.shot === "arrow") { p.strokeStyle = "#7A5230"; p.lineWidth = 3; p.beginPath(); p.arc(8, -26, 12, -1.2, 1.2); p.stroke(); }
    else { p.strokeStyle = "#6A4A2A"; p.lineWidth = 3; p.beginPath(); p.moveTo(10, -10); p.lineTo(13, -46); p.stroke(); p.fillStyle = swing ? "#FFF0A0" : "#A0E0FF"; p.beginPath(); p.arc(13, -48, 5, 0, Math.PI * 2); p.fill(); }
    p.restore();
  },
  drawBros(run, now) {
    const c = this.brCanvas(), p = c.getContext("2d"), H = CM.BR.H, T = c.height / H, camX = Math.max(0, Math.min(run.w - c.width / T, run.p.x - c.width / T / 2.6));
    p.setTransform(1, 0, 0, 1, 0, 0); p.imageSmoothingEnabled = false;
    this.brScenery(p, c, run, camX, T);
    const strip = this.brStrip(run), k = T / 32; p.drawImage(strip, camX * 32, 0, c.width / k, strip.height, 0, 0, c.width, c.height);
    const X = (x) => (x - camX) * T, x0 = Math.floor(camX) - 1, x1 = Math.ceil(camX + c.width / T) + 1;
    for (let y = 0; y < H; y++) for (let x = Math.max(0, x0); x < Math.min(run.w, x1); x++) {
      const ch = run.grid[y][x];
      if (ch === "o") { const sw = Math.abs(Math.sin(run.t * 4 + x * 0.7)); p.fillStyle = "#F8D040"; p.strokeStyle = "#A07A10"; p.lineWidth = 2; p.beginPath(); p.ellipse(X(x + 0.5), (y + 0.5) * T, Math.max(1, T * 0.28 * sw), T * 0.34, 0, 0, Math.PI * 2); p.fill(); p.stroke(); }
      else if (ch === "h") { const Xc = X(x + 0.5), Y = (y + 0.55) * T + Math.sin(run.t * 3 + x) * T * 0.05; p.fillStyle = "#D02838"; p.beginPath(); p.arc(Xc, Y + T * 0.08, T * 0.22, 0, Math.PI * 2); p.fill(); p.fillRect(Xc - T * 0.07, Y - T * 0.3, T * 0.14, T * 0.2); p.fillStyle = "#D8C8A0"; p.fillRect(Xc - T * 0.09, Y - T * 0.36, T * 0.18, T * 0.08); p.fillStyle = "rgba(255,255,255,0.5)"; p.beginPath(); p.arc(Xc - T * 0.07, Y, T * 0.06, 0, Math.PI * 2); p.fill(); }   // (a draught)
      else if (ch === "C" || ch === "K") { const Xc = X(x), Y = y * T; p.fillStyle = ch === "C" ? "#C8902A" : "#6A5A48"; p.fillRect(Xc, Y, T, T); p.strokeStyle = ch === "C" ? "#6A4410" : "#3A3028"; p.lineWidth = 2; p.strokeRect(Xc + 2, Y + 2, T - 4, T - 4); if (ch === "C") { p.fillStyle = "#F8E080"; p.beginPath(); p.arc(Xc + T / 2, Y + T / 2, T * 0.18, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C8902A"; p.font = `bold ${Math.round(T * 0.26)}px Georgia`; p.textAlign = "center"; p.fillText("$", Xc + T / 2, Y + T * 0.6); p.textAlign = "left"; } }   // (a coin crate: the party's money-mark on it)
      else if (ch === "J" && run.jetOn()) { const g = p.createLinearGradient(0, y * T - T * 3, 0, y * T); g.addColorStop(0, "rgba(255,200,60,0)"); g.addColorStop(1, "rgba(255,120,30,0.9)"); p.fillStyle = g; p.fillRect(X(x) + T * 0.2, y * T - T * 3, T * 0.6, T * 3); }
    }
    for (const q of run.pops) { const a = (run.t - q.t) / 0.6; p.globalAlpha = 1 - a; p.fillStyle = "#F8D040"; p.beginPath(); p.ellipse(X(q.x), (q.y - a * 2) * T, T * 0.25, T * 0.32, 0, 0, Math.PI * 2); p.fill(); p.globalAlpha = 1; }
    // the banner on its pole, in the party's colours
    if (run.pole) { const px = X(run.pole.x + 0.5), fy = run.cleared ? (run.pole.y - 1) * T : (run.pole.y - 9) * T; p.fillStyle = "#7A1A1A"; p.beginPath(); p.moveTo(px - 2, fy); p.lineTo(px - T * 1.4, fy + T * 0.45); p.lineTo(px - 2, fy + T * 0.9); p.closePath(); p.fill(); p.fillStyle = "#E8C040"; p.beginPath(); p.arc(px - T * 0.6, fy + T * 0.45, T * 0.15, 0, Math.PI * 2); p.fill(); }
    // the foes, in the game's own pictures
    for (const f of run.foes) {
      const sx = X(f.x); if (sx < -2 * T || sx > c.width + 2 * T) continue;
      const pic = this.brPic(f.art, () => (f.boss ? CM.art.monster(BR_WARDEN_ART, true) : CM.art.monster(CM.monsterKind(f.art) || CM.monsterKind("Goblin")))), sz = (f.boss ? 3.2 : f.h + 0.5) * T, dead = f.dead ? (run.t - f.deadAt) : 0;
      p.save(); p.translate(sx, f.y * T); if (f.vx > 0) p.scale(-1, 1); if (dead) { p.globalAlpha = Math.max(0, 1 - dead); p.scale(1, Math.max(0.2, 1 - dead * 2)); }
      if (run.t - f.hitAt < 0.15) p.filter = "brightness(2.2)";
      if (pic) p.drawImage(pic, -sz / 2, -sz, sz, sz); else { p.fillStyle = "#884"; p.fillRect(-f.w * T / 2, -f.h * T, f.w * T, f.h * T); }
      p.filter = "none"; p.restore();
      if (f.boss && !f.dead) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(c.width / 2 - 150, 40, 300, 12); p.fillStyle = "#C8902A"; p.fillRect(c.width / 2 - 150, 40, 300 * f.hp / f.max, 12); p.fillStyle = "#FFF"; p.font = "bold 14px Georgia, serif"; p.textAlign = "center"; p.fillText("The Brass Warden", c.width / 2, 68); p.textAlign = "left"; }
    }
    for (const s of run.shots) { const sx = X(s.x), sy = s.y * T; if (s.kind === "bolt") { const g = p.createRadialGradient(sx, sy, 0, sx, sy, T * 0.4); g.addColorStop(0, "#FFFFFF"); g.addColorStop(0.4, "#80C0FF"); g.addColorStop(1, "rgba(80,120,255,0)"); p.fillStyle = g; p.beginPath(); p.arc(sx, sy, T * 0.4, 0, Math.PI * 2); p.fill(); } else if (s.kind === "bone") { p.save(); p.translate(sx, sy); p.rotate(run.t * 12); p.fillStyle = "#E8E0C8"; p.fillRect(-T * 0.3, -3, T * 0.6, 6); p.restore(); } else { p.strokeStyle = s.from === "hero" ? "#E8DCC0" : "#C8A070"; p.lineWidth = 3; p.beginPath(); p.moveTo(sx, sy); p.lineTo(sx - Math.sign(s.vx) * T * 0.7, sy); p.stroke(); } }
    this.brHero(p, run, X(run.p.x), run.p.y * T, T);
    // the HUD: coins, health, experience; the level's name card; the end
    const h = run.hero; p.font = `bold ${Math.round(T * 0.42)}px Georgia, serif`; p.fillStyle = "#FFF"; p.strokeStyle = "rgba(0,0,0,0.7)"; p.lineWidth = 3;
    const txt = (t, x, y, al = "left") => { p.textAlign = al; p.strokeText(t, x, y); p.fillText(t, x, y); p.textAlign = "left"; };
    txt(`${h.name.toUpperCase()}`, 16, T * 0.7); txt(`WORLD ${run.L.id}`, c.width / 2, T * 0.7, "center"); txt(`● ${run.coins}`, c.width - 16, T * 0.7, "right");
    p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(16, T * 0.9, 180, 12); p.fillStyle = "#D83A3A"; p.fillRect(16, T * 0.9, 180 * Math.max(0, h.hp) / h.max, 12); p.font = `bold ${Math.round(T * 0.3)}px Georgia, serif`; p.fillStyle = "#FFF"; txt(`${Math.max(0, h.hp)} / ${h.max}   xp ${Math.round(run.xp * CM.BR.xpShare)}`, 202, T * 0.9 + 11);
    p.font = `${Math.round(T * 0.26)}px Georgia, serif`; txt("A D or arrows run (Shift faster) - Space, W or Up jump (hold: higher) - J, F or the mouse: your weapon - Esc the menu", c.width / 2, c.height - 10, "center");
    const card = now - (this.brCardAt || 0);
    if (card < 2200) { p.fillStyle = `rgba(0,0,0,${Math.min(0.85, (2200 - card) / 600)})`; p.fillRect(0, 0, c.width, c.height); p.fillStyle = "#FFF"; p.font = `bold ${Math.round(T * 0.9)}px Georgia, serif`; txt(`WORLD ${run.L.id}`, c.width / 2, c.height * 0.42, "center"); p.font = `italic ${Math.round(T * 0.5)}px Georgia, serif`; txt(run.L.name, c.width / 2, c.height * 0.42 + T * 0.9, "center"); }
    if (run.cleared) { p.fillStyle = "#FFF"; p.font = `bold ${Math.round(T * 0.8)}px Georgia, serif`; txt(run.li + 1 >= CM.BR_LEVELS.length ? "THE KEEP IS YOURS!" : "LEVEL CLEAR!", c.width / 2, c.height * 0.35, "center"); }
    if (run.over === "dead") { p.fillStyle = "rgba(40,0,0,0.6)"; p.fillRect(0, 0, c.width, c.height); p.fillStyle = "#FFF"; p.font = `bold ${Math.round(T * 0.8)}px Georgia, serif`; txt("OOF!", c.width / 2, c.height * 0.4, "center"); p.font = `${Math.round(T * 0.4)}px Georgia, serif`; txt(`Back up the pipe with ${run.coins} coins and the experience.`, c.width / 2, c.height * 0.4 + T, "center"); }
  },
});
