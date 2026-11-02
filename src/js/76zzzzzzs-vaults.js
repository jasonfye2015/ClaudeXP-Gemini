"use strict";
// Secret floors - the window's side (v37.4): the revealed stair (a lifted flagstone over a dark stair), the keeper (a
// pale ghost by the vault's kind, lit by its own cold light), the way back up; and the vault's name on the side panel.
// Rules: 69zza-vaults.js.
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "vault:stair": (p) => { p.fillStyle = "#1A1410"; p.fillRect(40, 40, 176, 176); for (let i = 0; i < 5; i++) { p.fillStyle = `rgb(${70 - i * 12},${60 - i * 10},${50 - i * 9})`; p.fillRect(48 + i * 6, 60 + i * 30, 160 - i * 12, 18); }
      p.fillStyle = "#8A8070"; p.save(); p.translate(180, 60); p.rotate(0.5); p.fillRect(-50, -10, 100, 28); p.restore(); },
    "vault:ghost": (p) => { const g = p.createRadialGradient(128, 110, 10, 128, 110, 120); g.addColorStop(0, "rgba(220,240,255,0.95)"); g.addColorStop(0.6, "rgba(160,200,240,0.6)"); g.addColorStop(1, "rgba(120,160,220,0)"); p.fillStyle = g;
      p.beginPath(); p.moveTo(70, 250); p.quadraticCurveTo(60, 120, 128, 60); p.quadraticCurveTo(196, 120, 186, 250); p.quadraticCurveTo(160, 220, 140, 250); p.quadraticCurveTo(120, 220, 100, 250); p.quadraticCurveTo(84, 225, 70, 250); p.fill();
      p.fillStyle = "rgba(30,40,60,0.8)"; p.fillRect(108, 96, 10, 12); p.fillRect(138, 96, 10, 12); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { vaultstair: (t, x, y) => [{ x, y, layer: "vault:stair", w: 0.9, flat: true }], vaultkeeper: (t, x, y, now) => [{ x, y, layer: "vault:ghost", w: 0.7, h: 1.0, glow: 1.2, alpha: 0.75 + 0.15 * Math.sin((now || 0) / 600), lift: 0.05 + 0.03 * Math.sin((now || 0) / 900) }], vaultexit: (t, x, y) => [{ x, y, layer: "stairs_up", w: 0.6, h: 1.0 }] });
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, r) => { if (xl0) xl0(game, fl, out, r); if (!fl || !fl.vault) return; for (const [k, t] of Object.entries(fl.things)) if (t.type === "vaultkeeper") { const [x, y] = k.split(",").map(Number); out.push({ x: x + 0.5, y: 0.7, z: y + 0.5, reach: 4, colour: [0.55, 0.75, 1.0], flicker: false, d: Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) }); } }; }
  const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a), g = this.game, w = this.$ && this.$("#side .where"); const cp = this.$ && this.$("#view .compass"); if (cp && g && g.floor && g.floor.vault && g.mode !== "title") cp.textContent = `${CM.DIR_NAMES[g.floor.facing]}   -   ${CM.VAULTS[g.floor.vault].name[0].toUpperCase() + CM.VAULTS[g.floor.vault].name.slice(1)}`;
    if (w && g && g.floor && g.floor.vault && g.mode !== "title") w.textContent = `${CM.VAULTS[g.floor.vault].name[0].toUpperCase() + CM.VAULTS[g.floor.vault].name.slice(1)}, under floor ${(CM.VAULT_SPEC[g.floor.number] || {}).from || "?"}`; return out; };
}
