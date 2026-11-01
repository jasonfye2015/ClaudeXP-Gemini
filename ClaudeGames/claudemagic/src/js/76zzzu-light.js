"use strict";
// Light (v22.0, UPGRADE_PLAN_17.md): more of the world gives light. In the town, the Portal Court's portals and their
// braziers in their own colours, the Wayfarer's Stone's runes; after dark, the lit windows on the street. In the Wood,
// the Glyph Deep's cabinet and the stone. Everywhere, a spell or a blast flares where it lands - fire orange, frost
// blue, lightning white, holy light gold, a blink violet - and dies away. The nearest 24 of all of them reach the
// renderer each frame (80-main.js lightsNear calls CM.extraLights).
{ const FLARE = { fire: [[1.0, 0.5, 0.15], 3.4, 0.45], fireball: [[1.0, 0.45, 0.12], 4.2, 0.6], firebolt: [[1.0, 0.5, 0.15], 3.2, 0.4], sear: [[1.0, 0.55, 0.2], 3.0, 0.4], cold: [[0.5, 0.75, 1.0], 3.0, 0.45], frost: [[0.5, 0.78, 1.0], 3.2, 0.5],
    lightning: [[0.85, 0.9, 1.0], 4.5, 0.25], calllightning: [[0.85, 0.9, 1.0], 5.0, 0.3], smite: [[1.0, 0.9, 0.55], 3.2, 0.45], turn: [[1.0, 0.92, 0.6], 3.6, 0.6], light: [[1.0, 0.9, 0.6], 4.0, 0.8], bless: [[1.0, 0.88, 0.55], 2.6, 0.5],
    sanctuary: [[1.0, 0.92, 0.65], 3.0, 0.7], mend: [[0.7, 1.0, 0.7], 2.4, 0.5], ward: [[0.6, 0.8, 1.0], 2.6, 0.5], teleport: [[0.75, 0.5, 1.0], 3.0, 0.5], blink: [[0.75, 0.5, 1.0], 2.6, 0.4], sparkle: [[1.0, 0.85, 0.4], 1.8, 0.5],
    shatter: [[0.7, 0.85, 1.0], 2.2, 0.3], missile: [[0.8, 0.6, 1.0], 2.6, 0.35], summon: [[0.7, 0.4, 1.0], 3.0, 0.6], rise: [[0.6, 1.0, 0.7], 3.6, 0.8], relic: [[1.0, 0.85, 0.45], 3.0, 0.6] };
  const flares = [];
  CM.lightFlare = (renderer, kind, at) => { const F = FLARE[kind]; if (!F || !renderer) return; let x, y, z;
    if (at) { x = at[0] + 0.5; z = at[1] + 0.5; y = 0.6; } else { const e = renderer.eye || [0, 0.5, 0], yaw = renderer.yaw || 0; x = e[0] + Math.sin(yaw) * 1.4; z = e[2] - Math.cos(yaw) * 1.4; y = 0.7; }   // (no square named: in front of the party, where a fight is)
    flares.push({ x, y, z, reach: F[1], colour: F[0], born: performance.now(), life: F[2] * 1000 }); if (flares.length > 8) flares.shift(); };
  const near = (fl, x, z, max = 10) => Math.abs(x - fl.pos[0] - 0.5) + Math.abs(z - fl.pos[1] - 0.5) <= max;
  CM.extraLights = (game, fl, out, renderer) => { const night = CM.isNight && CM.isNight(game), add = (x, y, z, reach, colour, flicker) => { if (near(fl, x, z)) out.push({ x, y, z, reach, colour, flicker, d: Math.abs(x - fl.pos[0] - 0.5) + Math.abs(z - fl.pos[1] - 0.5) }); };
    const hex = (c) => { const n = parseInt(c.slice(1), 16); return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255]; };
    if (fl.number === 0 && CM.PORTALCOURT) for (const [, at, , col] of CM.PORTALCOURT.PORTALS) { const c = hex(col); add(at[0] + 0.5, 0.75, at[1] + 0.5, night ? 3.0 : 2.0, c.map((v) => v * (night ? 0.9 : 0.55)), true); }
    if (CM.WAYSTONE) { const at = fl.number === 0 ? CM.WAYSTONE.court : fl.number === -1 ? CM.WAYSTONE.wood : null; if (at) add(at[0] + 0.5, 0.8, at[1] + 0.5, 1.8, [0.35, 0.6, 1.0].map((v) => v * (night ? 0.8 : 0.4)), false); }
    if (fl.number === -1 && CM.GLYPH_AT) add(CM.GLYPH_AT[0] + 0.5, 0.7, CM.GLYPH_AT[1] + 0.5, 2.0, [0.3, 1.0, 0.45].map((v) => v * (night ? 0.7 : 0.35)), false);
    if (night && renderer && renderer.windowLights) { const ws = renderer.windowLights.filter(([x, , z]) => near(fl, x, z, 8)).sort((a, b) => (Math.abs(a[0] - fl.pos[0]) + Math.abs(a[2] - fl.pos[1])) - (Math.abs(b[0] - fl.pos[0]) + Math.abs(b[2] - fl.pos[1]))).slice(0, 8);
      for (const [x, y, z] of ws) add(x, y, z, 2.2, [1.0, 0.68, 0.32].map((v) => v * 0.75), false); }
    const now = performance.now(); for (let i = flares.length - 1; i >= 0; i--) { const F = flares[i], k = 1 - (now - F.born) / F.life; if (k <= 0) { flares.splice(i, 1); continue; } out.push({ x: F.x, y: F.y, z: F.z, reach: F.reach, colour: F.colour.map((v) => v * 1.4 * k * k), flicker: false, d: -1 }); } };
  // a flare for every spell and blast the game shows (bound once the window and the renderer are up)
  { const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { if (!this.lightBound && this.game && this.game.on && CM.renderer) { this.lightBound = true; this.game.on("fx", (e) => { if (e && FLARE[e.kind]) CM.lightFlare(CM.renderer, e.kind, e.at); }); } return rf0.apply(this, a); }; }
}
