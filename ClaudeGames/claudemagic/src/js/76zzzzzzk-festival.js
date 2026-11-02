"use strict";
// Festivals, kept - the window's side (v36.1): in a festival's week the Square is dressed - strings of bunting across
// it and paper lanterns, lit at dusk - a jig plays coming into town, and "Festival games" among the town's actions opens
// the three games and the favour. Rules: 69zs-festgames.js.
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "fest:bunting": (p) => { p.strokeStyle = "#5A3A1E"; p.lineWidth = 3; p.beginPath(); p.moveTo(0, 40); p.quadraticCurveTo(128, 90, 256, 40); p.stroke(); const C = ["#C83A2A", "#E8C040", "#2A6AC8", "#3A9A4A", "#E8E0D0"];
      for (let i = 0; i < 9; i++) { const x = 14 + i * 28, y = 40 + Math.sin((i + 0.5) / 9 * Math.PI) * 30; p.fillStyle = C[i % C.length]; p.beginPath(); p.moveTo(x - 10, y); p.lineTo(x + 10, y); p.lineTo(x, y + 30); p.closePath(); p.fill(); } },
    "fest:lantern": (p) => { p.strokeStyle = "#3A2A1A"; p.lineWidth = 3; p.beginPath(); p.moveTo(128, 0); p.lineTo(128, 60); p.stroke(); const g = p.createRadialGradient(128, 140, 10, 128, 140, 80); g.addColorStop(0, "#FFE8A0"); g.addColorStop(1, "#E05A20");
      p.fillStyle = g; p.beginPath(); p.ellipse(128, 140, 60, 80, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(120,40,10,0.5)"; p.lineWidth = 2; for (let i = -2; i <= 2; i++) { p.beginPath(); p.ellipse(128, 140, Math.abs(i) * 14, 80, 0, 0, Math.PI * 2); p.stroke(); } },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const SPOTS = [[17, 17], [21, 17], [25, 17], [17, 21], [21, 21], [25, 21], [19, 19], [23, 19]];
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== 0 || !CM.festival || !CM.festival(game) || !CM.renderer || CM.renderer.index["fest:bunting"] === undefined) return out;
      const night = CM.isNight(game) || (CM.hourOf(game) >= 18);
      SPOTS.forEach(([x, y], i) => { out.push({ x, y, layer: i % 2 ? "fest:lantern" : "fest:bunting", w: i % 2 ? 0.35 : 1.4, h: i % 2 ? 0.45 : 0.5, lift: i % 2 ? 1.25 : 1.35, glow: i % 2 && night ? 0.9 : 0.15 }); });
      return out; }; }
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, r) => { if (xl0) xl0(game, fl, out, r); if (!fl || fl.number !== 0 || !CM.festival || !CM.festival(game) || !(CM.isNight(game) || CM.hourOf(game) >= 18)) return;
      SPOTS.filter((_, i) => i % 2).forEach(([x, y]) => { const d = Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]); if (d < 10) out.push({ x: x + 0.5, y: 1.3, z: y + 0.5, reach: 2.4, colour: [1.0, 0.6, 0.25], flicker: true, d }); }); }; }
  // the jig, coming into town in a festival's week
  { const mo0 = CM.music && CM.music.motif; if (mo0) CM.music.motif = function (name) { if (name !== "festival") return mo0.call(this, name); if (!this.enabled || !this._ensure()) return false; const ctx = CM.audio.ctx, at = ctx.currentTime + 0.05;
      [523, 659, 784, 659, 698, 880, 784, 659, 587, 698, 659, 523].forEach((hz, i) => this._osc("triangle", hz, at + i * 0.16, at + i * 0.16 + 0.15, 0.12, 4000, this.master)); return true; }; }
  { const em0 = CM.Game.prototype.emit; CM.Game.prototype.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.floor.number === 0 && CM.festival && CM.festival(this) && !this.replaying && !this.film) { try { CM.music && CM.music.motif && CM.music.motif("festival"); } catch (e) { /* quiet */ } } return em0.call(this, ev, ...a); }; }
  const make = (ui) => { if (ui.$("#dlg-festgames")) return; const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-festgames";
    d.innerHTML = `<div class="box journalbox"><h2>Festival games</h2><p class="lore" id="fest-lore"></p><div class="fgames"></div><div class="note" id="fest-note"></div><div class="end"><button class="close">Close</button></div></div>`;
    ui.$("#dlg-magetower").parentNode.appendChild(d); d.querySelector(".close").addEventListener("click", () => ui.closeDialogs()); };
  CM.UI.prototype.openFestGames = function (note) { make(this); const g = this.game, f = CM.festival(g), F = CM.FESTIVALS[f], R = g.festRecord(), box = this.$("#dlg-festgames .fgames");
    this.$("#fest-lore").textContent = `${F.name[0].toUpperCase() + F.name.slice(1)}: ${F.line || ""}`.trim();
    box.innerHTML = Object.entries(CM.FEST_GAMES).map(([id, G2]) => { const why = g.festWhy(id); return `<div class="recruit" style="grid-template-columns:1fr auto"><div><b>${this.esc(G2.name[0].toUpperCase() + G2.name.slice(1))}</b> <small>${this.esc(G2.what)} (${this.esc(CM.STAT_NAMES[G2.stat])}; the mark is ${CM.FEST_MARK})${R.played[id] ? (R.won[id] ? " - won" : " - lost") : ""}</small></div><button data-fg="${id}" ${why ? `disabled title="${this.esc(why)}"` : ""}>Try it</button></div>`; }).join("")
      + `<p class="small">Each won: ${CM.FEST_GOLD} gold and a little renown. All three: ${this.esc(CM.festFavour(f).name)}, once a year${R.favour ? " - taken" : ""}.</p>`;
    this.$("#fest-note").textContent = note || "";
    for (const b of box.querySelectorAll("[data-fg]")) b.addEventListener("click", () => { const r = g.festPlay(b.dataset.fg); this.openFestGames(r.error || `${r.hero}: ${r.total} - ${r.won ? "won" : "lost"}.`); this.refresh(); });
    this.openDialog("#dlg-festgames"); };
  CM.addAction(["explore"], "Festival games", (ui) => ui.openFestGames(), (ui) => Boolean(ui.game.inTown && ui.game.inTown() && CM.festival(ui.game)));
}
