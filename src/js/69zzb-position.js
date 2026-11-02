"use strict";
// Positioning (v38.0, UPGRADE_PLAN_33.md): a weapon with the reach word (a halberd's own, 10-data.js) strikes from the
// back row at full, as a polearm in hand does; a shield turns some of the blows aimed at the hero beside its bearer in
// the same row (a third of its own chance, for half); two heroes of the front row who strike the same foe in one round
// flank it - the second blow a fifth harder.
//   CM.FLANK; CM.besideOf(game, hero)
{ CM.FLANK = 0.2;
  const G = CM.Game.prototype;
  CM.besideOf = (g, h) => { const row = g.party.filter((p) => p.hp > 0 && p.row === h.row && !p.thrall), i = row.indexOf(h); return [row[i - 1], row[i + 1]].filter(Boolean); };
  const st0 = G.strike; G.strike = function (hero, target, note = "", opts = {}) {
    const w = hero && hero.weapon && !hero.weapon.unknown ? hero.weapon.props || {} : {}, reach = w.reach && hero.row === "back" && !(CM.atHome(hero, hero.weapon) && CM.weaponClass(hero.weapon) === "polearm"), row0 = hero ? hero.row : null;
    if (reach) hero.row = "front";   /* (reaching from the back as if from the front: the polearm's rule, for the reach word) */
    let out; const c = this.combat || {}, was = target ? target.hp : 0;
    try { out = st0.call(this, hero, target, note, opts); } finally { if (reach) hero.row = row0; }
    if (target && hero && row0 === "front" && out > 0 && target.hp > 0) { const F = c.flank = c.flank && c.flank.round === c.round ? c.flank : { round: c.round, by: new Map() };
      const first = F.by.get(target); if (first && first !== hero && first.row === "front") { const more = Math.max(1, Math.round(out * CM.FLANK)); target.hp = Math.max(1, target.hp - more);   /* (the flank wounds; the next blow kills) */ this.say(`${hero.name} and ${first.name} have ${CM.the(target)} between them: ${more} more.`); this.tally.flanks = (this.tally.flanks || 0) + 1; }
      else if (!first) F.by.set(target, hero); }
    return out; };
  const hurt0 = G.hurt; G.hurt = function (h, dmg, by, opts = {}) {
    if (h && !h.thrall && !opts.aoe && !opts.noBlock && !(h.offhand && h.offhand.kind === "shield") && this.party) { const nb = CM.besideOf(this, h).find((p) => p.offhand && p.offhand.kind === "shield" && !p.offhand.unknown && this.canAct(p));
      if (nb && this.rnd.chance(CM.blockChance(nb.offhand) / 3)) { dmg = Math.max(1, Math.ceil(dmg / 2)); opts = Object.assign({}, opts, { how: (opts.how || "") + ` - ${nb.name}'s shield catches the edge of it` }); this.tally.shieldsBeside = (this.tally.shieldsBeside || 0) + 1; } }
    return hurt0.call(this, h, dmg, by, opts); };
}
