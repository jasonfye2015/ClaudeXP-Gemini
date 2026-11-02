"use strict";
// Building the town - the window's side (v36.3): "Town works" among the town's actions - the four works, what each
// wants and gives; the bathhouse and the watchtower drawn where they stand, and banners on the walls once the wall is
// repaired. Rules: 69zu-works.js.
{ const S = 256, cv = (w = S, h = S) => { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; };
  const PAINT = {
    "work:bath": (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 248, 120, 8, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#D8CCB0"; p.fillRect(20, 110, 216, 140); p.fillStyle = "#7A3A2A"; p.beginPath(); p.moveTo(8, 116); p.lineTo(128, 50); p.lineTo(248, 116); p.fill();
      p.fillStyle = "#2A3A4A"; p.fillRect(104, 170, 48, 80); for (const x of [40, 184]) { p.fillStyle = "#E8C870"; p.fillRect(x, 150, 32, 30); } p.fillStyle = "#5A3A1E"; p.font = "bold 20px Georgia"; p.textAlign = "center"; p.fillText("BATHS", 128, 104);
      p.strokeStyle = "rgba(240,240,240,0.7)"; p.lineWidth = 6; for (const x of [90, 128, 166]) { p.beginPath(); p.moveTo(x, 50); p.bezierCurveTo(x - 10, 34, x + 10, 22, x, 4); p.stroke(); } },
    "work:watch": (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 250, 70, 6, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#5A3A1E"; p.lineWidth = 12; for (const [a, b] of [[70, 110], [186, 146]]) { p.beginPath(); p.moveTo(a, 250); p.lineTo(b, 60); p.stroke(); }
      p.lineWidth = 6; for (let y = 90; y < 250; y += 40) { p.beginPath(); p.moveTo(70 + (250 - y) * 0.21 * 0 + (y - 60) * -0.21 + 40, y); p.lineTo(186 - (y - 60) * -0.21 - 40, y); p.stroke(); }
      p.fillStyle = "#6A4A2A"; p.fillRect(84, 30, 88, 40); p.fillStyle = "#4A2E16"; p.beginPath(); p.moveTo(76, 32); p.lineTo(128, 0); p.lineTo(180, 32); p.fill(); p.fillStyle = "#C83A2A"; p.fillRect(126, 0, 4, 2); },
    "work:banner": (p) => { p.fillStyle = "#3A2A1A"; p.fillRect(40, 10, 176, 8); const g = p.createLinearGradient(0, 0, 256, 0); g.addColorStop(0, "#7A1A1A"); g.addColorStop(0.5, "#A82A2A"); g.addColorStop(1, "#7A1A1A"); p.fillStyle = g;
      p.beginPath(); p.moveTo(56, 18); p.lineTo(200, 18); p.lineTo(200, 220); p.lineTo(128, 180); p.lineTo(56, 220); p.closePath(); p.fill(); p.fillStyle = "#E8C870"; p.beginPath(); p.arc(128, 90, 34, 0, Math.PI * 2); p.fill(); p.fillStyle = "#7A1A1A"; p.beginPath(); p.arc(128, 90, 22, 0, Math.PI * 2); p.fill(); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { work: (t, x, y) => (t.id === "bath" ? [{ x, y, layer: "work:bath", w: 2.4, h: 2.0, dz: -0.2 }] : [{ x, y, layer: "work:watch", w: 1.6, h: 4.2, dz: -0.1 }]) });
  const BANNERS = [[8, 17, 0], [16, 13, 1], [29, 13, 3], [36, 32, 3], [8, 32, 1]];
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== 0 || !game.worksDone || !game.worksDone("wall") || !CM.renderer || CM.renderer.index["work:banner"] === undefined) return out;
      for (const [x, y] of BANNERS) if (fl.grid[y] && fl.grid[y][x] === 0) out.push({ x, y, layer: "work:banner", w: 0.45, h: 0.8, lift: 0.9, dz: 0, sway: 0.05 }); return out; }; }
  const make = (ui) => { if (ui.$("#dlg-works")) return; const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-works";
    d.innerHTML = `<div class="box journalbox"><h2>The town's works</h2><p class="lore">The reeve keeps a list on a board by the well: what the town would raise, if someone paid for it and brought the timber and stone from the island.</p><div class="wlist"></div><div class="note" id="works-note"></div><div class="end"><button class="close">Close</button></div></div>`;
    ui.$("#dlg-magetower").parentNode.appendChild(d); d.querySelector(".close").addEventListener("click", () => ui.closeDialogs()); };
  CM.UI.prototype.openWorks = function (note) { make(this); const g = this.game, box = this.$("#dlg-works .wlist"), R = CM.TOWNREQ && CM.TOWNREQ.byId;
    box.innerHTML = Object.entries(CM.WORKS).map(([id, Wk]) => { const done = g.worksDone(id), why = g.workWhy(id), mats = Wk.mats.map(([k, n]) => (R && R[k] ? R[k].what(n) : `${n} ${k}`)).join(" and ");
      return `<div class="recruit" style="grid-template-columns:1fr auto"><div><b>${this.esc(Wk.name)}</b> <small>${this.esc(Wk.what)}${done ? ` - raised ${this.esc(g.works()[id].day)}` : ` - ${Wk.gold} gold, ${this.esc(mats)}`}</small></div><button data-work="${id}" ${done || why ? `disabled title="${this.esc(why)}"` : ""}>${done ? "Done" : "Raise it"}</button></div>`; }).join("");
    this.$("#works-note").textContent = note || "";
    for (const b of box.querySelectorAll("[data-work]")) b.addEventListener("click", () => { this.openWorks(g.raiseWork(b.dataset.work) || "Raised."); this.refresh(); });
    this.openDialog("#dlg-works"); };
  CM.addAction(["explore"], "Town works", (ui) => ui.openWorks(), (ui) => Boolean(ui.game.inTown && ui.game.inTown()));
}
