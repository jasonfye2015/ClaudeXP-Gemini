"use strict";
// Claudeablo, the window's side (the sixteenth update): the world seen at an angle, as Claudeablo draws it - floor
// diamonds and wall blocks for every theme, the town's houses, trees and well, chests, barrels, shrines, portals, the
// heroes, townsfolk and monsters painted in code, the dark beyond the hero's light - and its panel: the life and mana
// orbs, the belt, the experience bar, and the inventory, character, spells, shop, waystone and map panels. The rules
// are 64l-claudeablo.js; who goes through and what comes back, 61i-redportal.js.
const ABT = { TW: 64, TH: 32, WALL_H: 56, PANEL_H: 104 };
const AB_THEMES = { town: ["#5E8A3A", ["#6E9A44", "#4E7A30", "#7AA64E"], "#7A6A58", "#6A5A48", "#5A4A3A", "#3A2A1A"], cathedral: ["#4A4640", ["#56524A", "#3E3A34", "#5E5A52"], "#6E6A64", "#56524C", "#46423C", "#2A2824"],
  catacombs: ["#4A3E30", ["#56483A", "#3E3428", "#5E5040"], "#6A5A46", "#54463A", "#44382C", "#2A2018"], caves: ["#4A3A2E", ["#58463A", "#3C2E24", "#62503E"], "#5E4A3A", "#4A3A2C", "#3A2C20", "#20160E"],
  hell: ["#3A1E1A", ["#4A2620", "#2E1612", "#5A2E24"], "#5A2A22", "#46201A", "#361812", "#1A0806"], abyss: ["#241A2E", ["#2E2238", "#1C1426", "#382A44"], "#3E2E4A", "#30243A", "#24182E", "#100818"], sanctum: ["#1E1414", ["#2A1A1A", "#140C0C", "#321E1E"], "#3A2020", "#2C1818", "#201010", "#0A0404"] };
const AB_LOOKS = {
  warrior: { skin: "#E0B090", body: "#8A8A94", trim: "#C8A040", legs: "#4A4A52", head: "helm", weapon: "sword", shield: true, cape: "#7A1A1A" }, rogue: { skin: "#E8C0A0", body: "#3E5A2E", trim: "#8A6A3A", legs: "#3A2E24", head: "hood", weapon: "bow", cape: "#2E3E22" },
  sorcerer: { skin: "#E0B898", body: "#2A3A8A", trim: "#C8A040", legs: "#1E2A60", head: "wizard", weapon: "staff", robe: true },
  smith: { skin: "#D8A07A", body: "#6A4A30", trim: "#3A2A1A", legs: "#3A3A40", head: "bald", weapon: "hammer", apron: true, size: 1.08 }, witch: { skin: "#E0C0A0", body: "#5A2A6A", trim: "#C8A040", legs: "#3A1A4A", head: "witch", robe: true },
  healer: { skin: "#E8C8A8", body: "#E8E4DA", trim: "#3A6AC0", legs: "#C8C4BA", head: "human", robe: true }, elder: { skin: "#E0C0A0", body: "#6A6460", trim: "#C8A040", legs: "#4A4440", head: "beard", robe: true, weapon: "cane" },
  zombie: { skin: "#7A9A5A", body: "#4A5A3A", trim: "#3A2A1A", legs: "#3A3A2A", head: "zombie", hunch: true }, ghoul: { skin: "#9AA88A", body: "#3A3A30", trim: "#2A2A20", legs: "#2A2A20", head: "zombie", hunch: true },
  skeleton: { skin: "#E8E0C8", head: "skull", weapon: "sword", bones: true }, skeleton_archer: { skin: "#E8E0C8", head: "skull", weapon: "bow", bones: true },
  fallen: { skin: "#C8402A", body: "#8A2A1A", trim: "#3A1A10", legs: "#6A1A10", head: "imp", weapon: "spear", size: 0.72 }, goatman: { skin: "#7A5A3A", body: "#5A4028", trim: "#3A2A1A", legs: "#4A3420", head: "goat", weapon: "axe", size: 1.05 },
  hidden: { skin: "#8AA0C8", body: "#2A3448", trim: "#1A2030", legs: "#1A2030", head: "hood", weapon: "dagger", ghost: true }, hellwitch: { skin: "#C890A0", body: "#5A1A2A", trim: "#E04060", legs: "#3A0E1A", head: "horned", robe: true, wings: true },
  knight: { skin: "#2A2A30", body: "#2E2E36", trim: "#7A1A1A", legs: "#202026", head: "greathelm", weapon: "sword", shield: true, size: 1.1 }, magma: { skin: "#6A2A1A", body: "#5A2214", trim: "#FF7020", legs: "#4A1A10", head: "horned", hulk: true, size: 1.35, glow: true },
  pitlord: { skin: "#4A1E30", body: "#3A1426", trim: "#C83030", legs: "#2A0E1A", head: "horned", hulk: true, size: 1.5, weapon: "axe", wings: true },
  diablo: { skin: "#B0281A", body: "#8A1A10", trim: "#F0C040", legs: "#6A1208", head: "diablo", hulk: true, size: 2.0, spikes: true, tail: true, glow: true },
};
const abShade = (hex, k) => { const n = parseInt(hex.slice(1), 16), f = (v) => Math.max(0, Math.min(255, Math.round(v * k))); return `rgb(${f(n >> 16)},${f((n >> 8) & 255)},${f(n & 255)})`; };
const abRng = (seed) => new CM.AB.Rng(seed);
Object.assign(CM.UI.prototype, {
  // ---- the red portal: who goes through ----
  openClaudeablo() {
    const g = this.game, box = this.$("#ablo-who"), note = this.$("#ablo-note"), A = g.abloStore();
    box.innerHTML = `${g.party.map((h, i) => { const av = A.heroes[CM.abloKey(h)]; return `<div class="recruit" style="grid-template-columns: 1fr auto"><div><b>${this.esc(h.name)}</b> the ${this.esc(h.cls)} <small>- as a ${CM.abloClass(h)}${av ? `, level ${av.level} there, deepest ${av.maxDepth || 0}` : ""}</small>${h.hp <= 0 ? "<br><small>Has fallen.</small>" : ""}</div><div class="hire"><button data-ablo-hero="${i}" ${h.hp <= 0 ? "disabled" : ""}>Step through</button></div></div>`; }).join("")}
      <p class="small">Haven, and the cathedral under it, fifty levels deep. Whatever gold and gear you carry in your pack when you step back through Haven's red portal is the party's; what you wear stays with you there for next time. Experience comes home too.</p>`;
    for (const b of box.querySelectorAll("[data-ablo-hero]")) b.addEventListener("click", () => { const why = g.enterClaudeablo(Number(b.dataset.abloHero)); note.textContent = why || ""; if (!why) { this.closeDialogs(); this.refresh(); } });
    note.textContent = "";
    this.openDialog("#dlg-claudeablo");
  },
  abloStart() { this.abPanels = new Set(); this.abHeld = null; this.abShop = null; this.abCache = {}; this.abMouse = [0, 0]; this.abCanvas(); },
  abCanvas() {
    let c = this.$("#ablocanvas");
    if (!c) { c = document.createElement("canvas"); c.id = "ablocanvas"; this.$("#view").appendChild(c); }
    const r = c.getBoundingClientRect(), w = Math.max(640, Math.round(r.width)), h = Math.max(420, Math.round(r.height));
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    return c;
  },
  abOrigin(w) { const c = this.$("#ablocanvas"), p = w.player; return [c.width / 2 - (p.x - p.y) * 32, (c.height - ABT.PANEL_H) / 2 - (p.x + p.y) * 16]; },
  abToScreen(w, x, y) { const [ox, oy] = this.abOrigin(w); return [ox + (x - y) * 32, oy + (x + y) * 16]; },
  abToTile(w, sx, sy) { const [ox, oy] = this.abOrigin(w), mx = sx - ox, my = sy - oy; return [(mx / 32 + my / 16) / 2, (my / 16 - mx / 32) / 2]; },
  // ---- the painted pieces (cached small canvases) ----
  abFloorTile(theme, v, lava) {
    const key = `f:${theme}:${v}:${lava}`; if (this.abCache[key]) return this.abCache[key];
    const c = document.createElement("canvas"); c.width = ABT.TW; c.height = ABT.TH; const p = c.getContext("2d"), rnd = abRng(`${theme}${v}${lava}`);
    p.beginPath(); p.moveTo(32, 0); p.lineTo(64, 16); p.lineTo(32, 32); p.lineTo(0, 16); p.closePath(); p.clip();
    if (lava) { const g = p.createLinearGradient(0, 0, 64, 32); g.addColorStop(0, "#FF8A20"); g.addColorStop(0.5, "#E04010"); g.addColorStop(1, "#FFB030"); p.fillStyle = g; p.fillRect(0, 0, 64, 32); p.strokeStyle = "rgba(255,230,120,0.7)"; p.lineWidth = 1.4; for (let k = 0; k < 4; k++) { p.beginPath(); p.ellipse(rnd.uniform(0, 64), rnd.uniform(0, 32), rnd.uniform(3, 7), rnd.uniform(1.5, 3), 0, Math.PI, 0); p.stroke(); } return (this.abCache[key] = c); }
    const [base, specks] = AB_THEMES[theme]; p.fillStyle = base; p.fillRect(0, 0, 64, 32);
    if (["cathedral", "catacombs", "sanctum", "hell", "abyss"].includes(theme)) { p.strokeStyle = "rgba(0,0,0,0.27)"; p.lineWidth = 1; for (let i = -2; i < 4; i++) { p.beginPath(); p.moveTo(i * 16, 0); p.lineTo(i * 16 + 32, 32); p.moveTo(i * 16 + 32, 0); p.lineTo(i * 16, 32); p.stroke(); } }
    for (let k = 0; k < 60; k++) { p.fillStyle = rnd.choice(specks); p.fillRect(rnd.randint(0, 63), rnd.randint(0, 31), 1, 1); }
    if (theme === "town") { p.strokeStyle = "#7AA64E"; for (let k = 0; k < 10; k++) { const x = rnd.randint(4, 59), y = rnd.randint(4, 29); p.beginPath(); p.moveTo(x, y); p.lineTo(x + rnd.choice([-1, 1]), y - 3); p.stroke(); } }
    return (this.abCache[key] = c);
  },
  abWallBlock(theme, style, v) {
    const key = `w:${theme}:${style}:${v}`; if (this.abCache[key]) return this.abCache[key];
    const TW = ABT.TW, TH = ABT.TH, hh = ABT.WALL_H, w = TW, h = TH + hh, c = document.createElement("canvas"); c.width = w; c.height = h + 10;
    const p = c.getContext("2d"), cx = w / 2, cy = h - TH / 2, rnd = abRng(`${theme}${style}${v}`), poly = (pts) => { p.beginPath(); p.moveTo(...pts[0]); for (const q of pts.slice(1)) p.lineTo(...q); p.closePath(); };
    const out = { canvas: c, ax: cx, ay: cy };
    if (style === "tree") {
      p.fillStyle = "rgba(0,0,0,0.24)"; p.beginPath(); p.ellipse(cx, cy, 22, 9, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#4A3018"; p.fillRect(cx - 3, cy - 30, 6, 30);
      [[-12, -44, 16], [12, -46, 16], [0, -62, 18], [-5, -52, 14]].forEach(([dx, dy, r], i) => { const col = abShade(["#2E5A22", "#3A6A2A", "#467A32", "#365E26"][i], 1 / (1 + rnd.randint(0, 25) / 100)); p.fillStyle = col; p.strokeStyle = abShade(["#2E5A22", "#3A6A2A", "#467A32", "#365E26"][i], 0.7); p.beginPath(); p.ellipse(cx + dx, cy + dy, r, r * 0.86, 0, 0, Math.PI * 2); p.fill(); p.stroke(); });
      return (this.abCache[key] = out);
    }
    if (style === "well") {
      p.strokeStyle = "#3A3A3E"; p.fillStyle = "#8A8A90"; p.beginPath(); p.ellipse(cx, cy - 6, 20, 10, 0, 0, Math.PI * 2); p.fill(); p.stroke(); p.fillStyle = "#1A2A4A"; p.beginPath(); p.ellipse(cx, cy - 8, 14, 6, 0, 0, Math.PI * 2); p.fill();
      p.strokeStyle = "#5A3A1E"; p.lineWidth = 3; p.beginPath(); p.moveTo(cx - 16, cy - 6); p.lineTo(cx - 16, cy - 40); p.moveTo(cx + 16, cy - 6); p.lineTo(cx + 16, cy - 40); p.stroke(); p.fillStyle = "#7A2A1E"; poly([[cx - 22, cy - 38], [cx + 22, cy - 38], [cx, cy - 54]]); p.fill();
      return (this.abCache[key] = out);
    }
    let [, , top, left, right, mortar] = AB_THEMES[theme];
    if (style === "house") [top, left, right, mortar] = ["#8A6A44", "#C8B090", "#A89070", "#5A3A1E"]; else if (style === "church") [top, left, right, mortar] = ["#7A766E", "#9A968E", "#86827A", "#4A4640"];
    p.strokeStyle = mortar; p.lineWidth = 1;
    p.fillStyle = left; poly([[cx - TW / 2, cy], [cx, cy + TH / 2], [cx, cy + TH / 2 - hh], [cx - TW / 2, cy - hh]]); p.fill(); p.stroke();
    p.fillStyle = right; poly([[cx, cy + TH / 2], [cx + TW / 2, cy], [cx + TW / 2, cy - hh], [cx, cy + TH / 2 - hh]]); p.fill(); p.stroke();
    const line = (a, b) => { p.beginPath(); p.moveTo(...a); p.lineTo(...b); p.stroke(); };
    if (style === "house") { for (let i = 1; i < 4; i++) { line([cx - TW / 2, cy - (hh * i) / 4], [cx, cy + TH / 2 - (hh * i) / 4]); line([cx, cy + TH / 2 - (hh * i) / 4], [cx + TW / 2, cy - (hh * i) / 4]); } p.strokeStyle = "#4A2E14"; p.lineWidth = 3; line([cx - TW / 2 + 2, cy - 1], [cx - TW / 2 + 2, cy - hh]); line([cx, cy + TH / 2 - 1], [cx, cy + TH / 2 - hh]); p.lineWidth = 1; }
    else if (theme === "caves") { for (let k = 0; k < 9; k++) { p.fillStyle = abShade(left, 1 / (1 + rnd.randint(5, 35) / 100)); p.beginPath(); p.ellipse(rnd.uniform(cx - 28, cx + 28), rnd.uniform(cy - hh + 4, cy + 4), rnd.uniform(3, 7), rnd.uniform(2, 5), 0, 0, Math.PI * 2); p.fill(); } }
    else {
      const rows = 6; for (let i = 1; i < rows; i++) { const y = (hh * i) / rows; line([cx - TW / 2, cy - y], [cx, cy + TH / 2 - y]); line([cx, cy + TH / 2 - y], [cx + TW / 2, cy - y]); const off = i % 2 ? 8 : 0; for (let k = 1; k < 3; k++) { const t = (k * 11 + off) / 32; line([cx - TW / 2 + t * 32, cy + t * 16 - y], [cx - TW / 2 + t * 32, cy + t * 16 - y + hh / rows]); line([cx + t * 32, cy + TH / 2 - t * 16 - y], [cx + t * 32, cy + TH / 2 - t * 16 - y + hh / rows]); } }
      if (theme === "catacombs" && rnd.random() < 0.3) { p.fillStyle = "#1A140E"; p.beginPath(); p.ellipse(cx - 16, cy - hh / 2 + 6, 6, 7, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#E0D8C0"; p.beginPath(); p.ellipse(cx - 16, cy - hh / 2 + 7, 3.5, 4, 0, 0, Math.PI * 2); p.fill(); }   // (a skull in its niche)
      if (["hell", "sanctum", "abyss"].includes(theme) && rnd.random() < 0.5) { p.strokeStyle = theme !== "abyss" ? "rgba(255,90,30,0.8)" : "rgba(190,90,255,0.8)"; p.lineWidth = 1.4; let x = rnd.uniform(cx - 26, cx + 26), y = cy - hh + 6; p.beginPath(); p.moveTo(x, y); for (let i = 0; i < 5; i++) { x += rnd.uniform(-5, 5); y += hh / 6; p.lineTo(x, y); } p.stroke(); p.lineWidth = 1; }   // (glowing cracks)
      if (style === "church" && rnd.random() < 0.6) { p.fillStyle = "#30406A"; p.beginPath(); p.roundRect ? p.roundRect(cx - 22, cy - hh + 12, 9, 22, 4) : p.rect(cx - 22, cy - hh + 12, 9, 22); p.fill(); }
    }
    p.strokeStyle = mortar; const topPoly = [[cx - TW / 2, cy - hh], [cx, cy + TH / 2 - hh], [cx + TW / 2, cy - hh], [cx, cy - TH / 2 - hh]];
    p.fillStyle = top; poly(topPoly); p.fill(); p.stroke();
    if (style === "house" || style === "church") { const roof = style === "house" ? "#8A2E20" : "#44444E"; p.fillStyle = roof; p.strokeStyle = abShade(roof, 0.6); poly(topPoly); p.fill(); p.stroke(); p.strokeStyle = abShade(roof, 0.75); for (let i = 1; i < 4; i++) { const t = i / 4; line([cx - TW / 2 + (t * TW) / 2, cy - hh - (t * TH) / 2], [cx + (t * TW) / 2, cy - hh + TH / 2 - (t * TH) / 2]); } }
    return (this.abCache[key] = out);
  },
  abDecor(p, kind, rnd) {
    const ell = (x, y, rx, ry) => { p.beginPath(); p.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); p.fill(); };
    if (kind === "blood") { p.fillStyle = "rgba(110,10,10,0.67)"; for (let k = 0; k < 3; k++) ell(rnd.uniform(-10, 10), rnd.uniform(-4, 4), rnd.uniform(4, 9), rnd.uniform(2, 4)); }
    else if (kind === "bones" || kind === "skulls") { p.strokeStyle = "#D8D0B8"; p.lineWidth = 2; p.lineCap = "round"; for (let k = 0; k < 2; k++) { const x = rnd.uniform(-12, 8), y = rnd.uniform(-5, 3); p.beginPath(); p.moveTo(x, y); p.lineTo(x + rnd.uniform(6, 12), y + rnd.uniform(-3, 3)); p.stroke(); } if (kind === "skulls" || rnd.random() < 0.4) { p.fillStyle = "#E0D8C0"; ell(4, -3, 4, 3.5); p.fillStyle = "#201810"; ell(3, -3.5, 1, 1); ell(5.5, -3.5, 1, 1); } p.lineCap = "butt"; p.lineWidth = 1; }
    else if (kind === "rug") { p.fillStyle = "rgba(110,24,24,0.8)"; p.strokeStyle = "#C8A040"; p.beginPath(); p.moveTo(0, -11); p.lineTo(22, 0); p.lineTo(0, 11); p.lineTo(-22, 0); p.closePath(); p.fill(); p.stroke(); }
    else if (kind === "cracks") { p.strokeStyle = "rgba(0,0,0,0.43)"; p.beginPath(); p.moveTo(-14, 2); p.lineTo(-6, -2); p.lineTo(0, 1); p.lineTo(8, -3); p.lineTo(14, 0); p.stroke(); }
    else if (kind === "rocks") { for (let k = 0; k < 3; k++) { p.fillStyle = abShade("#5A4A3A", 1 / (1 + rnd.randint(0, 40) / 100)); ell(rnd.uniform(-12, 12), rnd.uniform(-5, 5), rnd.uniform(2, 4), rnd.uniform(1.5, 3)); } }
    else if (kind === "path") { p.fillStyle = "rgba(140,110,70,0.78)"; p.beginPath(); p.moveTo(0, -16); p.lineTo(32, 0); p.lineTo(0, 16); p.lineTo(-32, 0); p.closePath(); p.fill(); }
    else if (kind === "flowers") { for (let k = 0; k < 5; k++) { p.fillStyle = rnd.choice(["#F0E060", "#F080B0", "#FFFFFF", "#A080F0"]); ell(rnd.uniform(-14, 14), rnd.uniform(-6, 6), 1.8, 1.4); } }
    else if (kind === "grasstuft") { p.strokeStyle = "#3E6A28"; for (let k = 0; k < 6; k++) { const x = rnd.uniform(-8, 8); p.beginPath(); p.moveTo(x, 2); p.lineTo(x + rnd.uniform(-3, 3), -6); p.stroke(); } }
    else if (kind === "stone") { p.fillStyle = "#8A8A90"; p.strokeStyle = "#5A5A5E"; p.beginPath(); p.ellipse(rnd.uniform(-8, 8), 0, 5, 3, 0, 0, Math.PI * 2); p.fill(); p.stroke(); }
  },
  abBox(p, cx, cy, hw, hh, height, top, left, right) {
    const poly = (pts, f) => { p.fillStyle = f; p.beginPath(); p.moveTo(...pts[0]); for (const q of pts.slice(1)) p.lineTo(...q); p.closePath(); p.fill(); p.stroke(); };
    p.strokeStyle = "rgba(0,0,0,0.47)"; p.lineWidth = 1;
    poly([[cx - hw, cy], [cx, cy + hh], [cx, cy + hh - height], [cx - hw, cy - height]], left); poly([[cx, cy + hh], [cx + hw, cy], [cx + hw, cy - height], [cx, cy + hh - height]], right); poly([[cx - hw, cy - height], [cx, cy + hh - height], [cx + hw, cy - height], [cx, cy - hh - height]], top);
  },
  abObject(p, kind, t, opened, colour) {
    const ell = (x, y, rx, ry) => { p.beginPath(); p.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); p.fill(); }, poly = (pts) => { p.beginPath(); p.moveTo(...pts[0]); for (const q of pts.slice(1)) p.lineTo(...q); p.closePath(); };
    p.lineWidth = 1;
    if (kind === "stairs_down") { p.strokeStyle = "#1A1410"; p.fillStyle = "#0A0806"; poly([[0, -13], [26, 0], [0, 13], [-26, 0]]); p.fill(); p.stroke(); for (let i = 0; i < 4; i++) { p.fillStyle = abShade("#6A625A", 1 / (1 + i * 0.3)); poly([[-18 + i * 5, -2 + i * 3], [-2 + i * 5, -10 + i * 3], [2 + i * 5, -8 + i * 3], [-14 + i * 5, i * 3]]); p.fill(); p.stroke(); } }
    else if (kind === "stairs_up") { for (let i = 0; i < 4; i++) { p.strokeStyle = "#2A2824"; p.fillStyle = abShade("#8A8478", 1 / (1 + (3 - i) * 0.15)); poly([[-20 + i * 6, 4 - i * 6], [i * 6, -6 - i * 6], [6 + i * 6, -3 - i * 6], [-14 + i * 6, 7 - i * 6]]); p.fill(); p.stroke(); } }
    else if (kind === "chest") { this.abBox(p, 0, 0, 13, 7, 12, "#9A6A30", "#7A5020", "#6A4418"); if (opened) { p.strokeStyle = "#3A2410"; p.fillStyle = "#1A1008"; poly([[-13, -12], [0, -5], [13, -12], [0, -19]]); p.fill(); p.stroke(); p.fillStyle = "#9A6A30"; poly([[-13, -12], [0, -19], [0, -32], [-13, -25]]); p.fill(); p.stroke(); } else { p.strokeStyle = "#E8C040"; p.lineWidth = 1.5; p.beginPath(); p.moveTo(-13, -8); p.lineTo(0, -1); p.lineTo(13, -8); p.stroke(); p.fillStyle = "#F8D040"; p.fillRect(-2, -6, 4, 4); } }
    else if (kind === "barrel") {
      if (opened) { p.strokeStyle = "#3A2410"; p.lineWidth = 2; for (let i = 0; i < 5; i++) { const a = i * 1.3; p.beginPath(); p.moveTo(Math.cos(a) * 4, Math.sin(a) * 2); p.lineTo(Math.cos(a) * 12, Math.sin(a) * 6); p.stroke(); } return; }
      p.strokeStyle = "#3A2410"; p.fillStyle = "#7A5230"; p.beginPath(); p.roundRect ? p.roundRect(-9, -24, 18, 25, 5) : p.rect(-9, -24, 18, 25); p.fill(); p.stroke(); p.fillStyle = "#9A7048"; ell(0, -23, 9, 4); p.strokeStyle = "#404048"; p.lineWidth = 1.6; p.beginPath(); p.moveTo(-9, -16); p.lineTo(9, -16); p.moveTo(-9, -6); p.lineTo(9, -6); p.stroke();
    } else if (kind === "shrine") {
      this.abBox(p, 0, 0, 14, 7, 14, "#8A8A90", "#6A6A70", "#5A5A60");
      if (!opened) { const g = p.createRadialGradient(0, -26, 0, 0, -26, 16); g.addColorStop(0, colour || "#60C0FF"); g.addColorStop(1, "rgba(0,0,0,0)"); p.fillStyle = g; ell(0, -26, 16, 16); p.fillStyle = colour || "#60C0FF"; poly([[0, -34 + Math.sin(t * 3) * 2], [5, -26], [0, -18], [-5, -26]]); p.fill(); }
    } else if (kind === "portal" || kind === "red_portal") {
      const [c1, c2] = kind === "portal" ? ["#80C8FF", "#2050C0"] : ["#FF8080", "#A01010"], g = p.createRadialGradient(0, -28, 0, 0, -28, 30);
      g.addColorStop(0, c1); g.addColorStop(0.7, c2); g.addColorStop(1, "rgba(0,0,0,0)"); p.fillStyle = g; ell(0, -28, 16, 28);
      p.strokeStyle = "rgba(255,255,255,0.63)"; p.lineWidth = 1.5; for (let i = 0; i < 3; i++) { const r = 4 + ((t * 18 + i * 7) % 14); p.beginPath(); p.ellipse(0, -28, r * 0.6, r, 0, 0, Math.PI * 2); p.stroke(); }
    } else if (kind === "waystone") {
      p.strokeStyle = "#2A2A30"; p.fillStyle = "#6A6A74"; poly([[-9, 0], [-7, -40], [0, -48], [7, -40], [9, 0]]); p.fill(); p.stroke();
      p.strokeStyle = `rgba(120,200,255,${(140 + 80 * Math.sin(t * 2)) / 255})`; p.lineWidth = 2; p.beginPath(); p.moveTo(0, -38); p.lineTo(0, -12); p.moveTo(-4, -30); p.lineTo(4, -22); p.moveTo(4, -30); p.lineTo(-4, -22); p.stroke();
    } else if (kind === "gold") { p.strokeStyle = "#8A6010"; p.fillStyle = "#F8D040"; for (const [dx, dy] of [[-4, 0], [3, -1], [0, -3], [-1, 2], [4, 2]]) { p.beginPath(); p.ellipse(dx, dy - 2, 3.5, 2, 0, 0, Math.PI * 2); p.fill(); p.stroke(); } }
  },
  // a person or a monster, feet on (0, 0), facing down-right ('front') or up-right ('back')
  abFigure(p, look, pose, phase, back, hurt, equip) {
    const spec = Object.assign({}, AB_LOOKS[look] || AB_LOOKS.zombie, equip || {}), s = spec.size || 1;
    p.save(); p.scale(s, s);
    const ell = (x, y, rx, ry) => { p.beginPath(); p.ellipse(x, y, Math.abs(rx), Math.abs(ry), 0, 0, Math.PI * 2); p.fill(); }, line = (a, b) => { p.beginPath(); p.moveTo(...a); p.lineTo(...b); p.stroke(); }, poly = (pts) => { p.beginPath(); p.moveTo(...pts[0]); for (const q of pts.slice(1)) p.lineTo(...q); p.closePath(); };
    if (pose === "dead") { p.fillStyle = "rgba(80,10,10,0.6)"; ell(2, 1, 16, 6); p.fillStyle = abShade(spec.body || spec.skin, 0.83); p.strokeStyle = "rgba(0,0,0,0.55)"; p.beginPath(); p.roundRect ? p.roundRect(-12, -6, 22, 8, 3) : p.rect(-12, -6, 22, 8); p.fill(); p.stroke(); p.fillStyle = abShade(spec.skin, 0.87); ell(13, -3, 5, 4.5); p.restore(); return; }
    if (spec.ghost) p.globalAlpha *= 0.55;
    p.fillStyle = "rgba(0,0,0,0.31)"; ell(0, 0, 14, 5);
    const walk = pose === "walk", swing = Math.sin(phase * 2) * (walk ? 9 : 0), bob = walk ? Math.abs(Math.sin(phase * 2)) * 1.5 : 0, hunch = spec.hunch ? 4 : 0, hulk = spec.hulk, bones = spec.bones;
    const skin = hurt > 0 ? abShade(spec.skin, 1.5) : spec.skin, body = spec.body, trim = spec.trim, legs = spec.legs, tw = hulk ? 20 : 14, top = -46 - (hulk ? 6 : 0) + bob, hip = -24 + bob;
    const leg = (dx, ang, far) => { const c = abShade(legs || spec.skin, far ? 0.8 : 1); p.strokeStyle = c; p.lineWidth = hulk ? 6 : bones ? 3 : 5; p.lineCap = "round"; const foot = [dx + ang * 0.5, -1]; line([dx, hip], foot); p.strokeStyle = abShade(c.startsWith("#") ? c : "#555555", 0.7); p.lineWidth = bones ? 3 : 4; line(foot, [foot[0] + 3, foot[1]]); };
    if (spec.tail) { p.strokeStyle = abShade(spec.skin, 0.83); p.lineWidth = 4; p.lineCap = "round"; p.beginPath(); p.moveTo(-6, hip); p.bezierCurveTo(-22, hip + 6, -26, hip - 14 + Math.sin(phase) * 4, -18, hip - 24); p.stroke(); }
    if (spec.wings) { const flap = Math.sin(phase * 1.5) * 6, c = abShade(spec.skin, 0.66); p.fillStyle = c; p.strokeStyle = abShade(spec.skin, 0.45); p.lineWidth = 1; for (const sg of [-1, 1]) { poly([[0, top + 6], [sg * 26, top - 14 - flap], [sg * 30, top + 4], [sg * 18, top + 2], [sg * 20, top + 14]]); p.fill(); p.stroke(); } }
    if (spec.cape && !back) { p.fillStyle = abShade(spec.cape, 0.83); poly([[-tw / 2 - 1, top + 2], [tw / 2, top + 2], [tw / 2 - 2, hip + 14], [-tw / 2 - 5, hip + 16]]); p.fill(); }
    leg(-4, -swing, true); leg(4, swing, false);
    p.lineCap = "butt";
    if (bones) { p.strokeStyle = skin; p.lineWidth = 2.5; p.lineCap = "round"; line([0, top + hunch], [0, hip]); for (let i = 0; i < 4; i++) { const y = top + 4 + i * 5; line([-6, y], [6, y]); } line([-5, hip], [5, hip]); }
    else {
      const g = p.createLinearGradient(-tw / 2, 0, tw / 2, 0); g.addColorStop(0, abShade(body, 0.77)); g.addColorStop(0.5, body); g.addColorStop(1, abShade(body, 0.87));
      p.fillStyle = g; p.strokeStyle = "rgba(20,14,10,0.78)"; p.lineWidth = 1; const robe = spec.robe, bottom = robe ? -2 : hip + 2;
      poly([[-tw / 2 + hunch, top + hunch], [tw / 2 + hunch, top + hunch], [tw / 2 - 1 + (robe ? 4 : 0), bottom], [-tw / 2 + 1 - (robe ? 4 : 0), bottom]]); p.fill(); p.stroke();
      p.strokeStyle = trim; p.lineWidth = 2; line([-tw / 2 + 2, hip - 2], [tw / 2 - 2, hip - 2]);
      if (spec.apron) { p.fillStyle = "#5A3A1E"; p.fillRect(-tw / 2 + 3, top + 10, tw - 6, hip - top - 4); }
      if (spec.glow) { p.strokeStyle = "rgba(255,140,40,0.82)"; p.lineWidth = 1.5; line([-4, top + 6], [2, top + 14]); line([2, top + 14], [-1, hip - 4]); }
      if (spec.spikes) { p.strokeStyle = "#E8D8B0"; p.lineWidth = 2; for (let i = 0; i < 4; i++) { const y = top + 3 + i * 6; line([-tw / 2 + 1, y], [-tw / 2 - 6, y - 4]); } }
    }
    const attack = pose === "attack", cast = pose === "cast", armC = bones ? skin : body ? abShade(body, 0.9) : skin;
    const shB = [-tw / 2 + hunch, top + 3 + hunch], shF = [tw / 2 + hunch, top + 3 + hunch]; let hB, hF;
    if (cast) { hB = [shB[0] - 4, shB[1] - 16]; hF = [shF[0] + 6, shF[1] - 18]; }
    else if (attack) { const reach = Math.sin(Math.min(1, phase) * Math.PI); hB = [shB[0] + 2, shB[1] + 16]; hF = [shF[0] + 6 + 10 * reach, shF[1] + 4 - 14 * (1 - reach)]; }
    else { hB = [shB[0] - 2 + swing * 0.3, shB[1] + 18]; hF = spec.hunch ? [shF[0] + 12, shF[1] + 6] : [shF[0] + 2 - swing * 0.3, shF[1] + 18]; }
    const wArm = hulk ? 6 : bones ? 2.5 : 4.5;
    p.strokeStyle = abShade(armC, 0.87); p.lineWidth = wArm; p.lineCap = "round"; line(shB, hB);
    if (spec.shield) { p.fillStyle = spec.shield_colour || "#6A4A2A"; p.strokeStyle = spec.trim || "#C8A040"; p.lineWidth = 1.5; p.beginPath(); p.ellipse(hB[0] - 1, hB[1], 7, 9, 0, 0, Math.PI * 2); p.fill(); p.stroke(); }
    if (spec.weapon) this.abWeapon(p, spec.weapon, hF, attack, spec);
    p.strokeStyle = armC; p.lineWidth = wArm; line(shF, hF); p.fillStyle = skin; ell(hF[0], hF[1], 2.4, 2.4); p.lineCap = "butt";
    if (cast) { const g = p.createRadialGradient(hF[0], hF[1] - 4, 0, hF[0], hF[1] - 4, 12); g.addColorStop(0, "rgba(255,220,120,0.86)"); g.addColorStop(1, "rgba(255,120,40,0)"); p.fillStyle = g; ell(hF[0], hF[1] - 4, 12, 12); }
    this.abHead(p, spec, [2 + hunch, top - 8 + hunch], back);
    p.restore();
  },
  abWeapon(p, kind, hand, attack, spec) {
    const colour = spec.weapon_colour || "#C8CCD4", line = (a, b) => { p.beginPath(); p.moveTo(...a); p.lineTo(...b); p.stroke(); }; p.lineCap = "round";
    if (kind === "sword" || kind === "dagger") { const n = kind === "sword" ? 22 : 11, tip = attack ? [hand[0] + n, hand[1] - n * 0.5] : [hand[0] + 4, hand[1] - n]; p.strokeStyle = colour; p.lineWidth = kind === "sword" ? 3 : 2; line(hand, tip); p.strokeStyle = "#8A6A30"; p.lineWidth = 2.5; line([hand[0] - 4, hand[1] + 1], [hand[0] + 4, hand[1] - 1]); }
    else if (["axe", "hammer", "mace"].includes(kind)) { const tip = attack ? [hand[0] + 16, hand[1] - 8] : [hand[0] + 2, hand[1] - 18]; p.strokeStyle = "#6A4A2A"; p.lineWidth = 2.5; line(hand, tip); p.fillStyle = colour; p.strokeStyle = "rgba(0,0,0,0.47)"; p.lineWidth = 1; if (kind === "axe") { p.beginPath(); p.moveTo(...tip); p.lineTo(tip[0] + 7, tip[1] - 5); p.lineTo(tip[0] + 8, tip[1] + 6); p.lineTo(tip[0] + 1, tip[1] + 4); p.closePath(); p.fill(); p.stroke(); } else p.fillRect(tip[0] - 4, tip[1] - 3, 8, 6); }
    else if (kind === "spear") { const tip = attack ? [hand[0] + 22, hand[1] - 6] : [hand[0] + 2, hand[1] - 26]; p.strokeStyle = "#6A4A2A"; p.lineWidth = 2; line(attack ? [hand[0] - 8, hand[1] + 3] : [hand[0], hand[1] + 10], tip); p.fillStyle = colour; p.fillRect(tip[0] - 1.5, tip[1] - 1.5, 3, 3); }
    else if (kind === "bow") { p.strokeStyle = "#7A5230"; p.lineWidth = 2.5; p.beginPath(); p.ellipse(hand[0] + 2, hand[1], 6, 16, 0, -Math.PI * 0.45, Math.PI * 0.45); p.stroke(); p.strokeStyle = "rgba(230,230,230,0.7)"; p.lineWidth = 0.8; line([hand[0] + 1, hand[1] - 15], [hand[0] + 1, hand[1] + 15]); }
    else if (kind === "staff") { p.strokeStyle = "#6A4A2A"; p.lineWidth = 3; line([hand[0] - 2, hand[1] + 14], [hand[0] + 2, hand[1] - 26]); const g = p.createRadialGradient(hand[0] + 2, hand[1] - 28, 0, hand[0] + 2, hand[1] - 28, 6); g.addColorStop(0, spec.orb || "#A0E0FF"); g.addColorStop(1, "rgba(80,140,255,0)"); p.fillStyle = g; p.beginPath(); p.arc(hand[0] + 2, hand[1] - 28, 6, 0, Math.PI * 2); p.fill(); }
    else if (kind === "cane") { p.strokeStyle = "#6A4A2A"; p.lineWidth = 2.5; line(hand, [hand[0] + 3, hand[1] + 22]); }
    p.lineCap = "butt";
  },
  abHead(p, spec, c, back) {
    const kind = spec.head || "human", skin = spec.skin, big = spec.hulk ? 1.25 : 1, ell = (x, y, rx, ry) => { p.beginPath(); p.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2); p.fill(); p.stroke(); };
    let r = 6.5 * big; p.strokeStyle = "rgba(20,14,10,0.78)"; p.lineWidth = 1;
    if (kind === "skull") { p.fillStyle = skin; ell(c[0], c[1], r, r); if (!back) { p.fillStyle = "#1A1410"; p.beginPath(); p.ellipse(c[0] - 1, c[1] - 1, 1.6, 1.8, 0, 0, Math.PI * 2); p.ellipse(c[0] + 3, c[1] - 1, 1.6, 1.8, 0, 0, Math.PI * 2); p.fill(); p.fillRect(c[0] - 1, c[1] + 3, 4, 2); } return; }
    if (kind === "hood") { p.fillStyle = abShade(spec.body, 0.83); ell(c[0], c[1], r + 1.5, r + 1.5); if (!back) { p.fillStyle = abShade(skin, spec.ghost ? 0.7 : 0.9); ell(c[0] + 2, c[1] + 1, r - 2.5, r - 2); } return; }
    p.fillStyle = skin; ell(c[0], c[1], r, r);
    if (kind === "helm") { p.fillStyle = spec.helm_colour || "#9A9AA4"; p.beginPath(); p.arc(c[0], c[1], r + 1, Math.PI, 0); p.closePath(); p.fill(); p.stroke(); if (!back) p.fillRect(c[0] + 1, c[1] - 1, 2, 6); }
    else if (kind === "greathelm") { p.fillStyle = spec.body; p.fillRect(c[0] - r, c[1] - r - 1, 2 * r, 2 * r + 2); p.strokeRect(c[0] - r, c[1] - r - 1, 2 * r, 2 * r + 2); if (!back) { p.strokeStyle = "rgba(255,60,30,0.86)"; p.lineWidth = 1.4; p.beginPath(); p.moveTo(c[0] - 1, c[1] - 1); p.lineTo(c[0] + 5, c[1] - 1); p.stroke(); } }
    else if (kind === "wizard") { p.fillStyle = spec.body; p.beginPath(); p.moveTo(c[0] - r - 2, c[1] - 2); p.lineTo(c[0] + r + 2, c[1] - 2); p.lineTo(c[0] - 2, c[1] - r - 14); p.closePath(); p.fill(); p.stroke(); p.strokeStyle = spec.trim; p.lineWidth = 1.5; p.beginPath(); p.moveTo(c[0] - r - 2, c[1] - 2); p.lineTo(c[0] + r + 2, c[1] - 2); p.stroke(); }
    else if (kind === "witch") { p.fillStyle = "#2A1A2E"; p.beginPath(); p.moveTo(c[0] - r - 5, c[1] - 3); p.lineTo(c[0] + r + 5, c[1] - 3); p.lineTo(c[0] + 4, c[1] - r - 16); p.closePath(); p.fill(); p.stroke(); }
    else if (kind === "beard") { p.fillStyle = "#E8E4DC"; p.beginPath(); p.moveTo(c[0] - 2, c[1] + 2); p.lineTo(c[0] + 6, c[1] + 2); p.lineTo(c[0] + 2, c[1] + 13); p.closePath(); p.fill(); p.beginPath(); p.arc(c[0], c[1], r, -Math.PI * 0.85, -Math.PI * 0.15); p.fill(); }
    else if (kind === "bald") { p.fillStyle = "#5A3A20"; p.beginPath(); p.moveTo(c[0] - 1, c[1] + 3); p.lineTo(c[0] + 6, c[1] + 3); p.lineTo(c[0] + 3, c[1] + 8); p.closePath(); p.fill(); }
    else if (kind === "zombie") { if (!back) { p.fillStyle = "#2A0A0A"; p.beginPath(); p.ellipse(c[0] + 3, c[1] + 2, 2, 1.4, 0, 0, Math.PI * 2); p.fill(); } }
    else if (kind === "imp") { p.fillStyle = abShade(skin, 0.83); p.beginPath(); p.moveTo(c[0] - 4, c[1] - 4); p.lineTo(c[0] - 7, c[1] - 12); p.lineTo(c[0] - 1, c[1] - 6); p.closePath(); p.moveTo(c[0] + 3, c[1] - 5); p.lineTo(c[0] + 6, c[1] - 13); p.lineTo(c[0] + 6, c[1] - 4); p.closePath(); p.fill(); }
    else if (kind === "goat") { p.fillStyle = abShade(skin, 0.9); ell(c[0] + 5, c[1] + 2, 5, 3.5); p.strokeStyle = "#D8CCB0"; p.lineWidth = 2.2; p.beginPath(); p.ellipse(c[0] - 3, c[1] - 6, 5, 6, 0, Math.PI * 1.05, Math.PI * 1.95); p.stroke(); }
    else if (kind === "horned" || kind === "diablo") {
      r *= 0.62; p.strokeStyle = "#E8D8B0"; p.lineWidth = 2; p.lineCap = "round";
      p.beginPath(); p.moveTo(c[0] - 3, c[1] - r + 1); p.bezierCurveTo(c[0] - 9, c[1] - r - 6, c[0] - 10, c[1] - r - 12, c[0] - 4, c[1] - r - 16); p.stroke();
      p.beginPath(); p.moveTo(c[0] + 3, c[1] - r + 1); p.bezierCurveTo(c[0] + 9, c[1] - r - 6, c[0] + 10, c[1] - r - 12, c[0] + 5, c[1] - r - 16); p.stroke();
      if (kind === "diablo") { p.lineWidth = 1.6; for (let i = 0; i < 3; i++) { p.beginPath(); p.moveTo(c[0] - 2 + i * 2, c[1] - r); p.lineTo(c[0] - 2 + i * 2, c[1] - r - 6); p.stroke(); } }
      p.lineCap = "butt";
    }
    if (!back && !["hood", "skull", "greathelm"].includes(kind)) { p.fillStyle = ["horned", "diablo", "imp"].includes(kind) ? "#FFE040" : "#202020"; p.beginPath(); p.arc(c[0] + 1.5, c[1] - 0.5, 1.1 * big, 0, Math.PI * 2); p.arc(c[0] + 4.5, c[1] - 0.5, 1.1 * big, 0, Math.PI * 2); p.fill(); }
  },
  abBat(p, phase, hurt) { const flap = Math.sin(phase * 4) * 9, y = -30 + Math.sin(phase * 1.3) * 4, c = hurt ? "#6E5A5A" : "#4A3A3A"; p.fillStyle = "rgba(0,0,0,0.24)"; p.beginPath(); p.ellipse(0, 0, 8, 3, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = c; p.strokeStyle = "#2A2020"; for (const sg of [-1, 1]) { p.beginPath(); p.moveTo(0, y); p.lineTo(sg * 16, y - 6 - flap); p.lineTo(sg * 12, y + 2); p.lineTo(sg * 6, y + 1); p.closePath(); p.fill(); p.stroke(); } p.beginPath(); p.arc(0, y, 4, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FF3030"; p.beginPath(); p.arc(1.5, y - 1, 0.9, 0, Math.PI * 2); p.fill(); },
  abBeast(p, phase, moving, hurt, dead) {
    const c = hurt ? "#9F6F57" : "#6A4A3A"; p.fillStyle = "rgba(0,0,0,0.27)"; p.beginPath(); p.ellipse(0, 0, 16, 5, 0, 0, Math.PI * 2); p.fill();
    if (dead) { p.fillStyle = abShade(c, 0.83); p.beginPath(); p.ellipse(0, -4, 15, 5, 0, 0, Math.PI * 2); p.fill(); return; }
    p.strokeStyle = abShade(c, 0.7); p.lineWidth = 3.5; p.lineCap = "round"; for (const [x, ph] of [[-9, 0], [8, Math.PI]]) { const sw = Math.sin(phase * 2 + ph) * (moving ? 5 : 0); p.beginPath(); p.moveTo(x, -10); p.lineTo(x + sw, -1); p.stroke(); } p.lineCap = "butt";
    p.fillStyle = c; p.strokeStyle = abShade(c, 0.6); p.lineWidth = 1; p.beginPath(); p.ellipse(0, -14, 14, 7, 0, 0, Math.PI * 2); p.fill(); p.stroke();
    p.fillStyle = abShade(c, 0.83); p.beginPath(); p.moveTo(-8, -20); p.lineTo(4, -24); p.lineTo(10, -18); p.lineTo(-6, -16); p.closePath(); p.fill();
    p.fillStyle = c; p.beginPath(); p.ellipse(14, -16, 6, 5, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.moveTo(16, -18); p.lineTo(24, -14); p.lineTo(16, -12); p.closePath(); p.fill(); p.fillStyle = "#FFD040"; p.beginPath(); p.arc(15, -18, 1, 0, Math.PI * 2); p.fill();
  },
  abIcon(it, size = 30) {
    const key = `i:${it.base}:${it.rarity}:${size}`; if (this.abCache[key]) return this.abCache[key];
    const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), k = CM.AB.kind(it), s = size / 30, col = it.rarity === "magic" ? "#B8C8FF" : it.rarity === "rare" ? "#F0E080" : "#C8CCD4";
    p.scale(s, s); p.lineCap = "round";
    const line = (a, b, w, colr) => { p.strokeStyle = colr; p.lineWidth = w; p.beginPath(); p.moveTo(...a); p.lineTo(...b); p.stroke(); };
    if (k === "sword" || k === "dagger") { line([7, 23], [k === "sword" ? 24 : 18, k === "sword" ? 6 : 12], 3, col); line([6, 18], [12, 24], 2.5, "#8A6A30"); }
    else if (k === "axe" || k === "mace") { line([8, 24], [20, 8], 2.5, "#6A4A2A"); p.fillStyle = col; if (k === "axe") { p.beginPath(); p.moveTo(17, 6); p.lineTo(26, 4); p.lineTo(24, 14); p.closePath(); p.fill(); } else p.fillRect(16, 4, 8, 8); }
    else if (k === "bow") { p.strokeStyle = "#7A5230"; p.lineWidth = 2.5; p.beginPath(); p.arc(10, 15, 11, -Math.PI / 2.4, Math.PI / 2.4); p.stroke(); line([14, 5], [14, 25], 0.8, "#E0E0E0"); }
    else if (k === "staff") { line([8, 26], [20, 6], 3, "#6A4A2A"); p.fillStyle = it.rarity === "normal" ? "#A0E0FF" : col; p.beginPath(); p.arc(21, 5, 4, 0, Math.PI * 2); p.fill(); }
    else if (k === "armor") { p.fillStyle = it.base.includes("Plate") ? "#C8CCD8" : it.base.includes("Mail") ? "#9A9AA4" : "#7A5A38"; p.beginPath(); p.moveTo(8, 6); p.lineTo(22, 6); p.lineTo(25, 12); p.lineTo(22, 26); p.lineTo(8, 26); p.lineTo(5, 12); p.closePath(); p.fill(); line([15, 7], [15, 25], 1, "rgba(0,0,0,0.4)"); }
    else if (k === "helm") { p.fillStyle = it.base === "Crown" ? "#E8C040" : "#9A9AA4"; p.beginPath(); p.arc(15, 17, 9, Math.PI, 0); p.fill(); p.fillRect(6, 17, 18, 4); }
    else if (k === "shield") { p.fillStyle = it.base.includes("Buckler") || it.base.includes("Small") ? "#6A4A2A" : "#8A8A94"; p.beginPath(); p.moveTo(6, 6); p.lineTo(24, 6); p.lineTo(23, 16); p.lineTo(15, 26); p.lineTo(7, 16); p.closePath(); p.fill(); p.strokeStyle = "#C8A040"; p.stroke(); }
    else if (k === "ring") { p.strokeStyle = "#E8C040"; p.lineWidth = 3; p.beginPath(); p.arc(15, 17, 6, 0, Math.PI * 2); p.stroke(); p.fillStyle = col === "#C8CCD4" ? "#60C0FF" : col; p.beginPath(); p.arc(15, 10, 3, 0, Math.PI * 2); p.fill(); }
    else if (k === "amulet") { line([8, 6], [15, 16], 1.5, "#E8C040"); line([22, 6], [15, 16], 1.5, "#E8C040"); p.fillStyle = "#C04060"; p.beginPath(); p.arc(15, 19, 5, 0, Math.PI * 2); p.fill(); }
    else if (k === "potion") { const cc = it.base.includes("Rejuvenation") ? "#C060C0" : it.base.includes("Mana") ? "#3050E0" : "#D02020"; p.fillStyle = cc; p.beginPath(); p.arc(15, 19, 7, 0, Math.PI * 2); p.fill(); p.fillRect(12, 6, 6, 8); p.fillStyle = "#C8A878"; p.fillRect(12, 4, 6, 3); if (it.base.includes("Full")) { p.strokeStyle = "#F0D060"; p.lineWidth = 1; p.beginPath(); p.arc(15, 19, 7, 0, Math.PI * 2); p.stroke(); } }
    else if (k === "scroll") { p.fillStyle = "#E8DCB8"; p.fillRect(7, 7, 16, 16); p.fillStyle = it.base.includes("Portal") ? "#4080E0" : "#C06020"; p.fillRect(10, 11, 10, 2); p.fillRect(10, 15, 10, 2); }
    else if (k === "book") { p.fillStyle = "#6A2A2A"; p.fillRect(7, 5, 16, 20); p.fillStyle = "#E8C040"; p.fillRect(9, 7, 2, 16); p.font = "bold 11px Georgia"; p.fillText(it.base.slice(8, 9), 13, 19); }
    return (this.abCache[key] = c);
  },
  // ---- a frame ----
  drawAblo(w) {
    const c = this.abCanvas(), p = c.getContext("2d"), lv = w.level, pl = w.player, now = w.time, W = c.width, H = c.height, vh = H - ABT.PANEL_H;
    this.abHits = []; this.abButtons = [];
    p.setTransform(1, 0, 0, 1, 0, 0); p.fillStyle = "#000"; p.fillRect(0, 0, W, H);
    const bright = (tx, ty) => { if (w.depth === 0) return 1; const d = Math.hypot(tx + 0.5 - pl.x, ty + 0.5 - pl.y), L = pl.light; return d <= L - 2.5 ? 1 : d <= L + 0.5 ? 0.25 + (0.75 * (L + 0.5 - d)) / 3 : 0.18; };
    const lit = (x, y) => w.depth === 0 || Math.hypot(x - pl.x, y - pl.y) <= pl.light + 0.5;
    const ptx = Math.floor(pl.x), pty = Math.floor(pl.y), R = 19, tiles = [];
    for (let ty = pty - R; ty <= pty + R; ty++) for (let tx = ptx - R; tx <= ptx + R; tx++) { if (!lv.inside(tx, ty) || !w.explored.has(`${tx},${ty}`)) continue; const [sx, sy] = this.abToScreen(w, tx + 0.5, ty + 0.5); if (sx > -70 && sx < W + 70 && sy > -40 && sy < vh + 120) tiles.push([tx, ty, sx, sy]); }
    const theme = lv.theme;
    p.save(); p.beginPath(); p.rect(0, 0, W, vh); p.clip();
    for (const [tx, ty, sx, sy] of tiles) {
      const t = lv.grid[ty][tx];
      if (t === CM.AB.WALL) { if (theme === "town" && ["tree", "well"].includes(lv.style[`${tx},${ty}`])) p.drawImage(this.abFloorTile(theme, (tx * 7 + ty * 13) % 3, false), sx - 32, sy - 16); continue; }
      p.globalAlpha = t === CM.AB.LAVA ? 1 : bright(tx, ty); p.drawImage(this.abFloorTile(theme, (tx * 7 + ty * 13) % 3, t === CM.AB.LAVA), sx - 32, sy - 16);
      const dec = lv.decor[`${tx},${ty}`]; if (dec && dec !== "pentagram") { p.save(); p.translate(sx, sy); this.abDecor(p, dec, abRng(tx * 1000 + ty)); p.restore(); }
    }
    p.globalAlpha = 1;
    if (theme === "sanctum") { const [cx0, cy0] = lv.places.diablo, cx = cx0 + 0.5, cy = cy0 + 2.5; p.strokeStyle = "rgba(200,30,20,0.78)"; p.lineWidth = 3; p.beginPath(); for (let i = 0; i <= 5; i++) { const a = -Math.PI / 2 + (i * 4 * Math.PI) / 5, [x, y] = this.abToScreen(w, cx + Math.cos(a) * 4, cy + Math.sin(a) * 4); if (i) p.lineTo(x, y); else p.moveTo(x, y); } p.stroke(); const [sx, sy] = this.abToScreen(w, cx, cy); p.beginPath(); p.ellipse(sx, sy, 4.3 * 32 * 1.41, 4.3 * 16 * 1.41, 0, 0, Math.PI * 2); p.stroke(); }
    // walls, things and creatures, back to front
    const items = [];
    for (const tt of tiles) { const [tx, ty] = tt; if (lv.grid[ty][tx] !== CM.AB.WALL) continue; if (theme !== "town") { let near = false; for (let dy = -1; dy <= 1 && !near; dy++) for (let dx = -1; dx <= 1; dx++) if (lv.floor(tx + dx, ty + dy) || (lv.inside(tx + dx, ty + dy) && lv.grid[ty + dy][tx + dx] === CM.AB.LAVA)) { near = true; break; } if (!near) continue; } items.push([tx + ty + 1, 0, tt]); }
    for (const o of w.objects) if (w.explored.has(`${Math.floor(o.x)},${Math.floor(o.y)}`)) items.push([o.x + o.y - (o.kind.startsWith("stairs") ? 0.3 : 0), 1, o]);
    for (const g of w.ground) if (w.explored.has(`${Math.floor(g.x)},${Math.floor(g.y)}`)) items.push([g.x + g.y - 0.2, 2, g]);
    for (const m of w.monsters) if (w.explored.has(`${Math.floor(m.x)},${Math.floor(m.y)}`) && lit(m.x, m.y)) items.push([m.x + m.y - (m.dead ? 0.5 : 0), 3, m]);
    for (const n of w.npcs) items.push([n.x + n.y, 3, n]);
    items.push([pl.x + pl.y, 3, pl]); for (const ms of w.missiles) items.push([ms.x + ms.y + 0.1, 4, ms]);
    items.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const pd = pl.x + pl.y; this.abHover = this.abThingAt(w, this.abMouse);
    for (const [, kind, thing] of items) {
      if (kind === 0) {
        const [tx, ty, sx, sy] = thing, style = lv.style[`${tx},${ty}`], blk = this.abWallBlock(theme, style, (tx * 3 + ty * 5) % 4); let op = bright(tx, ty);
        if (tx + ty + 1 > pd && Math.abs(tx - ty - (pl.x - pl.y)) < 3.2 && tx + ty + 1 - pd < 4.5 && style !== "tree") op *= 0.32;   // (the walls between you and the eye go see-through)
        else if (theme === "town" && (style === "house" || style === "church") && tx + ty > pd && Math.abs(tx - ty - (pl.x - pl.y)) < 2.5 && tx + ty - pd < 6) op *= 0.4;
        p.globalAlpha = op; p.drawImage(blk.canvas, sx - blk.ax, sy - blk.ay); p.globalAlpha = 1;
      } else if (kind === 1) { const [sx, sy] = this.abToScreen(w, thing.x, thing.y); p.save(); p.translate(sx, sy); this.abObject(p, thing.kind, now, thing.opened, thing.colour); p.restore(); }
      else if (kind === 2) { const [sx, sy] = this.abToScreen(w, thing.x, thing.y); if (!lit(thing.x, thing.y) && w.depth > 0) p.globalAlpha = 0.4; if (thing.item.base === "Gold") { p.save(); p.translate(sx, sy); this.abObject(p, "gold"); p.restore(); } else { p.drawImage(this.abIcon(thing.item, 21), sx - 10, sy - 14); if (thing.item.rarity === "magic" || thing.item.rarity === "rare") { p.fillStyle = thing.item.rarity === "magic" ? "rgba(112,144,255,0.24)" : "rgba(240,224,96,0.24)"; p.beginPath(); p.ellipse(sx, sy - 2, 12, 5, 0, 0, Math.PI * 2); p.fill(); } } p.globalAlpha = 1; }
      else if (kind === 3) this.abActor(p, w, thing);
      else { const [sx, sy0] = this.abToScreen(w, thing.x, thing.y), sy = sy0 - 24; if (thing.kind === "arrow") { const vx = (thing.vx - thing.vy) * 32, vy = (thing.vx + thing.vy) * 16, n = Math.hypot(vx, vy) || 1; p.strokeStyle = "#E8DCC0"; p.lineWidth = 2; p.beginPath(); p.moveTo(sx, sy); p.lineTo(sx - (vx / n) * 14, sy - (vy / n) * 14); p.stroke(); } else { const col = { firebolt: "#FF8020", fireball: "#FF6010", redbolt: "#FF3030" }[thing.kind] || "#FF8020", r = thing.kind === "fireball" ? 14 : 9, g = p.createRadialGradient(sx, sy, 0, sx, sy, r); g.addColorStop(0, "#FFF0B0"); g.addColorStop(0.4, col); g.addColorStop(1, "rgba(255,80,0,0)"); p.fillStyle = g; p.beginPath(); p.arc(sx, sy, r, 0, Math.PI * 2); p.fill(); } }
    }
    this.abEffects(p, w);
    if (w.depth > 0) { const [sx, sy] = this.abToScreen(w, pl.x, pl.y), r = pl.light * 32 * 1.5, g = p.createRadialGradient(sx, sy - 20, 0, sx, sy - 20, r); g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(0.65, "rgba(0,0,0,0.12)"); g.addColorStop(1, "rgba(0,0,0,0.63)"); p.fillStyle = g; p.fillRect(0, 0, W, vh); }
    if (this.abAlt) { for (const g of w.ground) if (w.explored.has(`${Math.floor(g.x)},${Math.floor(g.y)}`) && lit(g.x, g.y)) this.abLabel(p, w, g); } else if (this.abHover && this.abHover.item) this.abLabel(p, w, this.abHover);
    if (this.abHover && this.abHover.isNpc) this.abNameOver(p, ...this.abToScreen(w, this.abHover.x, this.abHover.y - 0), this.abHover.name);
    p.restore();
    this.abTargetBar(p, w); this.abMessages(p, w); this.abPanel(p, w);
    if (this.abPanels.has("map")) this.abAutomap(p, w);
    if (this.abPanels.has("inv")) this.abInventory(p, w);
    if (this.abPanels.has("char")) this.abChar(p, w); else if (this.abPanels.has("spells")) this.abSpellsPanel(p, w); else if (this.abShop) this.abShopPanel(p, w); else if (w.waystoneOpen) this.abWaystone(p, w);
    this.abTooltip(p, w);
    if (this.abHeld) p.drawImage(this.abIcon(this.abHeld, 30), this.abMouse[0] - 15, this.abMouse[1] - 15);
    if (w.dead) { p.fillStyle = "rgba(60,0,0,0.55)"; p.fillRect(0, 0, W, H); p.fillStyle = "#E03030"; p.textAlign = "center"; p.font = "bold 40px Georgia, serif"; p.fillText("You have died", W / 2, H * 0.4); p.fillStyle = "#E8D8B0"; p.font = "16px Georgia, serif"; p.fillText("Click to wake in Haven (half your gold is lost in the dark).", W / 2, H * 0.4 + 34); p.textAlign = "left"; }
    else if (w.wonAt !== null && now - w.wonAt < 8) { p.fillStyle = "#F0C060"; p.textAlign = "center"; p.font = "bold 34px Georgia, serif"; p.fillText("Vorthak the Undying is undone", W / 2, H * 0.3); p.textAlign = "left"; }
  },
  abActor(p, w, a) {
    const [sx, sy] = this.abToScreen(w, a.x, a.y), back = a.facing === 2 || a.facing === 3, mirror = a.facing === 1 || a.facing === 3;
    p.save(); p.translate(sx, sy); if (mirror) p.scale(-1, 1);
    if (a.isPlayer) this.abFigure(p, a.cls, w.dead ? "dead" : a.pose, a.pose !== "attack" ? a.phase : 1 - a.anim / 0.45, back, a.hurt, this.abHeroLook(a));
    else if (a.isNpc) this.abFigure(p, a.look, a.pose, a.phase, back, 0);
    else {
      const pose = a.dead ? "dead" : a.pose;
      if (a.look === "bat") { if (!a.dead) this.abBat(p, a.phase + w.time, a.hurt); }
      else if (a.look === "beast") this.abBeast(p, a.phase, a.pose === "walk", a.hurt, a.dead);
      else { if (a.ai === "stealth" && !a.dead && Math.hypot(a.x - w.player.x, a.y - w.player.y) > 3) p.globalAlpha = 0.25; this.abFigure(p, a.look, pose, pose !== "attack" ? a.phase : 0.6, back, a.hurt, a.looks); }
      p.globalAlpha = 1;
      if (a.champion && !a.dead) { p.globalAlpha = 0.5; p.strokeStyle = "#6080FF"; p.lineWidth = 2; p.beginPath(); p.ellipse(0, 0, 16, 6, 0, 0, Math.PI * 2); p.stroke(); }
      if (a.boss && !a.dead) { const s = (a.looks.size || 1) * (a.kind === "diablo" ? 2 : 1); p.globalAlpha = 0.6; p.strokeStyle = "#F0C040"; p.lineWidth = 2; p.beginPath(); p.ellipse(0, 0, 18 * s, 7 * s, 0, 0, Math.PI * 2); p.stroke(); }
      p.globalAlpha = 1;
    }
    p.restore();
  },
  abHeroLook(pl) {
    const e = pl.equip, look = {}, wpn = e.weapon;
    look.weapon = wpn ? { dagger: "dagger", sword: "sword", axe: "axe", mace: "mace", bow: "bow", staff: "staff" }[CM.AB.kind(wpn)] || null : null;
    look.shield = Boolean(e.shield); if (e.shield) look.shield_colour = e.shield.base.includes("Buckler") || e.shield.base.includes("Small") ? "#6A4A2A" : "#8A8A94";
    if (e.armor) { const b = e.armor.base, col = b.includes("Leather") || b.includes("Quilted") || b.includes("Rags") ? "#7A5A38" : b.includes("Mail") ? "#9A9AA4" : b.includes("Plate") ? "#C8CCD8" : null; if (col) look.body = col; }
    if (e.helm) { look.head = "helm"; look.helm_colour = e.helm.base.includes("Crown") ? "#C8C0A0" : "#9A9AA4"; }
    if (wpn && (wpn.rarity === "magic" || wpn.rarity === "rare")) look.weapon_colour = wpn.rarity === "magic" ? "#B8C8FF" : "#F0E080";
    return look;
  },
  abNameOver(p, x, y, text, colour = "#E8D8B0") { p.font = "bold 11px Tahoma, sans-serif"; const tw = p.measureText(text).width + 10; p.fillStyle = "rgba(0,0,0,0.67)"; p.fillRect(x - tw / 2, y - 66, tw, 15); p.fillStyle = colour; p.textAlign = "center"; p.fillText(text, x, y - 54); p.textAlign = "left"; },
  abGroundName(g) { return g.item.base === "Gold" ? `${g.item.gold} gold` : CM.AB.name(g.item); },
  abLabelRect(w, g) { const [sx, sy] = this.abToScreen(w, g.x, g.y), c = this.$("#ablocanvas").getContext("2d"); c.font = "bold 11px Tahoma, sans-serif"; const tw = c.measureText(this.abGroundName(g)).width + 8; return [sx - tw / 2, sy - 30, tw, 14]; },
  abLabel(p, w, g) { const [x, y, ww, hh] = this.abLabelRect(w, g); p.fillStyle = "rgba(0,0,0,0.7)"; p.fillRect(x, y, ww, hh); p.font = "bold 11px Tahoma, sans-serif"; p.fillStyle = g.item.base === "Gold" ? "#F8D040" : CM.AB.colour(g.item); p.textAlign = "center"; p.fillText(this.abGroundName(g), x + ww / 2, y + 11); p.textAlign = "left"; },
  abEffects(p, w) {
    for (const e of w.effects) {
      const age = (w.time - e.t0) / e.ttl;
      if (e.kind === "text") { const [sx, sy] = this.abToScreen(w, e.x, e.y); p.font = "bold 12px Tahoma, sans-serif"; p.globalAlpha = Math.max(0, 1 - age); p.fillStyle = "#000"; p.fillText(e.text, sx - 9, sy - 62 - age * 22); p.fillStyle = e.colour; p.fillText(e.text, sx - 10, sy - 63 - age * 22); p.globalAlpha = 1; }
      else if (e.kind === "explosion" || e.kind === "flame") { const [sx, sy] = this.abToScreen(w, e.x, e.y), r = (e.r || 0.8) * 40 * (0.4 + age), g = p.createRadialGradient(sx, sy - 12, 0, sx, sy - 12, r); g.addColorStop(0, `rgba(255,240,160,${0.9 * (1 - age)})`); g.addColorStop(0.5, `rgba(255,120,20,${0.78 * (1 - age)})`); g.addColorStop(1, "rgba(120,20,0,0)"); p.fillStyle = g; p.beginPath(); p.ellipse(sx, sy - 12, r, r * 0.75, 0, 0, Math.PI * 2); p.fill(); }
      else if (e.kind === "bolt") { p.globalAlpha = Math.max(0, 1 - age); p.strokeStyle = e.colour; p.lineWidth = 3; p.beginPath(); e.pts.forEach(([x, y], i) => { const [sx, sy] = this.abToScreen(w, x, y); if (i) p.lineTo(sx, sy - 24); else p.moveTo(sx, sy - 24); }); p.stroke(); p.strokeStyle = "#FFFFFF"; p.lineWidth = 1; p.stroke(); p.globalAlpha = 1; }
      else if (e.kind === "nova") { const [sx, sy] = this.abToScreen(w, e.x, e.y), r = e.r * 32 * age * 1.4; p.globalAlpha = Math.max(0, 1 - age); p.strokeStyle = e.colour; p.lineWidth = 6; p.beginPath(); p.ellipse(sx, sy - 10, Math.max(1, r), Math.max(1, r * 0.5), 0, 0, Math.PI * 2); p.stroke(); p.globalAlpha = 1; }
      else if (["heal", "mana", "flash", "level"].includes(e.kind)) { const [sx, sy] = this.abToScreen(w, e.x, e.y), col = { heal: [255, 96, 96], mana: [96, 128, 255], level: [240, 208, 96] }[e.kind] || [200, 200, 255], a = Math.max(0, 0.8 * (1 - age)), g = p.createRadialGradient(sx, sy - 30, 0, sx, sy - 30, 34); g.addColorStop(0, `rgba(${col},${a})`); g.addColorStop(1, `rgba(${col},0)`); p.fillStyle = g; p.beginPath(); p.ellipse(sx, sy - 30, 26, e.kind === "level" ? 44 : 30, 0, 0, Math.PI * 2); p.fill(); }
    }
  },
  abTargetBar(p, w) {
    const h = this.abHover, t = h && h.isMonster ? h : w.player.target && w.player.target.isMonster ? w.player.target : null; if (!t || t.dead) return;
    const W = this.$("#ablocanvas").width, x = W / 2 - 150; p.fillStyle = "rgba(10,6,4,0.8)"; p.strokeStyle = "#6A5030"; p.fillRect(x, 8, 300, 26); p.strokeRect(x, 8, 300, 26); p.fillStyle = "#8A1010"; p.fillRect(x + 2, 10, 296 * Math.max(0, t.hp / t.maxhp), 22);
    p.font = "bold 13px Georgia, serif"; p.fillStyle = t.boss ? "#F0C040" : t.champion ? "#8098FF" : "#E8E0D0"; p.textAlign = "center"; p.fillText(`${t.name}  (level ${t.mlevel})`, W / 2, 26); p.textAlign = "left";
  },
  abMessages(p, w) { const H = this.$("#ablocanvas").height; let y = H - ABT.PANEL_H - 24; p.font = "bold 13px Georgia, serif"; for (const [text, colour, t] of w.messages.slice().reverse()) { const age = w.time - t; if (age > 7) continue; p.globalAlpha = Math.min(1, (7 - age) / 2); p.fillStyle = "#000"; p.fillText(text, 13, y + 1); p.fillStyle = colour; p.fillText(text, 12, y); y -= 18; } p.globalAlpha = 1; },
  abBtn(p, x, y, w, h, text, action, on) { p.fillStyle = on ? "#3A2A18" : "#1A140C"; p.strokeStyle = on ? "#D8B060" : "#6A5A3A"; p.lineWidth = 1; p.fillRect(x, y, w, h); p.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1); p.font = "bold 11px Georgia, serif"; p.fillStyle = "#E8D8B0"; p.textAlign = "center"; p.fillText(text, x + w / 2, y + h / 2 + 4); p.textAlign = "left"; this.abButtons.push([[x, y, w, h], action]); },
  abPanel(p, w) {
    const c = this.$("#ablocanvas"), pl = w.player, W = c.width, H = c.height, top = H - ABT.PANEL_H, g = p.createLinearGradient(0, top, 0, H);
    g.addColorStop(0, "#2A2218"); g.addColorStop(1, "#0E0A06"); p.fillStyle = g; p.fillRect(0, top, W, ABT.PANEL_H); p.strokeStyle = "#D8B060"; p.lineWidth = 2; p.beginPath(); p.moveTo(0, top + 1); p.lineTo(W, top + 1); p.stroke(); p.lineWidth = 1;
    const orb = (cx, cy, r, frac, colour, text) => { p.strokeStyle = "#6A5030"; p.lineWidth = 3; p.fillStyle = "#0A0606"; p.beginPath(); p.arc(cx, cy, r, 0, Math.PI * 2); p.fill(); p.stroke(); p.save(); p.beginPath(); p.rect(cx - r, cy + r - 2 * r * Math.max(0, Math.min(1, frac)), 2 * r, 2 * r); p.clip(); const og = p.createRadialGradient(cx - r * 0.3, cy - r * 0.3, 0, cx, cy, r * 1.3); og.addColorStop(0, abShade(colour, 1.6)); og.addColorStop(1, abShade(colour, 0.6)); p.fillStyle = og; p.beginPath(); p.arc(cx, cy, r - 3, 0, Math.PI * 2); p.fill(); p.restore(); p.fillStyle = "rgba(255,255,255,0.16)"; p.beginPath(); p.ellipse(cx - r * 0.35, cy - r * 0.45, r * 0.35, r * 0.2, 0, 0, Math.PI * 2); p.fill(); p.font = "bold 11px Tahoma, sans-serif"; p.fillStyle = "#FFF"; p.textAlign = "center"; p.fillText(text, cx, cy + 4); p.textAlign = "left"; p.lineWidth = 1; };
    orb(70, top + 52, 44, pl.hp / Math.max(1, pl.maxhp), "#C01818", `${Math.floor(pl.hp)}/${pl.maxhp}`); orb(W - 70, top + 52, 44, pl.mana / Math.max(1, pl.maxmana), "#1838C8", `${Math.floor(pl.mana)}/${pl.maxmana}`);
    p.strokeStyle = "#5A4A30"; p.fillStyle = "#100C08"; p.fillRect(140, top + 8, W - 280, 7); p.strokeRect(140, top + 8, W - 280, 7); p.fillStyle = "#C8A040"; p.fillRect(140, top + 8, (W - 280) * Math.min(1, pl.xp / pl.nextLevelXp()), 7);
    const bx = W / 2 - 80; for (let i = 0; i < 4; i++) { const x = bx + i * 40, y = top + 26; p.strokeStyle = "#6A5A3A"; p.fillStyle = "#140E08"; p.fillRect(x, y, 34, 34); p.strokeRect(x, y, 34, 34); if (pl.belt[i]) p.drawImage(this.abIcon(pl.belt[i], 30), x + 2, y + 2); p.font = "bold 9px Tahoma, sans-serif"; p.fillStyle = "#C8B080"; p.fillText(String(i + 1), x + 3, y + 10); this.abHits.push([[x, y, 34, 34], "belt", i]); }
    const sx = W / 2 + 100, sy = top + 22; p.strokeStyle = "#D8B060"; p.lineWidth = 1.5; p.fillStyle = "#1A1008"; p.fillRect(sx, sy, 42, 42); p.strokeRect(sx, sy, 42, 42); p.lineWidth = 1;
    if (pl.activeSpell) this.abSpellIcon(p, sx + 4, sy + 4, 34, pl.activeSpell);
    p.font = "10px Tahoma, sans-serif"; p.fillStyle = "#A89870"; p.textAlign = "center"; p.fillText(pl.activeSpell || "no spell", sx + 21, sy + 54); p.textAlign = "left"; this.abButtons.push([[sx, sy, 42, 42], () => this.abToggle("spells")]);
    [["CHAR", "char"], ["INV", "inv"], ["SPELLS", "spells"], ["MAP", "map"], ["HOME", "home"]].forEach(([text, panel], i) => { const col = i % 3, row = Math.floor(i / 3); this.abBtn(p, 140 + col * 62, top + 26 + row * 30, 58, 24, text, panel === "home" ? () => this.abHome() : () => this.abToggle(panel), this.abPanels.has(panel)); });
    p.font = "bold 12px Georgia, serif"; p.fillStyle = "#D8B060"; p.fillText(CM.AB.THEME_NAMES[w.level.theme] + (w.depth === 0 ? "" : ` - level ${w.depth}`), W / 2 + 150, top + 36);
    p.font = "11px Tahoma, sans-serif"; p.fillStyle = "#C8B890"; p.fillText(`Level ${pl.level} ${pl.cls[0].toUpperCase() + pl.cls.slice(1)}${pl.points ? `  (+${pl.points} points)` : ""}`, W / 2 + 150, top + 54); p.fillText(`Gold: ${pl.gold}`, W / 2 + 150, top + 70);
  },
  abSpellIcon(p, x, y, size, spell) { const col = { Firebolt: "#FF7020", Fireball: "#FF4010", Inferno: "#FF9020", Healing: "#40D060", Lightning: "#A0C8FF", "Chain Lightning": "#C0D8FF", Nova: "#80B0FF", Teleport: "#C080FF", "Town Portal": "#60A0FF" }[spell] || "#FFFFFF", g = p.createRadialGradient(x + size / 2, y + size / 2, 0, x + size / 2, y + size / 2, size / 2); g.addColorStop(0, "#FFFFFF"); g.addColorStop(0.35, col); g.addColorStop(1, abShade(col, 0.33)); p.fillStyle = g; p.fillRect(x, y, size, size); p.font = `bold ${Math.round(size * 0.42)}px Georgia, serif`; p.fillStyle = "rgba(0,0,0,0.67)"; p.textAlign = "center"; p.fillText(spell[0], x + size / 2, y + size * 0.66); p.textAlign = "left"; },
  abFrame(p, x, y, w, h, title) { p.fillStyle = "rgba(14,10,6,0.94)"; p.strokeStyle = "#D8B060"; p.lineWidth = 2; p.fillRect(x, y, w, h); p.strokeRect(x, y, w, h); p.lineWidth = 1; p.font = "bold 15px Georgia, serif"; p.fillStyle = "#D8B060"; p.textAlign = "center"; p.fillText(title, x + w / 2, y + 22); p.textAlign = "left"; },
  abInventory(p, w) {
    const c = this.$("#ablocanvas"), pl = w.player, x0 = c.width - 330, y0 = 8, H = c.height - ABT.PANEL_H - 16; this.abFrame(p, x0, y0, 322, H, "Inventory");
    const slots = { helm: [125, 54, 2, 2], amulet: [195, 60, 1, 1], weapon: [36, 110, 2, 3], armor: [125, 120, 2, 3], shield: [214, 110, 2, 3], ring1: [66, 222, 1, 1], ring2: [214, 222, 1, 1] };
    for (const [slot, [sx, sy, cw, ch]] of Object.entries(slots)) { const x = x0 + sx, y = y0 + sy, ww = cw * 30, hh = ch * 30; p.fillStyle = "#140E08"; p.strokeStyle = "#6A5A3A"; p.fillRect(x, y, ww, hh); p.strokeRect(x, y, ww, hh); const it = pl.equip[slot]; if (it) { p.fillStyle = it.rarity === "magic" ? "rgba(112,144,255,0.18)" : it.rarity === "rare" ? "rgba(240,224,96,0.18)" : "transparent"; p.fillRect(x, y, ww, hh); p.drawImage(this.abIcon(it, 30), x + ww / 2 - 15, y + hh / 2 - 15); } else { p.font = "9px Tahoma, sans-serif"; p.fillStyle = "#5A4A30"; p.textAlign = "center"; p.fillText(slot.replace(/\d/, ""), x + ww / 2, y + hh / 2 + 3); p.textAlign = "left"; } this.abHits.push([[x, y, ww, hh], "equip", slot]); }
    const gx = x0 + 11, gy = y0 + 270; for (let i = 0; i < 40; i++) { const x = gx + (i % 10) * 30, y = gy + Math.floor(i / 10) * 30; p.fillStyle = "#140E08"; p.strokeStyle = "#4A3A26"; p.fillRect(x, y, 29, 29); p.strokeRect(x, y, 29, 29); const it = pl.inv[i]; if (it) { if (it.rarity === "magic" || it.rarity === "rare") { p.fillStyle = it.rarity === "magic" ? "rgba(112,144,255,0.2)" : "rgba(240,224,96,0.2)"; p.fillRect(x, y, 29, 29); } if (it.ident === false) { p.fillStyle = "rgba(200,40,40,0.25)"; p.fillRect(x, y, 29, 29); } p.drawImage(this.abIcon(it, 27), x + 1, y + 1); if ((it.qty || 1) > 1) { p.font = "bold 9px Tahoma, sans-serif"; p.fillStyle = "#FFF"; p.fillText(String(it.qty), x + 2, y + 27); } } this.abHits.push([[x, y, 29, 29], "inv", i]); }
    p.font = "12px Georgia, serif"; p.fillStyle = "#F0D060"; p.fillText(`Gold: ${pl.gold}`, gx, gy + 136);
    p.font = "11px Georgia, serif"; p.fillStyle = "#A89870"; p.fillText("Right-click: use or wear. In the pack when you step home: the party's.", gx, gy + 154);
  },
  abChar(p, w) {
    const pl = w.player, x0 = 8, y0 = 8; this.abFrame(p, x0, y0, 322, 360, "Character"); p.font = "13px Georgia, serif";
    const rows = [["Name", pl.name], ["Class", pl.cls[0].toUpperCase() + pl.cls.slice(1)], ["Level", pl.level], ["Experience", `${Math.floor(pl.xp)} / ${pl.nextLevelXp()}`], ["Life", `${Math.floor(pl.hp)} / ${pl.maxhp}`], ["Mana", `${Math.floor(pl.mana)} / ${pl.maxmana}`], ["Armor class", pl.ac], ["To hit", `${pl.toHit}%`], ["Damage", `${pl.dmg[0]}-${pl.dmg[1]}${pl.elem ? ` +${pl.elem}` : ""}`], ["Block", `${pl.block}%`], ["Resist fire / lightning", `${pl.resFire}% / ${pl.resLight}%`]];
    rows.forEach(([a, b], i) => { p.fillStyle = "#A89870"; p.fillText(a, x0 + 16, y0 + 52 + i * 18); p.fillStyle = "#E8D8B0"; p.fillText(String(b), x0 + 190, y0 + 52 + i * 18); });
    const stats = [["Strength", "str", pl.str_], ["Dexterity", "dex", pl.dex], ["Magic", "mag", pl.mag], ["Vitality", "vit", pl.vit]];
    stats.forEach(([label, key, val], i) => { const y = y0 + 262 + i * 22; p.fillStyle = "#A89870"; p.fillText(label, x0 + 16, y + 12); p.fillStyle = "#E8D8B0"; p.fillText(String(val), x0 + 140, y + 12); if (pl.points > 0) this.abBtn(p, x0 + 190, y, 30, 18, "+", () => { pl.base[key] += 1; pl.points -= 1; pl.recalc(); }); });
    if (pl.points) { p.fillStyle = "#F0C060"; p.fillText(`${pl.points} points to spend`, x0 + 16, y0 + 352); }
  },
  abSpellsPanel(p, w) {
    const pl = w.player, x0 = 8, y0 = 8, names = Object.keys(pl.spells); this.abFrame(p, x0, y0, 322, 80 + names.length * 44, "Spells");
    if (!names.length) { p.font = "13px Georgia, serif"; p.fillStyle = "#A89870"; p.fillText("No spells yet: books are sold by the witch, and found below.", x0 + 14, y0 + 52); return; }
    names.forEach((s, i) => { const y = y0 + 40 + i * 44; this.abSpellIcon(p, x0 + 14, y, 36, s); p.font = "bold 13px Georgia, serif"; p.fillStyle = s === pl.activeSpell ? "#F0C060" : "#E8D8B0"; p.fillText(`${s} (level ${pl.spells[s] + pl.spellBonus})`, x0 + 60, y + 15); p.font = "11px Georgia, serif"; p.fillStyle = "#A89870"; p.fillText(`${CM.AB.SPELLS[s][3]} Mana ${CM.AB.SPELLS[s][0]}`, x0 + 60, y + 31); this.abButtons.push([[x0 + 10, y - 2, 300, 40], () => { pl.activeSpell = s; }]); });
  },
  abShopPanel(p, w) {
    const S = this.abShop, pl = w.player, x0 = 8, y0 = 8, H = this.$("#ablocanvas").height - ABT.PANEL_H - 16, who = S.npc;
    this.abFrame(p, x0, y0, 322, H, who.name); p.font = "12px Georgia, serif"; p.fillStyle = "#A89870";
    if (who.role === "healer") { p.fillText("\"Let me see to those wounds.\"", x0 + 14, y0 + 46); this.abBtn(p, x0 + 14, y0 + 56, 140, 24, "Heal me (free)", () => { w.heal(); this.abSfx("heal"); }); }
    if (who.role === "elder") { p.fillText("\"Bring me what you cannot read.\"", x0 + 14, y0 + 46); this.abBtn(p, x0 + 14, y0 + 56, 200, 24, "Identify everything", () => { w.say(w.identifyAll(), "#E8D8B0"); }); return; }
    const stock = w.shopStock[who.role] || [], start = who.role === "healer" ? 92 : 40, perPage = Math.floor((H - start - 60) / 32), off = Math.min(S.scroll || 0, Math.max(0, stock.length - perPage));
    stock.slice(off, off + perPage).forEach((it, k) => { const i = off + k, y = y0 + start + k * 32, price = CM.AB.buyPrice(it); p.drawImage(this.abIcon(it, 26), x0 + 12, y); p.font = "12px Georgia, serif"; p.fillStyle = CM.AB.colour(it); p.fillText(CM.AB.name(it), x0 + 44, y + 12); p.fillStyle = price > pl.gold ? "#A04040" : "#F0D060"; p.fillText(`${price} gold`, x0 + 44, y + 26); this.abHits.push([[x0 + 8, y - 2, 306, 30], "shop", i]); });
    p.font = "11px Georgia, serif"; p.fillStyle = "#A89870"; p.fillText(`Click to buy (wheel scrolls). Right-click your pack to sell. Gold: ${pl.gold}`, x0 + 12, y0 + H - 14);
  },
  abWaystone(p, w) {
    const x0 = 8, y0 = 8, ds = w.waystoneDepths(); this.abFrame(p, x0, y0, 322, 70 + ds.length * 30, "The Waystone");
    ds.forEach((d, i) => this.abBtn(p, x0 + 20, y0 + 40 + i * 30, 280, 24, `${CM.AB.THEME_NAMES[CM.AB.themeFor(d)]}, level ${d}`, () => { w.waystoneOpen = false; w.enter(d, "up"); this.abSfx("teleport"); }));
  },
  abAutomap(p, w) {
    const c = this.$("#ablocanvas"), lv = w.level, s = 4, cx = c.width / 2, cy = (c.height - ABT.PANEL_H) / 2, pl = w.player;
    p.globalAlpha = 0.85;
    for (const k of w.explored) { const [x, y] = k.split(",").map(Number); if (!lv.inside(x, y)) continue; const t = lv.grid[y][x]; if (t === CM.AB.WALL) { let edge = false; for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) if (lv.floor(x + dx, y + dy)) edge = true; if (!edge) continue; p.fillStyle = "#B8A070"; } else p.fillStyle = t === CM.AB.LAVA ? "#A04010" : "rgba(80,70,50,0.6)"; p.fillRect(cx + (x - y - (pl.x - pl.y)) * s, cy + (x + y - (pl.x + pl.y)) * s * 0.5, s, s * 0.5 + 1); }
    for (const o of w.objects) if (o.kind.startsWith("stairs") || o.kind.includes("portal")) { p.fillStyle = o.kind.includes("portal") ? "#FF6060" : "#60C0FF"; p.fillRect(cx + (o.x - o.y - (pl.x - pl.y)) * s - 2, cy + (o.x + o.y - (pl.x + pl.y)) * s * 0.5 - 2, 5, 5); }
    p.fillStyle = "#FFF"; p.fillRect(cx - 2, cy - 2, 5, 5); p.globalAlpha = 1;
  },
  abTooltip(p, w) {
    const m = this.abMouse, hit = this.abHitAt(m); let it = null;
    if (hit) { const [, kind, key] = hit; it = kind === "inv" ? w.player.inv[key] : kind === "equip" ? w.player.equip[key] : kind === "belt" ? w.player.belt[key] : kind === "shop" ? (w.shopStock[this.abShop.npc.role] || [])[key] : null; }
    if (!it && this.abHover && this.abHover.item && this.abHover.item.base !== "Gold") it = this.abHover.item;
    if (!it) return;
    const lines = CM.AB.tooltip(it, w.player); if (hit && hit[1] === "inv" && this.abShop) lines.push([`Sells for ${it.rarity !== "supply" ? CM.AB.sellPrice(it) : Math.max(1, Math.floor(CM.AB.SUPPLIES[it.base][1] / 4))} gold (right-click)`, "#F0D060"]);
    p.font = "12px Georgia, serif"; const ww = Math.max(...lines.map(([t]) => p.measureText(t).width)) + 16, hh = lines.length * 16 + 10, c = this.$("#ablocanvas"), x = Math.min(c.width - ww - 4, m[0] + 16), y = Math.max(4, Math.min(c.height - hh - 4, m[1] - hh / 2));
    p.fillStyle = "rgba(8,6,4,0.94)"; p.strokeStyle = "#6A5030"; p.fillRect(x, y, ww, hh); p.strokeRect(x, y, ww, hh); p.textAlign = "center"; lines.forEach(([t, col], i) => { p.fillStyle = col; p.fillText(t, x + ww / 2, y + 18 + i * 16); }); p.textAlign = "left";
  },
  // ---- what is under the mouse ----
  abHitAt([mx, my]) { for (const h of (this.abHits || []).slice().reverse()) { const [[x, y, w, hh]] = h; if (mx >= x && mx <= x + w && my >= y && my <= y + hh) return h; } return null; },
  abOverUi([mx, my]) { const c = this.$("#ablocanvas"); if (my > c.height - ABT.PANEL_H) return true; if ((this.abPanels.has("char") || this.abPanels.has("spells") || this.abShop || (this.game.abloWorld && this.game.abloWorld.waystoneOpen)) && mx < 330) return true; if (this.abPanels.has("inv") && mx > c.width - 330) return true; return false; },
  abThingAt(w, [mx, my]) {
    if (this.abOverUi([mx, my])) return null;
    let best = null, bd = 1e9;
    for (const m of w.monsters) { if (m.dead || !w.explored.has(`${Math.floor(m.x)},${Math.floor(m.y)}`) || (w.depth > 0 && Math.hypot(m.x - w.player.x, m.y - w.player.y) > w.player.light + 0.5)) continue; const [sx, sy] = this.abToScreen(w, m.x, m.y), size = (m.looks.size || 1) * (m.kind === "diablo" ? 2 : 1); if (mx >= sx - 14 * size && mx <= sx + 14 * size && my >= sy - 56 * size && my <= sy + 2) { const d = Math.abs(mx - sx) + Math.abs(my - (sy - 26 * size)); if (d < bd) { best = m; bd = d; } } }
    if (best) return best;
    for (const n of w.npcs) { const [sx, sy] = this.abToScreen(w, n.x, n.y); if (mx >= sx - 14 && mx <= sx + 14 && my >= sy - 58 && my <= sy + 2) return n; }
    for (const g of w.ground) { const [sx, sy] = this.abToScreen(w, g.x, g.y); if (mx >= sx - 14 && mx <= sx + 14 && my >= sy - 14 && my <= sy + 4) return g; if (this.abAlt) { const [x, y, ww, hh] = this.abLabelRect(w, g); if (mx >= x && mx <= x + ww && my >= y && my <= y + hh) return g; } }
    for (const o of w.objects) { if (["chest", "barrel", "shrine"].includes(o.kind) && o.opened) continue; const [sx, sy] = this.abToScreen(w, o.x, o.y), tall = o.kind.includes("portal") || o.kind === "waystone"; if (mx >= sx - 18 && mx <= sx + 18 && my >= sy - (tall ? 52 : 30) && my <= sy + 6) return o; }
    return null;
  },
  abToggle(name) { if (this.abPanels.has(name)) this.abPanels.delete(name); else { if (["char", "spells"].includes(name)) { this.abPanels.delete("char"); this.abPanels.delete("spells"); this.abShop = null; } this.abPanels.add(name); } },
  abCloseAll() { const w = this.game.abloWorld; if (this.abHeld && w) { if (!w.player.addItem(this.abHeld)) w.dropItem(this.abHeld); this.abHeld = null; } this.abPanels.clear(); this.abShop = null; if (w) w.waystoneOpen = false; },
  abHome() { const w = this.game.abloWorld; if (!w) return; if (w.depth !== 0) { w.say("The red portal home stands in Haven, by the path south of the well.", "#FF9090"); return; } const portal = w.objects.find((o) => o.kind === "red_portal"); w.interact(portal); },
  abSfx(name, vol = 0.4, rate = 1) { try { CM.audio.play(name, vol, 0, rate); } catch (e) { /* quiet */ } },
  // ---- the mouse and the keys (80-main.js hands them on) ----
  abMouseDown(e, at) {
    const w = this.game.abloWorld; if (!w) return; this.abMouse = at;
    for (const [[x, y, ww, hh], action] of (this.abButtons || []).slice().reverse()) if (at[0] >= x && at[0] <= x + ww && at[1] >= y && at[1] <= y + hh) { if (e.button === 0) action(); this.abSfx("card", 0.25); return; }
    if (w.dead) { if (e.button === 0) { w.revive(); this.abSfx("heal"); } return; }
    const hit = this.abHitAt(at); if (hit) { this.abPanelClick(w, hit[1], hit[2], e.button, e.shiftKey); return; }
    if (this.abOverUi(at)) return;
    if (e.button === 2) { const m = this.abThingAt(w, at); const [x, y] = m && m.isMonster ? [m.x, m.y] : this.abToTile(w, ...at); w.cast(x, y); return; }
    if (e.button !== 0) return;
    if (this.abHeld) { w.dropItem(this.abHeld); this.abHeld = null; return; }
    this.abLeft = true; this.abWalkT = 0.3;
    if (e.shiftKey) { this.abAttackHere(w, at); return; }
    this.abClickWorld(w, at, false);
  },
  abAttackHere(w, at) {
    const p = w.player, [x, y] = this.abToTile(w, ...at), m = this.abThingAt(w, at); let target = m && m.isMonster ? m : null;
    if (!target) target = w.monsters.find((mm) => !mm.dead && Math.hypot(mm.x - x, mm.y - y) < 1.2) || null;
    if (target) w.attack(target); else if (p.ranged && p.cool <= 0) { w.face(x, y); p.cool = p.swing; p.anim = 0.35; p.pose = "attack"; w.missiles.push(new CM.AB.Missile("arrow", p.x, p.y, x - p.x, y - p.y, 13, w.rollDamage(), "player", "phys", 0.4, 1.2)); }
  },
  abClickWorld(w, at, hold) {
    const thing = this.abThingAt(w, at);
    if (thing && thing.isMonster) w.attack(thing);
    else if (thing && !hold) { if (thing.isNpc) { this.abShop = null; } w.interact(thing); }
    else if (!(hold && w.player.target && w.player.target.isMonster)) { const [x, y] = this.abToTile(w, ...at); if (w.level.floor(Math.floor(x), Math.floor(y))) w.moveTo(Math.floor(x), Math.floor(y)); }
  },
  abPanelClick(w, kind, key, button, shift) {
    const pl = w.player;
    if (kind === "belt") { if (button === 2 || !this.abHeld) { w.useBelt(key); return; } if (this.abHeld && CM.AB.kind(this.abHeld) === "potion") { const old = pl.belt[key]; pl.belt[key] = this.abHeld; this.abHeld = old; } return; }
    if (kind === "shop") { const why = w.buy(this.abShop.npc.role, key); if (why) w.say(why, "#FF8080"); else this.abSfx("coin", 0.4); return; }
    if (kind === "inv") {
      if (button === 2) { if (this.abShop && this.abShop.npc.role !== "elder") { const price = w.sell(key); if (price) { w.say(`Sold for ${price} gold.`, "#F0D060"); this.abSfx("coin", 0.4); } return; } w.useItem(key); return; }
      const here = pl.inv[key]; pl.inv[key] = this.abHeld; this.abHeld = here; return;
    }
    if (kind === "equip") {
      if (this.abHeld) { const s = CM.AB.slot(this.abHeld); if (!(s === key || (s === "ring" && key.startsWith("ring")))) { w.say("That doesn't go there.", "#FF8080"); return; } const i = pl.inv.indexOf(null); if (i < 0) { w.say("Your pack is full.", "#FF8080"); return; } pl.inv[i] = this.abHeld; this.abHeld = null; w.equipFrom(i); return; }
      if (button === 2 || shift) { w.unequip(key); return; }
      const it = pl.equip[key]; if (it) { pl.equip[key] = null; this.abHeld = it; pl.recalc(); }
    }
  },
  abKey(e) {
    const w = this.game.abloWorld; if (!w) return false;
    if (e.code === "AltLeft" || e.code === "AltRight") { this.abAlt = true; e.preventDefault(); return true; }
    if (w.dead) return e.code !== "Escape";
    if (/^Digit[1-4]$/.test(e.code)) { w.useBelt(Number(e.code.slice(-1)) - 1); return true; }
    const map = { KeyI: "inv", KeyB: "inv", KeyC: "char", KeyS: "spells", Tab: "map" }; if (map[e.code]) { e.preventDefault(); this.abToggle(map[e.code]); return true; }
    if (e.code === "Space") { e.preventDefault(); this.abCloseAll(); return true; }
    if (e.code === "Escape" && (this.abPanels.size || this.abShop || w.waystoneOpen)) { e.preventDefault(); this.abCloseAll(); return true; }
    return e.code !== "Escape";
  },
});
