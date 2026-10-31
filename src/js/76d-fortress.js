"use strict";
// The Fortress, the window's side (the fourteenth update): the doors' dialog (who goes in), and the floors drawn from
// above on a canvas laid over the view, as a gauntlet is - the maze in the depth's own stone (its walls with their faces
// to the south, the doors of dark wood, the stairs), the keys, draughts, gold, flasks and chests, the lairs, the
// monsters in the game's own pictures, the fighter as a token with their portrait and the swing of their blade, the
// dark around, and the HUD. The run is 64j-fortress.js; the rules 61h-fortress.js; the frame loop 80-main.js.
const FORT_TILE = 32;
Object.assign(CM.UI.prototype, {
  openFortress() {
    const g = this.game, box = this.$("#fortress-who"), note = this.$("#fortress-note"), F = g.fort || { cleared: 0 };
    box.innerHTML = `<div class="list-title">Who goes in (floor ${Math.min(CM.FORT_FLOORS, (F.cleared || 0) + 1)} of ${CM.FORT_FLOORS})</div>${g.fortChoices().map((c) => `<div class="recruit" style="grid-template-columns: 1fr auto"><div><b>${this.esc(c.name)}</b> the ${this.esc(c.cls)}${c.why ? `<br><small>${this.esc(c.why)}</small>` : ""}</div><div class="hire"><button data-fort-hero="${c.i}" ${c.why ? "disabled" : ""}>Go in</button></div></div>`).join("")}
      <p class="small">Keys open the doors (all of a door at once). Lairs send monsters until they are broken. Draughts mend; a fire flask (Q) burns everything near. At the stairs, go on down or come out with everything you carry. Die, and you wake at these doors with a tenth of your health and none of it - but the experience is yours.</p>`;
    for (const b of box.querySelectorAll("[data-fort-hero]")) b.addEventListener("click", () => { const why = g.enterFortress(Number(b.dataset.fortHero)); note.textContent = why || ""; if (!why) { this.closeDialogs(); this.refresh(); } });
    note.textContent = "";
    this.openDialog("#dlg-fortress");
  },
  fortCanvas() {
    let c = this.$("#fortcanvas");
    if (!c) { c = document.createElement("canvas"); c.id = "fortcanvas"; this.$("#view").appendChild(c); }
    const r = c.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1), w = Math.max(320, Math.round(r.width * dpr)), h = Math.max(200, Math.round(r.height * dpr));
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    return c;
  },
  fortArt(key, make) { this.fortPics = this.fortPics || {}; if (!this.fortPics[key]) { try { this.fortPics[key] = make(); } catch (e) { this.fortPics[key] = null; } } return this.fortPics[key]; },
  monPic(kind) { return this.fortArt(`mon:${kind}`, () => CM.art.monster(kind === CM.FORT_MARSHAL.name ? CM.FORT_MARSHAL : CM.monsterKind(kind) || CM.monsterKind("Goblin"), kind === CM.FORT_MARSHAL.name)); },
  // the floor drawn once (again when a door opens): stone underfoot, the walls with their south faces, doors, the stairs
  fortBackground(run) {
    const key = `${run.n}:${run.doorsOpened}:${this.game.seed}`; if (this.fortBg && this.fortBg.key === key) return this.fortBg.canvas;
    const S = run.fl.size, T = FORT_TILE, c = (this.fortBg && this.fortBg.canvas) || document.createElement("canvas"); c.width = c.height = S * T;
    const p = c.getContext("2d"), G = run.grid, rnd = new CM.Random(CM.hashSeed(`fortbg:${run.n}`)), hatch = this.fortArt(`hatch:${run.n}`, () => CM.art.hatch(CM.themeFor(CM.fortDepth(run.n))));
    const PAL = [["#3A3530", "#7A7068", "#4A423A"], ["#3A2E2A", "#7A5E52", "#4E3A32"], ["#2E3238", "#66707E", "#3A4048"], ["#2E3428", "#62705A", "#3A4434"]][Math.floor((run.n - 1) / 5) % 4];   // (floor, wall top, wall face: a stone for every five floors)
    const shade = (hex, k) => { const n = parseInt(hex.slice(1), 16), f = (v) => Math.max(0, Math.min(255, Math.round(v * k))); return `rgb(${f(n >> 16)},${f((n >> 8) & 255)},${f(n & 255)})`; };
    p.fillStyle = "#000"; p.fillRect(0, 0, c.width, c.height);
    for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
      const v = G[y][x], X = x * T, Y = y * T;
      if (v !== 1) {                                                       // flagstones, two or four to a tile, and their mortar
        p.fillStyle = shade(PAL[0], 0.85 + rnd.next() * 0.3); p.fillRect(X, Y, T, T);
        p.strokeStyle = "rgba(0,0,0,0.45)"; p.lineWidth = 1.5; const split = rnd.next() < 0.5; p.strokeRect(X + 0.75, Y + 0.75, T - 1.5, T - 1.5); p.beginPath(); if (split) { p.moveTo(X, Y + T / 2); p.lineTo(X + T, Y + T / 2); } else { p.moveTo(X + T / 2, Y); p.lineTo(X + T / 2, Y + T); } p.stroke();
        for (let k = 0; k < 5; k++) { p.fillStyle = `rgba(${rnd.next() < 0.5 ? "0,0,0" : "255,255,255"},0.06)`; p.fillRect(X + rnd.next() * T, Y + rnd.next() * T, 3, 2); }
        if (G[y - 1] && G[y - 1][x] === 1) { const g = p.createLinearGradient(0, Y, 0, Y + T * 0.45); g.addColorStop(0, "rgba(0,0,0,0.55)"); g.addColorStop(1, "rgba(0,0,0,0)"); p.fillStyle = g; p.fillRect(X, Y, T, T * 0.45); }   // (the wall's shadow)
        if (G[y][x - 1] === 1) { p.fillStyle = "rgba(0,0,0,0.25)"; p.fillRect(X, Y, T * 0.15, T); }
      }
      if (v === 1) {                                                       // the wall: its top in light courses, and where it faces the south, its face
        const face = G[y + 1] && G[y + 1][x] !== 1, top = face ? T * 0.55 : T;
        p.fillStyle = shade(PAL[1], 0.9 + rnd.next() * 0.2); p.fillRect(X, Y, T, top);
        p.strokeStyle = "rgba(0,0,0,0.35)"; p.lineWidth = 1; for (let j = 0; j < 2; j++) { const yy = Y + (top / 2) * j; p.strokeRect(X + (j ? T / 2 : 0) + 0.5, yy + 0.5, T - 1, top / 2 - 1); }
        p.fillStyle = "rgba(255,255,255,0.12)"; if (!(G[y - 1] && G[y - 1][x] === 1)) p.fillRect(X, Y, T, 2);
        if (face) { p.fillStyle = shade(PAL[2], 0.9 + rnd.next() * 0.15); p.fillRect(X, Y + top, T, T - top); p.strokeStyle = "rgba(0,0,0,0.4)"; for (let j = 0; j < 2; j++) p.strokeRect(X + (j ? -T / 3 : T / 6) + 0.5, Y + top + j * (T - top) / 2 + 0.5, T * 0.66, (T - top) / 2 - 1); p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(X, Y + T - 2, T, 2); }
      } else if (v === 2) {                                                // a door: dark planks, iron bands, a gold rim (a key opens it)
        p.fillStyle = "#4A2C16"; p.fillRect(X + 2, Y + 2, T - 4, T - 4); p.fillStyle = "rgba(0,0,0,0.4)"; for (let k = 1; k < 4; k++) p.fillRect(X + 2 + k * (T - 4) / 4, Y + 2, 1.5, T - 4);
        p.fillStyle = "#26262C"; p.fillRect(X + 2, Y + T * 0.28, T - 4, 3); p.fillRect(X + 2, Y + T * 0.68, T - 4, 3); p.strokeStyle = "#E8C050"; p.lineWidth = 2; p.strokeRect(X + 1, Y + 1, T - 2, T - 2);
        p.fillStyle = "#E8C050"; p.beginPath(); p.arc(X + T / 2, Y + T / 2, 3, 0, Math.PI * 2); p.fill(); p.fillRect(X + T / 2 - 1, Y + T / 2, 2, 6);   // (a keyhole)
      }
    }
    const [sx, sy] = run.fl.stairs; if (hatch) p.drawImage(hatch, sx * T - T * 0.1, sy * T - T * 0.1, T * 1.2, T * 1.2); else { p.fillStyle = "#111"; p.fillRect(sx * T, sy * T, T, T); }
    this.fortBg = { key, canvas: c };
    return c;
  },
  drawFortress(run, now) {
    const c = this.fortCanvas(), p = c.getContext("2d"), T = Math.max(26, Math.round(c.height / 15)), k = T / FORT_TILE, bg = this.fortBackground(run);
    const ox = run.x * T - c.width / 2, oy = run.y * T - c.height / 2, X = (x) => x * T - ox, Y = (y) => y * T - oy;
    this.fortView = { ox, oy, T };
    p.setTransform(1, 0, 0, 1, 0, 0); p.imageSmoothingEnabled = true; p.fillStyle = "#000"; p.fillRect(0, 0, c.width, c.height);
    p.drawImage(bg, -ox, -oy, bg.width * k, bg.height * k);
    const t = run.t, pics = { key: () => CM.art.key(), chest: () => CM.art.chest() }, near = (x, y) => Math.abs(x * T - ox - c.width / 2) < c.width && Math.abs(y * T - oy - c.height / 2) < c.height;
    // the lairs and the things on the floor
    for (const L of run.lairs) { if (!near(L.x, L.y)) continue; const pic = this.fortArt("nest", () => CM.art.nest()); p.globalAlpha = L.hp > 0 ? 1 : 0.35; if (pic) p.drawImage(pic, X(L.x) - T * 0.6, Y(L.y) - T * 0.6, T * 1.2, T * 1.2); if (L.hp > 0) { p.fillStyle = `rgba(200,40,255,${0.25 + 0.15 * Math.sin(t * 4 + L.id)})`; p.beginPath(); p.arc(X(L.x), Y(L.y), T * 0.5, 0, Math.PI * 2); p.fill(); if (t - L.hitAt < 0.15) { p.fillStyle = "rgba(255,255,255,0.5)"; p.fill(); } } p.globalAlpha = 1; }
    for (const it of run.items) {
      if (it.taken || !near(it.x, it.y)) continue; const cx = X(it.x + 0.5), cy = Y(it.y + 0.5), bob = Math.sin(t * 3 + it.x) * T * 0.04;
      if (it.kind === "key" || it.kind === "chest") { const pic = this.fortArt(it.kind, pics[it.kind]); if (pic) p.drawImage(pic, cx - T * 0.4, cy - T * 0.45 + bob, T * 0.8, T * 0.8); if (it.kind === "key") { p.fillStyle = "rgba(255,220,90,0.25)"; p.beginPath(); p.arc(cx, cy, T * 0.45, 0, Math.PI * 2); p.fill(); } }
      else if (it.kind === "gold") { p.fillStyle = "#8A6A1A"; for (let j = 0; j < (it.big ? 7 : 4); j++) { const a = j * 2.4, r = T * 0.12 * Math.sqrt(j); p.beginPath(); p.ellipse(cx + Math.cos(a) * r, cy + Math.sin(a) * r * 0.6 + T * 0.1, T * 0.13, T * 0.08, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = j % 2 ? "#F2C230" : "#E0A820"; } }
      else { const red = it.kind === "draught"; p.fillStyle = red ? "#C0283A" : "#E87A20"; p.beginPath(); p.arc(cx, cy + T * 0.05 + bob, T * 0.18, 0, Math.PI * 2); p.fill(); p.fillRect(cx - T * 0.05, cy - T * 0.25 + bob, T * 0.1, T * 0.16); p.fillStyle = "#D8C8A0"; p.fillRect(cx - T * 0.06, cy - T * 0.3 + bob, T * 0.12, T * 0.06); p.fillStyle = "rgba(255,255,255,0.5)"; p.beginPath(); p.arc(cx - T * 0.06, cy + bob, T * 0.05, 0, Math.PI * 2); p.fill(); }
    }
    // the monsters, back to front
    const order = run.mons.filter((o) => (o.m.hp > 0 || (o.fellAt !== null && t - o.fellAt < 0.6)) && near(o.x, o.y)).sort((a, b) => a.y - b.y);
    for (const o of order) {
      const pic = this.monPic(o.kind), sc = (o.scale || 1) * T * 1.15, dead = o.fellAt !== null ? (t - o.fellAt) / 0.6 : 0;
      let lx = 0, ly = 0; if (t - o.lungeAt < 0.25) { const a = Math.atan2(run.y - o.y, run.x - o.x), s = Math.sin(((t - o.lungeAt) / 0.25) * Math.PI) * T * 0.25; lx = Math.cos(a) * s; ly = Math.sin(a) * s; }
      const cx = X(o.x) + lx, cy = Y(o.y) + ly;
      p.fillStyle = "rgba(0,0,0,0.4)"; p.beginPath(); p.ellipse(cx, cy + T * 0.3 * (o.scale || 1), sc * 0.32, sc * 0.12, 0, 0, Math.PI * 2); p.fill();
      if (o.boss) { p.strokeStyle = `rgba(255,${o.boss === "marshal" ? 60 : 160},40,${0.5 + 0.3 * Math.sin(t * 5)})`; p.lineWidth = 3; p.beginPath(); p.ellipse(cx, cy + T * 0.3 * o.scale, sc * 0.4, sc * 0.16, 0, 0, Math.PI * 2); p.stroke(); }
      p.globalAlpha = 1 - dead; if (t - o.hitAt < 0.12) p.filter = "brightness(2.2) sepia(1) hue-rotate(-30deg) saturate(4)";
      if (o.charging) p.filter = "brightness(1.4) saturate(2)";
      if (pic) p.drawImage(pic, cx - sc / 2, cy + T * 0.35 * (o.scale || 1) - sc - dead * T * 0.2, sc, sc * (1 - dead * 0.4)); else { p.fillStyle = o.m.colour || "#888"; p.beginPath(); p.arc(cx, cy, T * 0.35, 0, Math.PI * 2); p.fill(); }
      p.filter = "none"; p.globalAlpha = 1;
      if (o.m.hp > 0 && o.m.hp < o.m.max) { const w = T * 0.8 * (o.scale || 1); p.fillStyle = "rgba(30,0,0,0.8)"; p.fillRect(cx - w / 2, cy - sc * 0.75, w, 4); p.fillStyle = "#E53935"; p.fillRect(cx - w / 2, cy - sc * 0.75, w * o.m.hp / o.m.max, 4); }
    }
    for (const b of run.bolts || []) { p.fillStyle = "#FF7040"; p.beginPath(); p.arc(X(b.x), Y(b.y), T * 0.12, 0, Math.PI * 2); p.fill(); }
    // the fighter: a token with their portrait, and the blade's sweep
    const hx = X(run.x), hy = Y(run.y), hero = run.hero, por = this.fortArt(`por:${hero.cls}`, () => CM.art.portraitDrawn(hero.cls, 64)), hurt = t - run.lastHurt < 0.25;
    p.fillStyle = "rgba(0,0,0,0.45)"; p.beginPath(); p.ellipse(hx, hy + T * 0.32, T * 0.38, T * 0.14, 0, 0, Math.PI * 2); p.fill();
    p.save(); p.beginPath(); p.arc(hx, hy, T * 0.36, 0, Math.PI * 2); p.closePath(); p.fillStyle = "#2A2018"; p.fill(); p.clip(); if (por) p.drawImage(por, hx - T * 0.38, hy - T * 0.38, T * 0.76, T * 0.76); p.restore();
    p.strokeStyle = hurt ? "#FF3A2A" : "#E8C050"; p.lineWidth = 3; p.beginPath(); p.arc(hx, hy, T * 0.36, 0, Math.PI * 2); p.stroke();
    p.fillStyle = "#E8C050"; p.beginPath(); p.moveTo(hx + Math.cos(run.face) * T * 0.5, hy + Math.sin(run.face) * T * 0.5); p.lineTo(hx + Math.cos(run.face + 0.35) * T * 0.38, hy + Math.sin(run.face + 0.35) * T * 0.38); p.lineTo(hx + Math.cos(run.face - 0.35) * T * 0.38, hy + Math.sin(run.face - 0.35) * T * 0.38); p.fill();   // (which way they face)
    const sw = (t - run.swingAt) / 0.18;
    if (sw >= 0 && sw <= 1) { const a0 = run.face - CM.FT.arc / 2, a = a0 + CM.FT.arc * sw; p.strokeStyle = `rgba(255,250,230,${0.85 * (1 - sw * 0.5)})`; p.lineWidth = T * 0.12; p.lineCap = "round"; p.beginPath(); p.arc(hx, hy, T * CM.FT.reach * 0.85, a0, a); p.stroke(); p.strokeStyle = "#D8D8E0"; p.lineWidth = 4; p.beginPath(); p.moveTo(hx + Math.cos(a) * T * 0.35, hy + Math.sin(a) * T * 0.35); p.lineTo(hx + Math.cos(a) * T * CM.FT.reach, hy + Math.sin(a) * T * CM.FT.reach); p.stroke(); p.lineCap = "butt"; }
    // the dark, and a torch's reach
    const lg = p.createRadialGradient(hx, hy, T * 2, hx, hy, T * 8.5); lg.addColorStop(0, "rgba(0,0,0,0)"); lg.addColorStop(1, "rgba(0,0,0,0.88)"); p.fillStyle = lg; p.fillRect(0, 0, c.width, c.height);
    if (this.fortFlashAt && now - this.fortFlashAt < 350) { p.fillStyle = `rgba(255,140,40,${0.45 * (1 - (now - this.fortFlashAt) / 350)})`; p.fillRect(0, 0, c.width, c.height); }
    // the floating numbers
    this.fortFloats = (this.fortFloats || []).filter((f) => now - f.at < 800);
    p.font = `bold ${Math.round(T * 0.45)}px Georgia, serif`; p.textAlign = "center";
    for (const f of this.fortFloats) { const a = (now - f.at) / 800; p.fillStyle = f.colour.replace("A", `${1 - a}`); p.fillText(f.text, X(f.x), Y(f.y) - T * 0.6 - a * T * 0.8); }
    p.textAlign = "left";
    this.fortHud(p, c, run);
  },
  fortFloat(x, y, text, colour) { (this.fortFloats = this.fortFloats || []).push({ x, y, text, colour, at: performance.now() }); },
  fortHud(p, c, run) {
    const u = Math.max(1, c.width / 960), h = run.hero, F = (px, b) => `${b ? "bold " : ""}${Math.round(px * u)}px Georgia, serif`;
    p.save(); p.scale(u, u); const W = c.width / u, H = c.height / u;
    p.fillStyle = "rgba(0,0,0,0.55)"; p.fillRect(10, 10, 250, 64); p.strokeStyle = "#8A6A3A"; p.strokeRect(10, 10, 250, 64);
    p.fillStyle = "#E8DCB8"; p.font = F(13, true); p.fillText(`${h.name} the ${h.cls}`, 18, 28);
    p.fillStyle = "rgba(60,0,0,0.9)"; p.fillRect(18, 34, 234, 12); p.fillStyle = "#C83A3A"; p.fillRect(18, 34, 234 * Math.max(0, h.hp) / h.max, 12); p.fillStyle = "#fff"; p.font = F(10, true); p.fillText(`${Math.max(0, Math.ceil(h.hp))} / ${h.max}`, 22, 44);
    p.font = F(13); p.fillStyle = "#F2C230"; p.fillText(`🗝 ${run.keys}   🔥 ${run.flasks}   ${run.gold} gold   ${run.loot.length ? `${run.loot.length} thing${run.loot.length > 1 ? "s" : ""}` : ""}`, 18, 66);
    p.textAlign = "center"; p.fillStyle = "#E8C890"; p.font = F(15, true); p.fillText(CM.fortFloorName(run.n), W / 2, 26);
    const boss = run.bossInSight(); if (boss) { const bw = W * 0.4; p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(W / 2 - bw / 2, 36, bw, 12); p.fillStyle = "#B03020"; p.fillRect(W / 2 - bw / 2, 36, bw * Math.max(0, boss.m.hp) / boss.m.max, 12); p.fillStyle = "#fff"; p.font = F(12, true); p.fillText(boss.name.charAt(0).toUpperCase() + boss.name.slice(1), W / 2, 64); }
    if (run.atStairs()) { p.fillStyle = "#FFF0C0"; p.font = F(16, true); p.fillText(run.n < CM.FORT_FLOORS ? `The stairs: E to go down to floor ${run.n + 1} - L to come out with everything` : "The way out: E to come up into the daylight", W / 2, H * 0.7); }
    else if (run.fl.marshal && run.marshal && run.marshal.m.hp > 0 && Math.hypot(run.fl.stairs[0] - run.x, run.fl.stairs[1] - run.y) < 2) { p.fillStyle = "#FFB0A0"; p.font = F(15, true); p.fillText("The Iron Marshal holds the way out", W / 2, H * 0.7); }
    p.textAlign = "right"; p.fillStyle = "rgba(230,220,200,0.6)"; p.font = F(11); p.fillText(`experience ${Math.round(run.xp * CM.FT.xpShare)}   kills ${run.kills}`, W - 12, 24);
    p.fillText("W A S D move - Space, J or the mouse strikes (the mouse aims) - Q a fire flask - E at the stairs - Esc the menu", W - 12, H - 10);
    p.restore();
    if (run.over === "dead") { p.fillStyle = "rgba(60,0,0,0.6)"; p.fillRect(0, 0, c.width, c.height); p.fillStyle = "#F2E6C8"; p.textAlign = "center"; p.font = `${Math.round(40 * u)}px Georgia, serif`; p.fillText(`${h.name} falls`, c.width / 2, c.height * 0.42); p.font = `${Math.round(15 * u)}px Georgia, serif`; p.fillText("Everything carried is lost. The experience is theirs.", c.width / 2, c.height * 0.42 + 36 * u); p.textAlign = "left"; }
  },
});
