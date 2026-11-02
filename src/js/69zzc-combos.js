"use strict";
// Combos, more (v38.1, UPGRADE_PLAN_33.md): four more, each from two blows one after the other on the same foe in a round,
// kept with the rest (CM.COMBOS; the journal finds them). The feint: a blow from one hero, then the Rogue's - a sure weak
// spot (the Rogue's blow again as much). The volley: a shot, then another's: half again. Smite and sear: holy light on a
// foe, then fire: half again. Hammer and anvil: the Knight's shield bash, then a blow from another hero: a third again.
//   game.combat.lastHit = {who, target, kind, round}
{ Object.assign(CM.COMBOS, {
    feint: { name: "The feint", what: "One hero draws the guard, and the Rogue's blow that follows finds the weak spot: as much again." },
    volley: { name: "Volley", what: "A shot, and another's straight after it into the same foe: half again." },
    smitesear: { name: "Smite and sear", what: "Holy light opens a foe, and fire after it burns the wound: half again." },
    anvil: { name: "Hammer and anvil", what: "The Knight's shield bash, and a blow from another into the reeling foe: a third again." } });
  const G = CM.Game.prototype, bowOf = (h) => Boolean(h && h.weapon && !h.weapon.unknown && (h.weapon.props || {}).bow);
  const bonus = (g, target, extra, id) => { if (extra <= 0 || !target || target.hp <= 0) return; target.hp = Math.max(1, target.hp - extra); g.combo(id);   /* (the combo wounds deep; the killing blow is still a blow) */ g.say(`${CM.COMBOS[id].name}: ${extra} more.`); g.tally.combos2 = (g.tally.combos2 || 0) + 1; };
  const st0 = G.strike; G.strike = function (hero, target, note = "", opts = {}) { const c = this.combat || {}, L = c.lastHit, out = st0.call(this, hero, target, note, opts);
    if (out > 0 && target && L && L.round === c.round && L.target === target && L.who !== hero) {
      if (hero.cls === "Rogue" && L.kind === "blow") bonus(this, target, out, "feint");
      else if (bowOf(hero) && L.kind === "shot") bonus(this, target, Math.ceil(out / 2), "volley");
      else if (L.kind === "bash") bonus(this, target, Math.ceil(out / 3), "anvil"); }
    if (out > 0 && target) c.lastHit = { who: hero, target, kind: opts.bash ? "bash" : bowOf(hero) ? "shot" : "blow", round: c.round };
    return out; };
  const sh0 = G.spellHit; G.spellHit = function (foe, dmg, what, element, chained) { const c = this.combat || {}, L = c.lastHit, out = sh0.call(this, foe, dmg, what, element, chained);
    if (foe && L && L.round === c.round && L.target === foe && L.kind === "holy" && element === "fire" && out > 0) bonus(this, foe, Math.ceil(out / 2), "smitesear");
    if (foe && !chained) c.lastHit = { who: null, target: foe, kind: element === "holy" ? "holy" : "spell", round: c.round };
    return out; };
}
