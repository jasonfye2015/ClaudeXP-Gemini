"use strict";
// Deaths of their own (v29.2, UPGRADE_PLAN_24.md): a monster dies as what it is. The bones crumble where they stand;
// the burning, the demons and the undead flesh go to ash, darkening and blowing away; the crystal ones shatter in a
// flash; the drowned - and anything that falls in water - sink with a splash; the ghosts rise away (as they did);
// the rest topple and fade (as they did).
{ CM.deathStyleOf = (m, game) => {
    if (!m) return null; const name = m.kind || m.name || "", K = CM.monsterKind(name) || {}, hide = CM.hideOf ? CM.hideOf(m) : "flesh";
    if (K.body === "ghost") return null;
    if (/Crystal|Shard|Glass|Gem/.test(name) || hide === "shell" && /Golem|Wisp/.test(name)) return "shatter";
    if (/Drowned|Weed|Eel|Siren/.test(name) || (game && game.terrain && game.mode === "combat" && game.terrain().includes("water"))) return "sink";
    if (hide === "bone" || /Skelet|Bone/.test(name)) return "crumble";
    if (/Demon|Imp|Fire|Ember|Slag|Foundr|Salamander/.test(name) || (m.undead && hide !== "bone")) return "ash";
    return null; };
  // the poses (28-motion.js's fall, as each dies)
  const motion0 = CM.motion;
  CM.motion = function (s) {
    if (!s.deathStyle || s.fellAt === undefined || s.fellAt === null) return motion0.call(this, s);
    const t = s.now - s.fellAt, out = { forward: 0, back: 0, lift: 0, tilt: 0, scaleY: 1, scale: 1, flash: 0, alpha: 1, skew: 0, done: false, dark: 0 };
    if (s.reduced) { const k = Math.min(1, t / 600); out.alpha = 1 - k; out.done = k >= 1; return out; }
    if (s.deathStyle === "crumble") { const k = Math.min(1, t / 520); out.scaleY = Math.max(0.02, 1 - k * k); out.skew = 0.04 * Math.sin(t / 30) * (1 - k); out.alpha = k < 0.85 ? 1 : (1 - k) / 0.15; out.done = k >= 1; }
    else if (s.deathStyle === "ash") { const k = Math.min(1, t / 900); out.dark = Math.min(0.85, k * 1.6); out.lift = k * 0.12; out.scale = 1 - 0.25 * k; out.alpha = k < 0.45 ? 1 : 1 - (k - 0.45) / 0.55; out.done = k >= 1; }
    else if (s.deathStyle === "shatter") { const k = Math.min(1, t / 160); out.flash = 1 - k * 0.3; out.scale = 1 + 0.12 * k; out.alpha = 1 - k; out.done = k >= 1; }
    else if (s.deathStyle === "sink") { const k = Math.min(1, t / 800); out.lift = -k * k * 0.9; out.tilt = 0.25 * k; out.alpha = k < 0.8 ? 1 : (1 - k) / 0.2; out.done = k >= 1; }
    return out; };
  // what flies when each dies
  { const bind = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { if (!this.deathBound && this.game && this.game.on && CM.fxKit) { this.deathBound = true; const g = this.game;
        g.on("fx", (e) => { if (!e || e.kind !== "die" || !e.foe || CM.reducedMotion) return; const K = CM.fxKit, style = CM.deathStyleOf(e.foe, g); if (!style || !K.renderer || !K.renderer.ok) return;
          setTimeout(() => { const at = K.atFoe(e.foe, 0.4); if (!at) return;
            if (style === "crumble") { K.fxs.burst({ at: [at[0], 0.2, at[2]], layer: "fx:shard", n: 18, size: 0.09, speed: 0.9, up: 0.8, gravity: 5, ms: 900 }); }
            if (style === "ash") { K.fxs.drift({ at: [at[0], 0.4, at[2]], layer: "fx:fire", n: 14, size: 0.05, spread: 0.6, rise: 0.9, ms: 1400 }); K.fxs.drift({ at: [at[0], 0.3, at[2]], layer: "fx:shard", n: 10, size: 0.07, spread: 0.5, rise: 0.6, ms: 1600 }); }
            if (style === "shatter") { K.fxs.burst({ at, layer: "fx:frost", n: 30, size: 0.08, speed: 2.2, up: 1.6, ms: 800 }); K.fxs.ring({ at: [at[0], 0, at[2]], to: 1.8, ms: 400 }); if (CM.lightFlare) CM.lightFlare(K.renderer, "shatter", [at[0] - 0.5, at[2] - 0.5]); K.renderer.shake(0.2); }
            if (style === "sink") { K.fxs.ring({ at: [at[0], 0, at[2]], to: 1.4, ms: 900, glow: 0.4 }); setTimeout(() => K.fxs.ring({ at: [at[0], 0, at[2]], to: 1.0, ms: 800, glow: 0.3 }), 250); K.fxs.burst({ at: [at[0], 0.05, at[2]], layer: "fx:frost", n: 12, size: 0.05, speed: 0.8, up: 1.8, gravity: 4, ms: 700 }); }
          }, 60); }); }
      return bind.apply(this, a); }; }
}
