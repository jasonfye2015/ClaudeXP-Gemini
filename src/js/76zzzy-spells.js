"use strict";
// Spells that travel (v23.0, UPGRADE_PLAN_18.md): every spell aimed at foes leaves its caster's hand - the hero's own
// side of the view - and travels to them, lands with an impact (a ring on the floor, a burst, a flare of its light on
// the walls), and some leave something on the ground a while: fire, frost, holy light, roots. Spells on the party rise
// about the caster's side instead. 80-main.js's castFx asks here first (CM.castFx2) and draws its own recipe for
// anything this leaves alone. The kit (CM.fxKit) is 80-main's: the effects, where a foe stands, the party's hand.
{ const GROUND = { fire: ["fx:fire", "fx:spark"], frost: ["fx:frost", null], holy: ["fx:holy", "fx:holy"], leaf: ["fx:leaf", "fx:leaf"], force: ["fx:ring", null], bolt: ["fx:ring", "fx:spark"] };
  const TINT = { fire: "rgba(255,120,30,0.28)", frost: "rgba(120,200,255,0.25)", force: "rgba(200,120,255,0.22)", holy: "rgba(255,240,180,0.3)", bolt: "rgba(220,235,255,0.5)", leaf: null, dark: "rgba(140,20,40,0.3)" };
  const LIGHT = { fire: "fire", frost: "frost", holy: "smite", bolt: "lightning", force: "missile", leaf: "mend", dark: "summon" };
  const LAYER = { fire: "fx:fire", frost: "fx:frost", holy: "fx:holy", bolt: "fx:bolt", force: "fx:force", leaf: "fx:leaf", dark: "fx:shard" };
  const wait = (ms, fn) => setTimeout(fn, ms / (CM.fxSpeed || 1));
  const holdFor = (K, ms) => { K.fxs.holdUntil = Math.max(K.fxs.holdUntil, performance.now() + ms / (CM.fxSpeed || 1)); };   // (the numbers wait for the last of a volley)
  const sideOf = (K, hero) => { const i = hero ? K.game.party.indexOf(hero) : -1; return i < 0 ? 0 : (i - 1.5) * 0.9; };
  // where a bolt lands: a burst, a ring, its light; and, if it lingers, something on the floor under the foe
  function impact(K, at, el, o = {}) {
    if (!at) return;
    K.fxs.burst({ at, layer: el === "frost" ? "fx:frost" : el === "leaf" ? "fx:leaf" : el === "dark" ? "fx:shard" : "fx:spark", n: o.n || 12, size: el === "frost" ? 0.1 : 0.07, speed: o.speed || 1.3, up: 1.5 });
    K.fxs.ring({ at: [at[0], 0, at[2]], to: o.ring || 1.1, ms: 420, layer: "fx:ring" });
    if (CM.lightFlare) CM.lightFlare(K.renderer, LIGHT[el] || "missile", [at[0] - 0.5, at[2] - 0.5]);
    if (TINT[el] && !o.noTint) K.ui.tint(TINT[el], 240);
    if (o.linger && GROUND[o.linger] && !CM.reducedMotion) K.fxs.ground({ at: [at[0], 0, at[2]], layer: GROUND[o.linger][0], motes: GROUND[o.linger][1], size: o.patch || 0.75, ms: o.lingerMs || 2600, alpha: 0.7 });
  }
  function bolt(K, hero, foe, el, o = {}) {                             // from the hand to the foe, then the impact
    const to = K.atFoe(foe, o.h || 0.5); if (!to) return;
    const from = o.from || K.fromParty(sideOf(K, hero));
    K.fxs.projectile({ from, to, layer: LAYER[el], size: o.size || 0.22, ms: o.ms || 320, trail: o.trail === undefined ? LAYER[el] : o.trail, arc: o.arc === undefined ? 0.12 : o.arc, then: () => impact(K, to, el, o) });
  }
  function fromAbove(K, foe, el, o = {}) {                              // a crack from the sky (or the roof): a column of light, then the impact
    const to = K.atFoe(foe, 0.5); if (!to) return;
    const top = [to[0] + (o.lean || 0.1), 1.6, to[2]];
    K.fxs.projectile({ from: top, to, layer: LAYER[el], size: o.size || 0.3, ms: o.ms || 150, trail: LAYER[el], arc: 0, then: () => { impact(K, to, el, o); K.fxs.flare({ at: [to[0], 0.6, to[2]], layer: LAYER[el], size: 1.1, ms: 300, grow: 0.1 }); if (o.shake) K.renderer.shake(o.shake); } });
  }
  function onParty(K, hero, layer, tint) {                              // a spell on the party: motes rising at the caster's side, the light about them
    const s = sideOf(K, hero), at = K.beforeParty(0.55), r = [Math.cos(K.renderer.yaw), 0, Math.sin(K.renderer.yaw)];
    K.fxs.drift({ at: [at[0] + r[0] * s * 0.25, 0.15, at[2] + r[2] * s * 0.25], layer, n: 10, size: 0.05, spread: 0.7, rise: 0.6, ms: 1100 });
    if (tint) K.ui.tint(tint, 600);
    if (CM.lightFlare) CM.lightFlare(K.renderer, layer === "fx:leaf" ? "mend" : "bless", null);
  }
  CM.castFx2 = (fx, foes, K) => {
    if (!K || !K.renderer || !K.renderer.ok) return false;
    const id = fx.id, h = fx.hero, foe = fx.foe || foes[0], big = (fx.power || 1) > 1;
    switch (id) {
      case "missile": for (let i = 0; i < 3; i++) wait(i * 90, () => bolt(K, h, foe, "force", { size: 0.14, ms: 260, arc: 0.2 * (i - 1), n: 6, ring: 0.6, noTint: i > 0 })); holdFor(K, 180 + 260); return true;
      case "firebolt": bolt(K, h, foe, "fire", { linger: "fire", patch: 0.6, lingerMs: 1800 }); return true;
      case "fire": if (fx.item === "wand" && fx.foe) { bolt(K, h, fx.foe, "fire", { linger: "fire", patch: 0.6, lingerMs: 1800 }); return true; } // falls through: a scroll is a fireball
      case "fireball": {
        const places = foes.map((m) => K.atFoe(m, 0.5)).filter(Boolean); if (!places.length) return false;
        const mid = places.reduce((a, p) => [a[0] + p[0] / places.length, a[1] + p[1] / places.length, a[2] + p[2] / places.length], [0, 0, 0]);
        K.fxs.projectile({ from: K.fromParty(sideOf(K, h)), to: mid, layer: "fx:fire", size: big ? 0.44 : 0.34, ms: 380, trail: "fx:fire", arc: 0.18, then: () => {
          K.fxs.ring({ at: [mid[0], 0, mid[2]], to: 2.8, ms: 520 }); K.fxs.flare({ at: [mid[0], 0.5, mid[2]], layer: "fx:fire", size: 1.4, ms: 380, grow: 0.6 });
          for (const p of places) { K.fxs.burst({ at: p, layer: "fx:fire", n: 9, size: 0.09, speed: 1.3, up: 1.4, ms: 550 }); if (!CM.reducedMotion) K.fxs.ground({ at: [p[0], 0, p[2]], layer: "fx:fire", motes: "fx:spark", size: 0.8, ms: 3000, alpha: 0.75 }); }
          if (CM.lightFlare) CM.lightFlare(K.renderer, "fireball", [mid[0] - 0.5, mid[2] - 0.5]); K.ui.tint("rgba(255,120,30,0.45)", 400); K.renderer.shake(0.4); } });
        return true; }
      case "frost": foes.forEach((m, i) => wait(i * 70, () => bolt(K, h, m, "frost", { size: 0.18, ms: 300, arc: 0.16, linger: "frost", patch: 0.8, lingerMs: 3200, noTint: i > 0 })));
        foes.forEach((m) => { const at = K.atFoe(m, 0); if (at) wait(300, () => K.fxs.rain({ at: [at[0], 0, at[2]], n: 8 })); }); holdFor(K, foes.length * 70 + 300); return true;
      case "lightning": { const to = K.atFoe(foe, 0.55); if (!to) return false; const from = K.fromParty(sideOf(K, h));
        for (let i = 0; i < 3; i++) wait(i * 40, () => K.fxs.projectile({ from, to: [to[0] + (i - 1) * 0.05, to[1] + (i % 2) * 0.08, to[2]], layer: "fx:bolt", size: 0.2, ms: 110, trail: "fx:bolt", arc: (i - 1) * 0.1 }));
        wait(110, () => { impact(K, to, "bolt", { ring: 1.4, linger: "bolt", patch: 0.7, lingerMs: 900 }); K.fxs.flare({ at: [to[0], 0.6, to[2]], layer: "fx:bolt", size: 1.1, ms: 300, grow: 0.1 }); K.renderer.shake(0.35); }); holdFor(K, 200); return true; }
      case "calllightning": fromAbove(K, foe, "bolt", { size: 0.32, ms: 130, ring: 1.6, shake: 0.45, linger: "bolt", patch: 0.8, lingerMs: 1200 }); return true;
      case "smite": fromAbove(K, foe, "holy", { size: 0.3, ms: 220, ring: 1.2, linger: "holy", patch: 0.7, lingerMs: 2200, lean: 0 }); return true;
      case "turn": { const at = K.beforeParty(0.4); K.fxs.ring({ at: [at[0], 0, at[2]], to: 4.2, ms: 700, layer: "fx:ring" }); K.ui.tint("rgba(255,240,180,0.4)", 500); if (CM.lightFlare) CM.lightFlare(K.renderer, "turn", null);
        for (const m of foes) if (m.undead) wait(320, () => { const p = K.atFoe(m, 0.6); if (p) { K.fxs.flare({ at: p, layer: "fx:holy", size: 0.7, ms: 500, rise: 0.3, grow: 0.5 }); if (!CM.reducedMotion) K.fxs.ground({ at: [p[0], 0, p[2]], layer: "fx:holy", motes: "fx:holy", size: 0.7, ms: 2000, alpha: 0.6 }); } });
        holdFor(K, 360); return true; }
      case "sleep": case "lullaby": K.ui.tint("rgba(160,120,255,0.22)", 600);
        foes.forEach((m, i) => { const to = K.atFoe(m, 0.8); if (to) K.fxs.projectile({ from: K.fromParty(sideOf(K, h)), to, layer: "fx:spark", size: 0.08, ms: 600 + i * 60, trail: "fx:spark", arc: 0.25, then: () => K.fxs.drift({ at: to, n: 5, size: 0.05, rise: 0.4, ms: 1100 }) }); }); return true;
      case "thorns": foes.forEach((m, i) => wait(i * 60, () => { const at = K.atFoe(m, 0.05); if (!at) return; K.fxs.burst({ at, layer: "fx:leaf", n: 10, size: 0.1, speed: 0.9, up: 2.6, gravity: 4 }); if (!CM.reducedMotion) K.fxs.ground({ at: [at[0], 0, at[2]], layer: "fx:leaf", size: 0.8, ms: 3000, alpha: 0.8 }); })); return true;
      case "entangle": { const at = K.atFoe(foe, 0.05); if (!at) return false; K.fxs.burst({ at, layer: "fx:leaf", n: 14, size: 0.1, speed: 0.7, up: 2.4, gravity: 4 }); if (!CM.reducedMotion) K.fxs.ground({ at: [at[0], 0, at[2]], layer: "fx:leaf", motes: "fx:leaf", size: 0.9, ms: 3600, alpha: 0.85 }); return true; }
      case "drain": { const from = K.atFoe(foe, 0.55); if (!from) return false; impact(K, from, "dark", { n: 8, ring: 0.7, noTint: true });
        K.fxs.projectile({ from, to: K.fromParty(sideOf(K, h)), layer: "fx:fire", size: 0.15, ms: 420, trail: "fx:shard", arc: 0.1, then: () => K.ui.tint(TINT.dark, 300) }); return true; }
      case "hex": case "mockery": case "mark": { const at = K.atFoe(foe, 0.9); if (!at) return false; bolt(K, h, foe, "force", { size: 0.1, ms: 240, h: 0.9, n: 5, ring: 0.5, noTint: true }); wait(240, () => K.fxs.drift({ at, n: 6, size: 0.05, rise: 0.25, ms: 700 })); return true; }
      case "deathpact": foes.forEach((m, i) => wait(i * 50, () => bolt(K, h, m, "dark", { size: 0.14, ms: 300, noTint: i > 0 }))); holdFor(K, foes.length * 50 + 300); return true;
      case "firework": foes.forEach((m, i) => wait(i * 80, () => bolt(K, h, m, i % 2 ? "holy" : "fire", { size: 0.12, ms: 420, arc: 0.45, n: 16, speed: 1.8, noTint: true }))); holdFor(K, foes.length * 80 + 420); return true;
      case "heal": case "cure": case "lay": case "raise": onParty(K, h, "fx:holy", "rgba(255,240,180,0.25)"); return true;
      case "mend": case "regrowth": onParty(K, h, "fx:leaf", "rgba(160,240,140,0.22)"); return true;
      case "bless": case "rally": case "song": case "lift": onParty(K, h, "fx:spark", "rgba(255,230,150,0.25)"); return true;
      case "protection": onParty(K, h, "fx:frost", "rgba(140,180,255,0.3)"); return true;
      case "sanctuary": { const at = K.beforeParty(0.5); K.fxs.ring({ at: [at[0], 0, at[2]], to: 1.8, ms: 900 }); if (!CM.reducedMotion) K.fxs.ground({ at: [at[0], 0, at[2]], layer: "fx:holy", motes: "fx:holy", size: 1.2, ms: 3000, alpha: 0.5 }); K.ui.tint("rgba(140,180,255,0.3)", 600); return true; }
      default: return false;
    }
  };
}
