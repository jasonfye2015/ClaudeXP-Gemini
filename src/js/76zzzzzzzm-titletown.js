"use strict";
// An animated title (v42.1, UPGRADE_PLAN_37.md): behind the title the view is no longer a corridor turning on the spot -
// it drifts slowly up and down Caer Duin's longest street at the real hour, in the real season and under the day's own
// weather (the sky, the light, the rain on the ground, the snow), the props of the street standing about. The town's
// pictures are the ones the title already readies (80-main.js prepareTown); leaving the title gives the renderer back
// the corridor's, so whatever comes next finds things as it left them. Reduced motion: the view stands still.
{ let townArt = null, active = false, savedArt = null, calling = false, route = null, town = null, t0 = 0, quietSince = 0;
  const realGame = () => { const d = new Date(), start = new Date(d.getFullYear(), 0, 1), day = Math.floor((d - start) / 86400000) + 1, mins = d.getHours() * 60 + d.getMinutes();
    return Object.assign(Object.create(CM.game), { clock: day * 1440 + mins - CM.CLOCK.start, season: CM.seasonOfDate(d), seed: `title-${d.getFullYear()}` }); };
  const longestStreet = (fl) => { const N = fl.grid.length, open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0; let best = null;
    for (let y = 1; y < N - 1; y++) { let run = 0; for (let x = 1; x < N; x++) { if (open(x, y)) run++; else { if (!best || run > best.len) best = { len: run, x0: x - run, y0: y, dx: 1, dy: 0 }; run = 0; } } }
    for (let x = 1; x < N - 1; x++) { let run = 0; for (let y = 1; y < N; y++) { if (open(x, y)) run++; else { if (!best || run > best.len) best = { len: run, x0: x, y0: y - run, dx: 0, dy: 1 }; run = 0; } } }
    return best && best.len >= 5 ? best : null; };
  const own = (r, f) => { calling = true; try { return f(); } finally { calling = false; } };
  const prep = (r) => {
    const pr0 = r.prepare; r.prepare = function (art) { if (CM.game && CM.game.mode === "title" && art && art.index && art.index["solid:house"] !== undefined) townArt = art; return pr0.call(this, art); };
    const st0 = r.setTextures; r.setTextures = function (art, gentle) { if (!calling) { active = false; savedArt = art; } return st0.call(this, art, gentle); };   /* (the game's own: it has taken the pictures back) */
    const sf0 = r.setFloor; r.setFloor = function (floor, theme) { if (!calling && active) { active = false; if (theme !== CM.TOWN_THEME && savedArt) own(this, () => st0.call(this, savedArt, false)); } return sf0.call(this, floor, theme); };   /* (the game's next floor on the town's pictures: the corridor's given back first) */
    const fr0 = r.frame; r.frame = function (dt) { const g = CM.game;
      const clear = g && g.mode === "title" && !document.getElementById("splash"); if (!clear) quietSince = 0; else if (!quietSince) quietSince = performance.now();
      if (g && g.mode === "title" && townArt && this.ok && !CM.titleTownOff && (active || (quietSince && performance.now() - quietSince > 2500))) {   /* (v42.4: only once the title has stood a while - the town's mesh is a moment's work, and not under the card or the first key) */
        if (!active) { if (!town) { town = CM.makeFloor(0, "title"); route = longestStreet(town); } if (!route) return fr0.call(this, dt);
          own(this, () => this.setTextures(townArt, false)); const P = realGame(); this.season = P.season; this.night = CM.isNight(P) ? 0.7 : 0; own(this, () => this.setFloor(town, CM.TOWN_THEME)); active = true; t0 = performance.now(); }
        const P = realGame(), sky = CM.sky(P), w = CM.weather(P); this.sky = sky; this.light = CM.isNight(P) ? 0.8 : 1.3; this.wet = w === "rain" ? 1 : 0; this.snow = w === "snow" ? 1 : 0; this.lights = [];
        const R = route, span = R.len - 1, speed = 0.3, tt = CM.reducedMotion ? 0 : (performance.now() - t0) / 1000, leg = span / speed, ph = (tt % (2 * leg)) / leg, back = ph > 1, k = back ? 2 - ph : ph, e = k * k * (3 - 2 * k);
        const x = R.x0 + R.dx * span * e + 0.5, z = R.y0 + R.dy * span * e + 0.5, face = R.dx ? (back ? 3 : 1) : (back ? 0 : 2), turnK = Math.min(1, Math.min(ph % 1, 1 - (ph % 1)) * leg / 2);
        const yawTo = this.yawFor(face), yawFrom = this.yawFor((face + 2) % 4); let dy = ((yawTo - yawFrom + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
        this.eye = [x, this.eye ? this.eye[1] : 0.5, z]; this.yaw = (turnK >= 1 ? yawTo : yawFrom + dy * (0.5 + 0.5 * turnK)) + (CM.reducedMotion ? 0 : Math.sin(tt * 0.21) * 0.25); this.move = this.turn = null;
        const out = []; for (const p of this.standing || []) if (Math.abs(p.x + 0.5 - x) + Math.abs(p.y + 0.5 - z) <= 12) out.push({ x: p.x, y: p.y, dx: p.dx, dz: p.dz, layer: p.layer, w: p.w, h: p.h });
        this.setSprites(out); }
      return fr0.call(this, dt); };
    r.titleTownWrapped = true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (CM.renderer && !CM.renderer.titleTownWrapped) { prep(CM.renderer); clearInterval(t); } }, 50);
}
