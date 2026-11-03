"use strict";
// The Joker's chandeliers (v44.5): the Gilded Joker's hall was lit only by the party's torch and its wall torches, so
// past a few squares the tables stood in the dark and the hall looked empty from the door. Now chandeliers hang over it
// in rows, each a warm light, so the whole floor - its tables, cabinets and counters - can be seen across the room.
{ const S = 128, SPOTS = []; for (let y = 4; y <= 19; y += 5) for (let x = 4; x <= 32; x += 6) SPOTS.push([x, y]);
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); const c = document.createElement("canvas"); c.width = c.height = S; const p = c.getContext("2d");
      p.fillStyle = "#C8A040"; p.fillRect(62, 0, 4, 50); p.beginPath(); p.ellipse(64, 70, 50, 14, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8A6A20"; p.beginPath(); p.ellipse(64, 74, 40, 9, 0, 0, Math.PI * 2); p.fill();
      for (let i = 0; i < 7; i++) { const x = 20 + i * 14.6; p.fillStyle = "#F4E8D0"; p.fillRect(x - 2, 44, 5, 22); p.fillStyle = "#FFD060"; p.beginPath(); p.ellipse(x, 38, 4, 8, 0, 0, Math.PI * 2); p.fill(); }
      p.fillStyle = "#E8C860"; for (let i = 0; i < 6; i++) { p.beginPath(); p.arc(26 + i * 15, 92 + (i % 2) * 8, 4, 0, Math.PI * 2); p.fill(); }
      set.index["jk:chandelier"] = set.layers.length; set.layers.push(c); return set; }; }
  const on = (fl) => Boolean(fl && CM.isJokerFloor && CM.isJokerFloor(fl.number));
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!on(fl) || !CM.renderer || CM.renderer.index["jk:chandelier"] === undefined) return out;
      for (const [x, y] of SPOTS) out.push({ x, y, layer: "jk:chandelier", w: 0.7, h: 0.5, lift: 0.5, glow: 1.6, dx: 0.5, dz: 0.5 }); return out; }; }
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); if (!on(fl)) return; const [px, py] = fl.pos;
      SPOTS.map(([x, y]) => ({ x: x + 1, y: 0.9, z: y + 1, reach: 7.5, colour: [1.0, 0.8, 0.5], flicker: false, d: Math.abs(x + 0.5 - px) + Math.abs(y + 0.5 - py) })).sort((a, b) => a.d - b.d).slice(0, 12).forEach((L) => out.push(L)); }; }
}
