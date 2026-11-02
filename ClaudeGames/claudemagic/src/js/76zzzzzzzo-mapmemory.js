"use strict";
// A map that remembers (v42.3, UPGRADE_PLAN_37.md): the parchment keeps the expedition's story in little ink sketches
// in the corner of each square it happened on - crossed swords where a fight was fought, an open box where a chest was
// emptied, a grave-cross where a hero fell, a tent and its fire where the party made camp. Kept with the run
// (ext("mapmarks"), floor by floor, the newest sixty a floor), and drawn on the minimap and the big map alike.
{ const G = CM.Game.prototype, MOST = 60;
  const mark = (g, x, y, kind) => { const fl = g.floor; if (!fl || !g.ext || x === undefined || (g.towerRun && g.towerRun.fl)) return; const M = g.ext("mapmarks"), list = M[fl.number] = M[fl.number] || [];
    if (list.some((m) => m[0] === x && m[1] === y && m[2] === kind)) return; list.push([x, y, kind]); if (list.length > MOST) list.splice(0, list.length - MOST); };
  const sc0 = G.startCombat; G.startCombat = function (key, ...a) { if (typeof key === "string" && this.mode === "explore") { const [x, y] = key.split(",").map(Number); mark(this, x, y, "fight"); } return sc0.call(this, key, ...a); };
  const tr0 = G.trace; G.trace = function (id, x, y, ...a) { if (id === "chest_open") mark(this, x, y, "chest"); return tr0.call(this, id, x, y, ...a); };
  const sm0 = G.setMode; G.setMode = function (mode, ...a) { if (mode === "camp" && this.mode !== "camp" && this.floor && this.floor.number >= 1) mark(this, this.floor.pos[0], this.floor.pos[1], "camp"); return sm0.call(this, mode, ...a); };
  const up = new WeakMap();
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "change" && this.party && this.floor && this.floor.number >= 1) for (const h of this.party) { if (!h) continue; const was = up.get(h), now = h.hp > 0; if (was === true && !now) mark(this, this.floor.pos[0], this.floor.pos[1], "fallen"); up.set(h, now); }
    return em0.call(this, ev, ...a); };
  const INK = "rgba(70,36,12,0.9)";
  const SKETCH = {
    fight: (p, x, y, s) => { p.strokeStyle = "rgba(150,30,20,0.9)"; p.beginPath(); p.moveTo(x - s, y - s); p.lineTo(x + s, y + s); p.moveTo(x + s, y - s); p.lineTo(x - s, y + s); p.moveTo(x - s * 0.9, y + s * 0.3); p.lineTo(x - s * 0.3, y + s * 0.9); p.moveTo(x + s * 0.9, y + s * 0.3); p.lineTo(x + s * 0.3, y + s * 0.9); p.stroke(); },
    chest: (p, x, y, s) => { p.strokeStyle = INK; p.strokeRect(x - s, y - s * 0.3, s * 2, s * 1.2); p.beginPath(); p.moveTo(x - s, y - s * 0.3); p.lineTo(x - s * 0.7, y - s * 1.1); p.lineTo(x + s * 1.2, y - s * 1.0); p.lineTo(x + s, y - s * 0.3); p.stroke(); },
    fallen: (p, x, y, s) => { p.strokeStyle = "rgba(20,14,10,0.95)"; p.beginPath(); p.moveTo(x, y - s * 1.1); p.lineTo(x, y + s); p.moveTo(x - s * 0.6, y - s * 0.4); p.lineTo(x + s * 0.6, y - s * 0.4); p.moveTo(x - s, y + s); p.lineTo(x + s, y + s); p.stroke(); },
    camp: (p, x, y, s) => { p.strokeStyle = INK; p.beginPath(); p.moveTo(x - s, y + s * 0.8); p.lineTo(x - s * 0.1, y - s); p.lineTo(x + s * 0.7, y + s * 0.8); p.closePath(); p.moveTo(x - s * 0.1, y - s); p.lineTo(x - s * 0.1, y + s * 0.8); p.stroke(); p.fillStyle = "rgba(230,110,30,0.95)"; p.beginPath(); p.arc(x + s, y + s * 0.6, Math.max(1, s * 0.35), 0, Math.PI * 2); p.fill(); },
  };
  CM.MAP_SKETCHES = SKETCH;
  const da0 = CM.UI.prototype.drawAutomap; CM.UI.prototype.drawAutomap = function (canvas, ...a) { const out = da0.call(this, canvas, ...a), g = this.game, fl = g.towerRun ? null : g.floor; if (!fl || !g.ext) return out;
    const list = (g.ext("mapmarks") || {})[fl.number]; if (!list || !list.length) return out; const p = canvas.getContext("2d"), cell = canvas.width / fl.grid.length, s = Math.max(1.6, cell * 0.17);
    p.save(); p.lineWidth = Math.max(1, cell * 0.07); p.lineCap = "round";
    for (const [x, y, kind] of list) { const f = SKETCH[kind]; if (f) f(p, (x + 0.5) * cell + cell * 0.22, (y + 0.5) * cell - cell * 0.22, s); }
    p.restore(); return out; };
}
