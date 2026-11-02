"use strict";
// Doors and gates that work (v40.1, UPGRADE_PLAN_35.md): a found secret wall no longer just vanishes - the stone block
// grinds down into the floor over a second, dust bursting out at its foot; a portcullis judders up its chains a notch at a
// time, grit sifting from the lintel while it moves; a door swings past and settles back on its hinge, a puff of dust
// from under it as it first gives. (The swing and lift are 80-main.js's; this adds to the sprites it hands the renderer.)
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); const c = cv(), p = c.getContext("2d"); p.fillStyle = "#8A7C68"; p.beginPath(); p.arc(64, 64, 44, 0, Math.PI * 2); p.fill(); p.fillStyle = "#A89A84"; p.beginPath(); p.arc(52, 54, 18, 0, Math.PI * 2); p.fill();
      set.index["dr:dust"] = set.layers.length; set.layers.push(c); return set; }; }
  const SINK = 1000, dust = (x, y, z, n, spread) => { const K = CM.fxKit; if (!K || !K.fxs || CM.reducedMotion) return; K.fxs.burst({ at: [x, y, z], layer: "dr:dust", n, size: 0.05, speed: spread, up: 0.5, gravity: 1.2, ms: 900, glow: 0 }); };
  // a secret wall sinking: its four faces, let down into the floor (the floor hides what is under it)
  let flSeen = null; const sinking = new Map();
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !fl.features) return out;
      const secrets = Object.entries(fl.features).filter(([, f]) => (f.type === "secret" || f.type === "secretstair") && f.found);
      if (flSeen !== fl) { flSeen = fl; sinking.clear(); for (const [k] of secrets) sinking.set(k, 0); return out; }
      for (const [k] of secrets) if (!sinking.has(k)) { sinking.set(k, CM.reducedMotion ? 0 : now); const [x, y] = k.split(",").map(Number); dust(x + 0.5, 0.05, y + 0.5, 18, 0.9); }
      for (const [k, t0] of sinking) { if (!t0 || now - t0 > SINK) continue; const [x, y] = k.split(",").map(Number), q = (now - t0) / SINK, e = q * q * (3 - 2 * q), judder = Math.sin(now / 25) * 0.008 * (1 - q);
        for (let d = 0; d < 4; d++) out.push({ x, y, layer: "wallsecret", face: d, w: 1, h: 1, lift: -e + judder, shade: 0.85 });
        if (Math.floor(now / 160) !== Math.floor((now - 17) / 160)) dust(x + 0.5, 0.05, y + 0.5, 4, 0.6); }
      return out; }; }
  // the portcullis's judder and grit, the door's settle and puff: by watching what the renderer is given
  const last = new Map();
  const prep = (r) => { const ss0 = r.setSprites; r.setSprites = function (list) { if (!CM.reducedMotion) { const now = performance.now();
        for (const s of list) { if (s.layer === "gate" && s.axis) { const k = `g${s.x},${s.y}`, was = last.get(k); last.set(k, s.lift || 0); if (was !== undefined && Math.abs((s.lift || 0) - was) > 0.0005) {
              s.lift = Math.max(0, (s.lift || 0) - (Math.floor(now / 90) % 2) * 0.025);   /* (a notch at a time: the pawl catching) */
              if (Math.floor(now / 120) !== Math.floor((now - 17) / 120)) dust(s.x + 0.5 + (Math.random() - 0.5) * 0.6, 0.95, s.y + 0.5, 3, 0.15); } }
          else if (typeof s.layer === "string" && s.layer.startsWith("door") && s.axis) { const k = `d${s.x},${s.y}`, st = last.get(k) || { open: false, at: 0 }, open = Boolean(s.swing);
            if (open && !st.open) { st.at = now; dust(s.x + 0.5, 0.03, s.y + 0.5, 6, 0.5); } st.open = open; last.set(k, st);
            if (open && s.swing > 0) { const t = (now - st.at - 350) / 1000; if (t > 0 && t < 1.2) s.swing += Math.sin(t * 14) * Math.exp(-t * 4) * 0.12; } } } }
      return ss0.call(this, list); }; r.doorsWrapped = true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (CM.renderer && !CM.renderer.doorsWrapped) { prep(CM.renderer); clearInterval(t); } }, 200);
}
