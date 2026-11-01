"use strict";
// The Wayfarer's Stone, the window's side (v21.1; named apart from the dungeon camps' waystones): the stone drawn (a tall grey standing stone on a round dais, its runes lit
// blue and breathing), and its dialog - every place in the Wood it knows, to go to at a touch, the ones not yet found
// shown dim with how to find them, and from the Wood's stone, the Portal Court. The rules are 69q-waystone.js.
{ const WS = CM.WAYSTONE;
  CM.art.waystone = function (size) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64;
    p.fillStyle = "#6A6A70"; p.beginPath(); p.ellipse(32 * u, 59 * u, 22 * u, 4.5 * u, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#7A7A82"; p.beginPath(); p.ellipse(32 * u, 57 * u, 20 * u, 4 * u, 0, 0, Math.PI * 2); p.fill();
    const g = p.createLinearGradient(20 * u, 0, 44 * u, 0); g.addColorStop(0, "#5A5A62"); g.addColorStop(0.5, "#8A8A92"); g.addColorStop(1, "#4A4A52");
    p.fillStyle = g; p.beginPath(); p.moveTo(22 * u, 57 * u); p.lineTo(23 * u, 12 * u); p.quadraticCurveTo(32 * u, 2 * u, 41 * u, 12 * u); p.lineTo(42 * u, 57 * u); p.closePath(); p.fill();
    p.fillStyle = "rgba(120,200,255,0.95)"; p.font = `${5 * u}px serif`; p.textAlign = "center"; const R = "ᚹᚨᚤᛊᛏᛟᚾᛖ"; for (let i = 0; i < R.length; i++) p.fillText(R[i], 32 * u, (18 + i * 4.8) * u);
    p.strokeStyle = "rgba(120,200,255,0.5)"; p.lineWidth = u; p.beginPath(); p.moveTo(27 * u, 14 * u); p.lineTo(27 * u, 54 * u); p.moveTo(37 * u, 14 * u); p.lineTo(37 * u, 54 * u); p.stroke(); return c; };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); set.index.wayfarer = set.layers.length; set.layers.push(CM.art.waystone(set.size)); return set; }; }
  const ensure = (ui) => { if (ui.$("#dlg-wayfarer")) return; const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-wayfarer";
    d.innerHTML = `<div class="box wsbox"><h2>The Wayfarer's Stone</h2><div id="ws-body"></div><div class="note" id="ws-note"></div><div class="row"><button data-wsclose>Take your hand away</button></div></div>`;
    (ui.root || document.body).appendChild(d); d.querySelector("[data-wsclose]").addEventListener("click", () => ui.closeDialogs()); };
  Object.assign(CM.UI.prototype, {
    openWayfarer() { ensure(this); const g = this.game, known = g.wsKnown(), inWood = g.floor && g.floor.number === -1, box = this.$("#ws-body");
      box.innerHTML = `<p class="lore">Every place the stone knows is cut into it. Lay a hand on a name and it takes you there - the party, whole.</p>
        ${inWood ? `<button class="primary wsgo" data-ws="court"><b>The Portal Court</b><small>the Keep-yard, by the shaft</small></button>` : ""}
        <div class="wsgrid">${WS.PLACES.map(([id, name, , , , what]) => known.includes(id) ? `<button class="wsgo" data-ws="${id}"><b>${this.esc(name)}</b><small>${this.esc(what)}</small></button>` : `<div class="wsgo off"><b>${this.esc(name)}</b><small>not found yet - walk there once</small></div>`).join("")}</div>`;
      box.querySelectorAll("[data-ws]").forEach((b) => b.addEventListener("click", () => { const why = g.wsTravel(b.dataset.ws); this.$("#ws-note").textContent = why || ""; if (!why) { this.closeDialogs(); this.refresh && this.refresh(); } }));
      this.$("#ws-note").textContent = ""; this.openDialog("#dlg-wayfarer"); },
  });
}
