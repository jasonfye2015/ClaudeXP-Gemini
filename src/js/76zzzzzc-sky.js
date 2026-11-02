"use strict";
// The sky (v30.2, UPGRADE_PLAN_25.md): clouds drift with the wind (as many as the weather brings) and their shadows
// cross the sunlit ground; stars come out on clear nights and twinkle; on some clear winter nights an aurora hangs
// in the north; on some rainy evenings lightning whitens the land and the thunder follows. (The moon's face already
// waxes and wanes, 30-art.js.) Given to the renderer as renderer.skyx (40-render.js: uStars, uAurora, uCloud, uFlash).
{ const COVER = { clear: 0.2, wind: 0.42, mist: 0.55, rain: 0.86, snow: 0.8 };
  let ox = 0, oz = 0, flash = 0, next = 3, thunderAt = 0, restrike = false;
  const daily = (game, salt, n) => CM.hashSeed(`${game.seed}:${salt}:${CM.dayOf(game)}`) % n === 0;
  CM.stormNow = (game) => Boolean(game && game.seed !== undefined && CM.weather(game) === "rain" && CM.hourOf(game) >= 16 && daily(game, "storm", 2));
  CM.auroraNow = (game) => Boolean(game && game.seed !== undefined && CM.season(game) === "winter" && ["clear", "wind"].includes(CM.weather(game)) && daily(game, "aurora", 3));
  const thunder = (far) => { const A = CM.audio; if (!A || !A.ctx || !A.enabled || !A.master) return; try {
      const ctx = A.ctx, rate = ctx.sampleRate, secs = 3.2, n = Math.floor(rate * secs), b = ctx.createBuffer(1, n, rate), d = b.getChannelData(0); let lp = 0, lp2 = 0, s = 12345;
      for (let i = 0; i < n; i++) { s = (s * 1103515245 + 12345) & 0x7fffffff; const w = s / 0x7fffffff * 2 - 1, t = i / rate; lp += (w - lp) * 0.035; lp2 += (lp - lp2) * 0.08;
        const env = Math.min(1, t / (far ? 0.25 : 0.04)) * Math.exp(-t * (far ? 0.9 : 1.3)) * (1 + 0.6 * Math.sin(t * 7.1) * Math.sin(t * 2.3)); d[i] = lp2 * env * 9; }
      const src = ctx.createBufferSource(), g = ctx.createGain(); src.buffer = b; g.gain.value = far ? 0.35 : 0.6; src.connect(g); g.connect(A.master); src.start(); } catch (er) { /* quiet */ } };
  CM.skyExtras = (game, r, dt) => { const S = r.sky; if (!S) return null;
    const w = S.weather || "clear", cover = COVER[w] === undefined ? 0.3 : COVER[w], dir = r.wind && r.wind.dir ? r.wind.dir : [0.8, 0.6], sp = (w === "wind" ? 0.05 : 0.018) * (CM.reducedMotion ? 0 : 1);
    ox -= dir[0] * sp * dt; oz -= dir[1] * sp * dt;
    const dark = Math.max(0, Math.min(1, 1 - S.light / 0.3)), L = S.light;
    let col = w === "rain" ? [0.5, 0.52, 0.56] : w === "snow" || w === "mist" ? [0.8, 0.8, 0.84] : [1, 0.98, 0.96];
    col = col.map((c, i) => c * (0.18 + 0.85 * L) + (S.word === "dusk" || S.word === "dawn" ? S.horizon[i] * 0.35 : 0));
    if (CM.stormNow(game)) { next -= dt; if (next <= 0) { flash = 1; restrike = Math.random() < 0.5; next = 7 + Math.random() * 18; thunderAt = performance.now() + 700 + Math.random() * 2600; } }
    if (restrike && flash < 0.45 && flash > 0.3) { flash = 0.85; restrike = false; }
    flash = Math.max(0, flash - dt * 3.2);
    if (thunderAt && performance.now() >= thunderAt) { thunder(thunderAt % 2 > 1); thunderAt = 0; }
    return { stars: dark * (1 - cover * 0.95), aurora: CM.auroraNow(game) ? dark : 0, cloud: [ox, oz, cover, 1], cloudCol: col, flash: CM.reducedMotion ? 0 : flash * flash };
  };
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); r.skyx = r.sky ? CM.skyExtras(game, r, dt) : null; };
}
