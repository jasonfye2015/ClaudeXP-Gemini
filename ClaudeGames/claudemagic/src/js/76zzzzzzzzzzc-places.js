"use strict";
// The real-time places' look, the window's side (v64.0, UPGRADE_PLAN_59.md): in the Fortress the torch's light
// breathes and warms what is near, dust drifts in it and the view's corners fall into the dark; in Claudeita's cave
// water drips from the roof about the hero and the deep has a cold glow at its edge; over Claudebros' sky the hour
// lies - warm at dusk and dawn, a deep blue with stars at night - and clouds cross every kind of level. The flicker,
// the tint and the motes are 64zzze-placelook.js's; the rest is drawn here over (or under) what the places draw.
{ const U = CM.UI.prototype, rnd = Math.random;
  // the Fortress: drawn just before its HUD (drawFortress ends with fortHud)
  { const fh0 = U.fortHud; U.fortHud = function (p, c, run) { try { if (!CM.reducedMotion && this.fortView) { const t = run.t || 0, T = this.fortView.T, hx = run.x * T - this.fortView.ox, hy = run.y * T - this.fortView.oy, fl = CM.flickerAt(t, 3);
        const warm = p.createRadialGradient(hx, hy, 0, hx, hy, T * 3.2 * fl); warm.addColorStop(0, "rgba(255,170,80,0.16)"); warm.addColorStop(0.6, "rgba(255,140,60,0.06)"); warm.addColorStop(1, "rgba(255,120,40,0)"); p.fillStyle = warm; p.fillRect(0, 0, c.width, c.height);   // the torch's warmth, breathing
        const ring = p.createRadialGradient(hx, hy, T * 6.5 * fl, hx, hy, T * 9 * fl); ring.addColorStop(0, "rgba(0,0,0,0)"); ring.addColorStop(1, "rgba(0,0,0,0.35)"); p.fillStyle = ring; p.fillRect(0, 0, c.width, c.height);   // the edge of its reach, unsteady
        const M = this._fortMotes || (this._fortMotes = CM.motesOf(run.seed || 1, 28)); p.fillStyle = "rgba(255,230,180,0.5)";
        for (const m of M) { const x = ((m.x + m.vx * t) % 1 + 1) % 1, y = ((m.y + m.vy * t) % 1 + 1) % 1, px = x * c.width, py = y * c.height, d = Math.hypot(px - hx, py - hy) / (T * 7); if (d > 1) continue;
          p.globalAlpha = (1 - d) * (0.35 + 0.35 * Math.sin(t * 1.3 + m.phase)); p.beginPath(); p.arc(px, py, 1.3, 0, Math.PI * 2); p.fill(); }
        p.globalAlpha = 1; const vg = p.createRadialGradient(c.width / 2, c.height / 2, c.height * 0.45, c.width / 2, c.height / 2, c.height * 0.95); vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,0.55)"); p.fillStyle = vg; p.fillRect(0, 0, c.width, c.height); } } catch (e) { /* the look is a nicety */ }
      return fh0.call(this, p, c, run); }; }
  // the cave: drips from the roof near the hero, and the deep's cold glow - just before its HUD
  { const ch0 = U.caveHud; U.caveHud = function (p, c, run) { try { if (!CM.reducedMotion && this.caveView && run.player) { const V = this.caveView, { ox, oy, s, vw, vh } = V, pl = run.player, D = this._caveDrips || (this._caveDrips = []), now = performance.now() / 1000;
        if (pl.y > CM.CV.SURFACE + 12 && D.length < 6 && rnd() < 0.06) D.push({ x: pl.x + (rnd() - 0.5) * vw * 0.9, y: oy + 2, vy: 18 + rnd() * 10, born: now, splash: 0 });   // a drop from the roof, somewhere in the view
        p.setTransform(s, 0, 0, s, -ox * s, -oy * s); p.fillStyle = "rgba(170,210,240,0.85)";
        for (const d of D) { const age = now - d.born; if (!d.splash) { d.y += d.vy * (1 / 60); const cell = run.world && run.world.solid ? run.world.solid(d.x, d.y + 1) : d.y > oy + vh; if (cell || d.y > oy + vh + 4) d.splash = now; else p.fillRect(d.x, d.y, 0.8, 2.2); }
          else { const k = (now - d.splash) / 0.25; if (k < 1) { p.globalAlpha = 1 - k; p.fillRect(d.x - 1.5 - k * 2, d.y - 0.5, 1, 1); p.fillRect(d.x + 1.5 + k * 2, d.y - 0.5, 1, 1); p.globalAlpha = 1; } } void age; }
        this._caveDrips = D.filter((d) => !d.splash || now - d.splash < 0.3);
        p.setTransform(1, 0, 0, 1, 0, 0); const depth = Math.max(0, Math.min(1, (pl.y - CM.CV.SURFACE) / 600)); if (depth > 0.15) { const g = p.createRadialGradient(c.width / 2, c.height / 2, c.height * 0.35, c.width / 2, c.height / 2, c.height * 0.9); g.addColorStop(0, "rgba(40,80,140,0)"); g.addColorStop(1, `rgba(40,80,140,${0.18 * depth * (0.8 + 0.2 * Math.sin(now * 0.8))})`); p.fillStyle = g; p.fillRect(0, 0, c.width, c.height); } } } catch (e) { /* no matter */ }
      return ch0.call(this, p, c, run); }; }
  // Claudebros: the hour over the sky, and clouds for every level - over the scenery, under the level's own strip
  { const bs0 = U.brScenery; U.brScenery = function (p, c, run, camX, T) { const out = bs0.call(this, p, c, run, camX, T); try { const g = CM.game, h = g && CM.hourOf ? CM.hourOf(g) : 12, [dawn, dusk] = g && CM.daylightOf ? CM.daylightOf(g) : [6, 20], tint = CM.hourTint(h, dawn, dusk);
        if (run.L && run.L.ground !== "meadow" && run.L.ground !== "cave") { p.fillStyle = "rgba(255,255,255,0.5)"; for (let i = 0; i < 5; i++) { const x = ((i * 300 - camX * T * 0.15) % (c.width + 320) + c.width + 320) % (c.width + 320) - 160, y = 34 + (i % 3) * 26; p.beginPath(); p.ellipse(x, y, 42, 12, 0, 0, Math.PI * 2); p.ellipse(x + 24, y - 8, 28, 12, 0, 0, Math.PI * 2); p.ellipse(x - 22, y - 5, 24, 10, 0, 0, Math.PI * 2); p.fill(); } }
        if (tint[3] > 0) { p.fillStyle = `rgba(${tint[0]},${tint[1]},${tint[2]},${tint[3]})`; p.fillRect(0, 0, c.width, c.height);
          if (tint[3] > 0.5) { const r = new CM.Random("bros:stars"); p.fillStyle = "rgba(255,255,255,0.8)"; for (let i = 0; i < 40; i++) { const x = r.next() * c.width, y = r.next() * c.height * 0.5, tw = 0.5 + 0.5 * Math.sin((run.t || 0) * 2 + i); p.globalAlpha = tw * (tint[3] - 0.5) * 2; p.fillRect(x, y, 2, 2); } p.globalAlpha = 1; } } } catch (e) { /* no matter */ }
      return out; }; }
}
