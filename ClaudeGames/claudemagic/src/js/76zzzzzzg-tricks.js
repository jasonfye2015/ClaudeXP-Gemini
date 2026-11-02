"use strict";
// The hound's tricks - the window's side (v35.1): the farm's window teaches them; a den's mouth in the Wood is drawn -
// a dark hole under the roots, gnawed bones about it - and its way out a slope of earth up to the light; the side
// panel says how many dens the hound has found. Rules: 69zn-tricks.js.
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "den:mouth": (p) => { const g = p.createRadialGradient(128, 130, 10, 128, 130, 110); g.addColorStop(0, "rgba(0,0,0,1)"); g.addColorStop(0.55, "rgba(10,6,4,0.95)"); g.addColorStop(1, "rgba(60,40,24,0)");
      p.fillStyle = "#4A3420"; p.beginPath(); p.ellipse(128, 130, 120, 92, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = g; p.beginPath(); p.ellipse(128, 130, 110, 80, 0, 0, Math.PI * 2); p.fill();
      p.strokeStyle = "#5A3A1E"; p.lineWidth = 9; p.lineCap = "round"; for (const [a, l] of [[3.6, 70], [4.4, 60], [5.2, 80], [0.4, 50]]) { p.beginPath(); p.moveTo(128 + Math.cos(a) * 80, 130 + Math.sin(a) * 60); p.quadraticCurveTo(128 + Math.cos(a) * (80 + l * 0.6), 130 + Math.sin(a) * (60 + l * 0.2), 128 + Math.cos(a + 0.4) * (80 + l), 130 + Math.sin(a + 0.4) * (60 + l * 0.5)); p.stroke(); }
      p.strokeStyle = "#E8DCC0"; p.lineWidth = 7; for (const [x, y, a] of [[40, 210, 0.3], [200, 220, -0.5], [220, 60, 1.2]]) { p.beginPath(); p.moveTo(x, y); p.lineTo(x + Math.cos(a) * 30, y + Math.sin(a) * 30); p.stroke(); } },
    "den:exit": (p) => { const g = p.createLinearGradient(0, 256, 0, 0); g.addColorStop(0, "#3A2A1A"); g.addColorStop(1, "#C8D8A0"); p.fillStyle = g; p.beginPath(); p.moveTo(40, 250); p.lineTo(216, 250); p.lineTo(170, 20); p.lineTo(86, 20); p.closePath(); p.fill();
      p.strokeStyle = "#5A3A1E"; p.lineWidth = 6; for (let i = 0; i < 5; i++) { const y = 220 - i * 44; p.beginPath(); p.moveTo(60 + i * 8, y); p.lineTo(196 - i * 8, y); p.stroke(); } },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { den: (t, x, y) => [{ x, y, layer: "den:mouth", w: 0.95, flat: true }], denexit: (t, x, y) => [{ x, y, layer: "den:exit", w: 0.7, h: 0.9 }] });
  const of0 = CM.UI.prototype.openFarm;
  CM.UI.prototype.openFarm = function (...a) { const out = of0.apply(this, a), g = this.game, more = this.$("#farm-more"); if (!more || !g.tricks || !g.petName("dog")) return out;
    let box = more.querySelector(".tricks"); if (box) box.remove(); box = document.createElement("div"); box.className = "tricks"; box.innerHTML = `<div class="list-title">${this.esc(g.petName("dog"))}'s tricks</div>`;
    for (const [id, T] of Object.entries(CM.TRICKS)) { const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto"; const knows = g.tricks()[id], why = g.teachTrickWhy(id);
      row.innerHTML = `<div><b>${this.esc(T.name)}</b> <small>${this.esc(T.what)}</small></div>`; const b = document.createElement("button"); b.textContent = knows ? "Knows it" : `Teach (${T.gold} gold)`; b.disabled = Boolean(why); if (why && !knows) b.title = why;
      b.addEventListener("click", () => { this.$("#farm-note").textContent = g.teachTrick(id) || "Taught."; this.openFarm(); this.refresh(); }); row.appendChild(b); box.appendChild(row); }
    more.appendChild(box); return out; };
  const rf0 = CM.UI.prototype.refresh;
  CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a), g = this.game, el = this.$ && this.$("#side .pets"); if (el && g && g.dens && g.mode !== "title") { const open = g.dens().filter((d) => !d.cleared); if (open.length && !/den/.test(el.textContent)) el.textContent += ` - ${open.length} den${open.length === 1 ? "" : "s"} found in the Wood`; } return out; };
}
