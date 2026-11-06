"use strict";
// The trials - the window's side (UPGRADE_PLAN_65.md, release 3): the hourglass (its sand turning over when it runs),
// the blades swinging on their beat, the statues standing in their riddle doors, the ice as a flat sheet over the
// pond's squares, and a dark room that is only dark.
{ const S = 64;
  const PICS = {
    "sp:hourglass": (p) => { p.fillStyle = "#8A6A2A"; p.fillRect(14, 2, 36, 5); p.fillRect(14, 57, 36, 5); p.fillRect(14, 2, 4, 60); p.fillRect(46, 2, 4, 60); p.fillStyle = "rgba(200,220,240,0.35)"; p.beginPath(); p.moveTo(19, 8); p.lineTo(45, 8); p.lineTo(33, 32); p.lineTo(45, 56); p.lineTo(19, 56); p.lineTo(31, 32); p.closePath(); p.fill(); p.fillStyle = "#D8C070"; p.beginPath(); p.moveTo(23, 56); p.lineTo(41, 56); p.lineTo(32, 42); p.closePath(); p.fill(); },
    "sp:blade": (p) => { p.strokeStyle = "#5A5650"; p.lineWidth = 2; p.beginPath(); p.moveTo(32, 0); p.lineTo(32, 30); p.stroke(); p.fillStyle = "#C8CCD4"; p.beginPath(); p.moveTo(8, 30); p.quadraticCurveTo(32, 52, 56, 30); p.quadraticCurveTo(32, 40, 8, 30); p.fill(); p.strokeStyle = "#F0F4FA"; p.lineWidth = 1.5; p.beginPath(); p.moveTo(10, 32); p.quadraticCurveTo(32, 50, 54, 32); p.stroke(); },
    "sp:ice": (p) => { p.fillStyle = "rgba(170,205,235,0.45)"; p.fillRect(0, 0, S, S); p.strokeStyle = "rgba(255,255,255,0.5)"; p.lineWidth = 1.2; p.beginPath(); p.moveTo(6, 40); p.lineTo(24, 28); p.lineTo(30, 44); p.moveTo(40, 10); p.lineTo(48, 30); p.lineTo(60, 26); p.stroke(); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const name of Object.keys(PICS)) { if (set.index[name] !== undefined) continue; const c = document.createElement("canvas"); c.width = c.height = S; PICS[name](c.getContext("2d")); set.index[name] = set.layers.length; set.layers.push(c); } return set; }; }
  const has = (L) => { const R0 = CM.renderer; return R0 && R0.index && R0.index[L] !== undefined; };
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { hourglass: (t, x, y, now) => { const g = CM.game, running = g && CM.sandRuns && g.floor && CM.sandRuns(g, g.floor); return [{ x, y, layer: "sp:hourglass", w: 0.5, h: 0.95, glow: running ? 0.3 + 0.1 * Math.sin(now / 200) : 0 }]; } });
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !(fl.number >= 1) || game.mode === "title" || !fl.features) return out; const beat = Math.sin(now / 480 * Math.PI);
      for (const [k, f] of Object.entries(fl.features)) { const [x, y] = k.split(",").map(Number); if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) > 12) continue;
        if (f.type === "pendulum") out.push({ x, y, layer: "sp:blade", w: 0.9, h: 0.9, lift: 0.1, dx: (f.phase ? -beat : beat) * 0.45, shade: 0.95 });
        else if (f.type === "ice") out.push({ x, y, layer: "sp:ice", w: 0.98, flat: true, alpha: 0.8 });
        else if (f.type === "door" && f.statue && !f.open && has("monster:Gargoyle")) { for (let d = 0; d < 4; d++) { const [dx, dy] = CM.DIRS[d]; if (fl.grid[y + dy] && fl.grid[y + dy][x + dx] === 0 && !(fl.features[`${x + dx},${y + dy}`] || {}).statue) out.push({ x: x + dx, y: y + dy, face: (d + 2) % 4, layer: "monster:Gargoyle", w: 0.6, h: 0.85, lift: 0.0, shade: 0.5, alpha: 0.9 }); } } }
      return out; }; }
}
