"use strict";
// A living minimap (v25.1, UPGRADE_PLAN_20.md): the side map moves with the place. Monsters near the party pulse red;
// the portals, the Wayfarer's Stones and the Glyph cabinet glow in their own colours; the party's trail fades out
// behind it; and the map zooms in on the party - the + and - in its corner, or the wheel - and keeps the zoom. It is
// drawn again a few times a second while the dungeon screen is up (only the side map; the big map is as it was).
{ const ZOOMS = [1, 1.6, 2.5, 4], TRAIL = 40;
  const trails = new Map();                                              // floor number -> [[x, y, t]]
  const glowOf = (fl, x, y, t) => {
    if (t.type === "portal") { const P = CM.PORTALCOURT && CM.PORTALCOURT.PORTALS.find(([, at]) => at[0] === x && at[1] === y); return P ? P[3] : t.to === "claudeablo" ? "#E03030" : t.to === "claudecraft" ? "#A060FF" : "#7AA0FF"; }
    if (t.type === "wayfarer") return "#5A9AFF"; if (t.type === "glyphcab") return "#40E070"; if (t.type === "plinth") return "#C8A8FF"; return null;
  };
  const draw0 = CM.UI.prototype.drawAutomap;
  CM.UI.prototype.drawAutomap = function (canvas) {
    const g = this.game, fl = g.towerRun ? g.towerRun.fl : g.floor;
    if (!canvas || canvas.id !== "automap" || !fl || g.towerRun) return draw0.call(this, canvas);
    const p = canvas.getContext("2d"), W = canvas.width, size = fl.grid.length, cell = W / size, z = ZOOMS[this.mapZoom || 0] || 1;
    const ox = CM.clamp(W / 2 - (fl.pos[0] + 0.5) * cell * z, W - W * z, 0), oy = CM.clamp(W / 2 - (fl.pos[1] + 0.5) * cell * z, W - W * z, 0);
    this.mapView = { z, ox, oy, cell };
    p.setTransform(1, 0, 0, 1, 0, 0); p.fillStyle = "#2A2218"; p.fillRect(0, 0, W, W);
    p.setTransform(z, 0, 0, z, ox, oy); draw0.call(this, canvas);
    const now = performance.now(), C = (x, y) => [(x + 0.5) * cell, (y + 0.5) * cell], seen = this.seenSet && this.seenFor === fl.seen.length + ":" + fl.number ? this.seenSet : (this.seenSet = new Set(fl.seen.map(([a, b]) => `${a},${b}`)));
    this.seenFor = fl.seen.length + ":" + fl.number;
    // the trail: the last steps, fading
    const T = trails.get(fl.number) || []; for (let i = 0; i < T.length; i++) { const [x, y] = T[i], [cx, cy] = C(x, y), k = (i + 1) / T.length; p.fillStyle = `rgba(32,160,64,${0.08 + 0.4 * k})`; p.beginPath(); p.arc(cx, cy, cell * (0.1 + 0.08 * k), 0, Math.PI * 2); p.fill(); }
    // what glows, and the monsters in reach
    for (const [k, t] of Object.entries(fl.things)) { if (!seen.has(k)) continue; const [x, y] = k.split(",").map(Number), [cx, cy] = C(x, y);
      const col = glowOf(fl, x, y, t);
      if (col) { const r = cell * (0.9 + 0.25 * Math.sin(now / 380 + x)), grd = p.createRadialGradient(cx, cy, 0, cx, cy, r); grd.addColorStop(0, col); grd.addColorStop(1, "rgba(0,0,0,0)"); p.globalAlpha = 0.75; p.fillStyle = grd; p.beginPath(); p.arc(cx, cy, r, 0, Math.PI * 2); p.fill(); p.globalAlpha = 1; }
      if ((t.type === "monsters" || t.type === "boss" || t.type === "guardian") && Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 7) { const ph = (now / 900 + x * 0.3) % 1; p.strokeStyle = `rgba(220,40,40,${1 - ph})`; p.lineWidth = Math.max(1, cell * 0.12); p.beginPath(); p.arc(cx, cy, cell * (0.35 + ph * 0.8), 0, Math.PI * 2); p.stroke(); }
    }
    p.setTransform(1, 0, 0, 1, 0, 0);
  };
  // the trail is kept as the party walks (a few dozen steps a floor, not saved)
  // the zoom: buttons in the map's corner and the wheel; kept between visits
  const rf0 = CM.UI.prototype.refresh;
  CM.UI.prototype.refresh = function (...a) {
    if (!this.liveBound && this.game && this.game.on && this.$("#automap")) { this.liveBound = true; const g = this.game, c = this.$("#automap");
      try { this.mapZoom = CM.clamp(Number(CM.store.get("mapZoom", 0)) || 0, 0, ZOOMS.length - 1); } catch (e) { this.mapZoom = 0; }
      g.on("moved", (x, y) => { const fl = g.floor; if (!fl) return; const T = trails.get(fl.number) || []; const last = T[T.length - 1]; if (!last || last[0] !== x || last[1] !== y) T.push([x, y]); if (T.length > TRAIL) T.shift(); trails.set(fl.number, T); });
      const box = document.createElement("div"); box.className = "mapzoom"; box.innerHTML = '<button data-z="1" title="Zoom in (or the wheel)">+</button><button data-z="-1" title="Zoom out">−</button>'; c.insertAdjacentElement("afterend", box);
      const set = (d) => { this.mapZoom = CM.clamp((this.mapZoom || 0) + d, 0, ZOOMS.length - 1); try { CM.store.set("mapZoom", this.mapZoom); } catch (e) { /* (kept for the session) */ } this.drawAutomap(c); };
      box.addEventListener("click", (e) => { const b = e.target.closest("button[data-z]"); if (b) { e.stopPropagation(); set(Number(b.dataset.z)); } });
      c.addEventListener("wheel", (e) => { e.preventDefault(); set(e.deltaY < 0 ? 1 : -1); }, { passive: false });
      const tick = () => { if (this.screen === "play" && g.floor && !document.hidden && !g.towerRun) this.drawAutomap(c); setTimeout(tick, 120); }; setTimeout(tick, 120); }
    return rf0.apply(this, a);
  };
}
