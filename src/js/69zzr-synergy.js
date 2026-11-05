"use strict";
// The combat synergies (v79.0, UPGRADE_PLAN_61.md part 9): the weather is in the fight. Under a storm on the
// surface, lightning spells bite a quarter harder and the storm's own bolt leaps on to a second foe for half (as
// the water's chain does below - and standing in floodwater counts as water now, 69zzq-below.js); in rain or a
// storm, fire spells bite a quarter less and leave no burning behind; an arrow or a bolt shot into a headwind is
// harder to land and falls a point short, with a tailwind easier and a point longer.
//   CM.weatherMods(game, element) -> { mult, chain, word }      the spell's weather, by element
//   CM.windMods(game, hero) -> { hit, dmg, word }               a bow's wind, by the facing against the wind's way
{ const S = CM.SYNERGY = { stormMult: 1.25, rainFire: 0.75, windFrom: 0.5, headHit: 0.85, tailHit: 1.15 };
  const surface = (game) => game && game.floor && (game.floor.number === 0 || game.floor.number === -1);
  CM.weatherMods = (game, element) => { const none = { mult: 1, chain: false, word: "" }; if (!game || !game.ext || !surface(game) || !element) return none; const W = CM.weatherNow(game);
    if (element === "storm" && W.kind === "storm" && W.strength > 0.2) return { mult: S.stormMult, chain: true, word: " - the storm carries it" };
    if (element === "fire" && (W.kind === "rain" || W.kind === "storm") && W.strength > 0.2) return { mult: S.rainFire, chain: false, word: " - the rain damps it" };
    return none; };
  CM.windMods = (game, hero) => { const none = { hit: 1, dmg: 0, word: "" }; if (!game || !game.ext || !surface(game) || !hero || !hero.weapon || !hero.weapon.props || !hero.weapon.props.bow) return none; const W = CM.weatherNow(game); if (W.wind.speed < S.windFrom) return none;
    const fl = game.floor, [dx, dy] = CM.DIRS[fl.facing || 0], dot = dx * W.wind.dir[0] + dy * W.wind.dir[1];
    if (dot < -0.5) return { hit: S.headHit, dmg: -1, word: " into the wind" }; if (dot > 0.5) return { hit: S.tailHit, dmg: 1, word: " on the wind" }; return none; };
  const P = CM.Game.prototype;
  // floodwater underfoot is water for the fight's terrain
  { const t0 = P.terrain; P.terrain = function () { const out = t0.call(this); if (CM.floodedHere && CM.floodedHere(this) && !out.includes("water")) out.push("water"); return out; }; }
  // the spell: its weather, and the storm's own chain
  { const sh0 = P.spellHit; P.spellHit = function (foe, dmg, what, element, chained, ...rest) { const M = chained ? { mult: 1, chain: false, word: "" } : CM.weatherMods(this, element); if (M.mult !== 1) { dmg = Math.max(1, Math.ceil(dmg * M.mult)); if (what) what += M.word; }
      const out = sh0.call(this, foe, dmg, what, element, chained, ...rest);
      if (element === "fire" && M.mult < 1 && foe && foe.burning) { foe.burning = 0; foe.burnDmg = 0; }   // (no fire holds in the rain)
      if (M.chain && !chained && !this.terrain().includes("water") && foe && this.living) { const other = this.living().find((f) => f !== foe && !f.hidden); if (other) { this.emit("fx", { kind: "stormchain", from: foe, to: other }); this.spellHit(other, Math.max(1, Math.ceil(dmg / 2)), "The storm's own lightning leaps on to", "storm", true); } }
      return out; }; }
  // the bow: the wind against the facing
  { const hc0 = P.hitChance; P.hitChance = function (h, ...rest) { const c = hc0.call(this, h, ...rest), M = CM.windMods(this, h); return M.hit !== 1 ? Math.max(0.05, Math.min(1, c * M.hit)) : c; }; }
  { const st0 = P.strike; P.strike = function (hero, target, note = "", opts = {}) { const M = CM.windMods(this, hero); if (M.word && !(this.combat && this.combat.windSaid)) { if (this.combat) this.combat.windSaid = true; this.say(M.dmg < 0 ? `The wind is in ${hero.name}'s face: the arrows fall short.` : `The wind is at ${hero.name}'s back: the arrows fly long.`); }
      const out = st0.call(this, hero, target, note, opts); if (M.dmg && out > 0 && target && target.hp > 0) { if (M.dmg < 0) target.hp += 1; else target.hp -= 1; } return out; }; }
}
