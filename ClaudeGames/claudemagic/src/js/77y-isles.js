"use strict";
// The island dungeons, seen (UPGRADE_PLAN_81.md; the engine 69zzzzl-isles.js, the islands 69zzzzm-gullrock.js ...): the
// islands' creatures given their Quaternius figures (the Ultimate Monsters, the dinosaurs, the fish, the crab), their
// guardians the same figures larger and coloured; the stairs, the stones and the mouth drawn; the floor's name where
// the party is; and the Wren at an island's jetty as she lies at the home dock.
{
  // (the creatures' figures - their models, sizes, tints and lifts - are in src/models/figures.json, baked into 35c-figures.js)
  // the stairs, the stones
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), N = set.size; const c = document.createElement("canvas"); c.width = c.height = N; const p = c.getContext("2d"), u = N / 64;
      p.fillStyle = "#6A6E70"; p.beginPath(); p.moveTo(22 * u, 64 * u); p.lineTo(20 * u, 14 * u); p.quadraticCurveTo(32 * u, 2 * u, 44 * u, 12 * u); p.lineTo(42 * u, 64 * u); p.closePath(); p.fill();
      p.fillStyle = "rgba(255,255,255,0.12)"; p.fillRect(24 * u, 16 * u, 6 * u, 44 * u); p.strokeStyle = "rgba(140,220,230,0.8)"; p.lineWidth = 1.6 * u; p.beginPath(); p.arc(32 * u, 32 * u, 6 * u, 0, Math.PI * 2); p.moveTo(32 * u, 22 * u); p.lineTo(32 * u, 42 * u); p.stroke();
      set.index["isle:stone"] = set.layers.length; set.layers.push(c); return set; }; }
  CM.thingSprites = CM.thingSprites || {};
  Object.assign(CM.thingSprites, { isledown: (t, x, y) => [{ x, y, layer: "hatch", w: 0.9, flat: true, shade: 0.75 }], isleup: (t, x, y) => [{ x, y, layer: "stairs_up", w: 0.6, h: 1.0 }],
    islestone: (t, x, y, now) => [{ x, y, layer: "isle:stone", w: 0.55, h: 0.95, glow: 0.3 + 0.15 * Math.sin(now / 700) }], islemouth: () => [] });
  // where the party is
  { const r0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { const out = r0.apply(this, a), g = this.game, fl = g && g.floor; if (fl && CM.isleOf && CM.isleOf(fl.number)) { const o = CM.isleOf(fl.number), w = this.$("#side .where"), c = this.$("#view .compass");
      if (w) w.textContent = CM.isleFloorName(fl.number); if (c) c.textContent = `${CM.DIR_NAMES[fl.facing]}   -   ${o.depth ? o.isle.deep : o.isle.name}`; } return out; }; }
}
