"use strict";
// Townsfolk murmur (v43.2, UPGRADE_PLAN_38.md): by day the Square talks - a low murmur of voices, a syllable here and a
// laugh there, from the side each comes from, louder the more townsfolk are about and the nearer the party is to the
// middle of it; at night it falls quiet. And whoever the party speaks to in town says hello first: a two-note greeting
// in the speaker's own voice (pitched by who they are). On CM.voice, the "town" level.
{ const V = (o) => CM.voice && CM.voice(Object.assign({ group: "town" }, o)), VOW = ["a", "e", "i", "o", "u", "uh", "er"];
  let next = 0;
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor;
    if (!fl || fl.number !== 0 || game.mode !== "explore" || !CM.TOWN_SQUARE || CM.isNight(game) || now < next || !CM.voice || CM.VOICE_LEVELS.town <= 0) return;
    const [x0, y0, x1, y1] = CM.TOWN_SQUARE, cx = (x0 + x1) / 2 + 0.5, cz = (y0 + y1) / 2 + 0.5, eye = r.eye || [fl.pos[0] + 0.5, 0.5, fl.pos[1] + 0.5], d = Math.hypot(cx - eye[0], cz - eye[2]); if (d > 14) { next = now + 1000; return; }
    let folk = 0; for (const [k, t] of Object.entries(fl.things)) { if (t.type !== "villager" && !String(t.type).startsWith("res_") && t.type !== "peddler") continue; const [x, y] = k.split(",").map(Number); if (Math.hypot(x + 0.5 - eye[0], y + 0.5 - eye[2]) < 12) folk++; }
    const busy = Math.min(1, 0.35 + folk * 0.12), near = Math.max(0, 1 - d / 14); next = now + (260 + Math.random() * 520) / busy;
    const yawR = [Math.cos(r.yaw || 0), Math.sin(r.yaw || 0)], ang = Math.random() * Math.PI * 2, sx = cx + Math.cos(ang) * 3 - eye[0], sz = cz + Math.sin(ang) * 3 - eye[2], pan = Math.max(-1, Math.min(1, (sx * yawR[0] + sz * yawR[1]) / 4));
    const P = 110 + Math.random() * 150, laugh = Math.random() < 0.06, vol = 0.035 * near * busy * (0.6 + Math.random() * 0.6);
    if (laugh) for (let i = 0; i < 4; i++) V({ pitch: P * 1.4, to: P * 1.2, ms: 90, vowel: "a", vol: vol * 1.3, pan, at: i * 0.12, breath: 0.4 });
    else { const n = 1 + Math.floor(Math.random() * 3); for (let i = 0; i < n; i++) V({ pitch: P * (1 + (Math.random() - 0.5) * 0.15), to: P * (0.92 + Math.random() * 0.12), ms: 110 + Math.random() * 140, vowel: VOW[Math.floor(Math.random() * VOW.length)], to2: VOW[Math.floor(Math.random() * VOW.length)], vol, pan, at: i * 0.17, breath: 0.15 }); } };
  CM.greet = (who) => { const h = (CM.hashSeed(`greet:${who || "?"}`) >>> 0), P = 105 + (h % 160); V({ pitch: P * 1.15, to: P * 1.3, ms: 170, vowel: "e", to2: "uh", vol: 0.13, breath: 0.15 }); V({ pitch: P * 1.25, to: P * 0.95, ms: 260, vowel: "o", vol: 0.12, at: 0.19 }); };
  let lastGreet = 0;
  const bind = () => { const g = CM.game; if (!g || !g.on) return false; g.on("talk", (e) => { const fl = g.floor, now = performance.now(); if (!fl || !(fl.number === 0 || fl.number === -1 || (CM.isInterior && CM.isInterior(fl.number))) || now - lastGreet < 1500) return; lastGreet = now; CM.greet(e && e.title); }); return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (bind()) clearInterval(t); }, 300);
}
