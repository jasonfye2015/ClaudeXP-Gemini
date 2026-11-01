"use strict";
// The skill trees (v18.2): every calling has three branches to grow along, a skill point for each level gained (so a
// hero already at level 12 has eleven to spend), and fifteen ranks a branch across five tiers - a tier opens when two
// more points are spent in its branch than the tier before (the fifth needs eight, and level 15). What a rank gives is
// what the game already reckons with - a stat, attack, defence, health, magic, the gear's own kinds of bonus (to hit,
// weak spots, spell power, mending each round, thorns, quickness, mana and health from each kill, gold and experience)
// - so it bites everywhere a ring or a blade would. The capstones: two branches end in the traits of the path the hero
// didn't choose at level 5 (its first, and its second), and the third in a presence that steadies the whole party. The
// warriors' branches lean on blows, the casters' on spells. A tree can be unlearned for nothing in town, and spent again.
// The window is 76zzzd-skilltree.js.
{ const ST = CM.SKILLTREE = { tiers: [0, 2, 4, 6, 8], capLevel: 15 };
  const CASTERS = ["Cleric", "Mage", "Druid", "Bard", "Necromancer", "Artificer"];
  const SN = { str: "Strength", dex: "Dexterity", con: "Constitution", int: "Intelligence", wis: "Wisdom", luck: "Luck" };
  ST.NAMES = { Knight: ["The Blade", "The Shield", "The Banner"], Paladin: ["The Oath", "The Ward", "The Pilgrim"], Rogue: ["The Knife", "The Shadow", "The Purse"], Ranger: ["The Bow", "The Wild", "The Trail"],
    Cleric: ["The Word", "The Vigil", "The Flock"], Mage: ["The Flame", "The Ward-runes", "The Library"], Druid: ["The Thorn", "The Oak", "The Seasons"], Bard: ["The Song", "The Stage", "The Road"],
    Monk: ["The Fist", "The Stillness", "The Way"], Necromancer: ["The Grave", "The Bone", "The Bargain"], Artificer: ["The Engine", "The Plating", "The Workshop"] };
  // the three branches, shaped for the calling: [id, name, what, ranks, effect per rank]
  ST.branches = (cls) => { const c = CM.CLASSES[cls] || CM.CLASSES.Knight, key = c.key, caster = CASTERS.includes(cls), N = ST.NAMES[cls] || ST.NAMES.Knight;
    const off = caster ? [["a1", `Studied ${SN[key]}`, `+1 ${SN[key]}`, 3, { stat: { [key]: 1 } }], ["a2", "Deeper Power", "+1 to every spell", 3, { prop: { spellPower: 1 } }], ["a3", "Wellspring", "+4 magic", 2, { mp: 4 }], ["a4", "Feast on the Fallen", "+1 magic back for each foe slain", 2, { prop: { killMana: 1 } }]]
      : [["a1", `Trained ${SN[key]}`, `+1 ${SN[key]}`, 3, { stat: { [key]: 1 } }], ["a2", "Heavy Blows", "+1 attack", 3, { atk: 1 }], ["a3", "Find the Gap", "+4% weak spots (critical hits)", 2, { prop: { crit: 0.04 } }], ["a4", "Drilled", "+5% to hit", 2, { prop: { hitBonus: 0.05 } }]];
    const def = [["b1", "Hardened", "+1 Constitution", 3, { stat: { con: 1 } }], ["b2", "Braced", "+1 defence", 3, { df: 1 }], ["b3", "Deep Reserves", "+6 health", 2, { hp: 6 }], ["b4", "Second Breath", "+1 health mended each round of a fight", 2, { prop: { regen: 1 } }]];
    const luck = [["c1", "Born Lucky", "+1 Luck", 3, { stat: { luck: 1 } }], ["c2", "Quick Study", "+4% experience from fights", 3, { prop: { xpBonus: 0.04 } }], ["c3", "Light Fingers", "+5% gold from fights", 2, { prop: { killGold: 0.05 } }], ["c4", "First to Move", "+2 quickness in a fight", 2, { prop: { init: 2 } }]];
    const cap = (id, which) => [id, which === 3 ? "Steady Presence" : "The Other Road", which === 3 ? "+1 defence to the whole party, and +1 to every stat" : `The ${which === 1 ? "first" : "second"} trait of the path not taken`, 1, which === 3 ? { prop: { auraDf: 1 }, stat: { str: 1, dex: 1, con: 1, int: 1, wis: 1, luck: 1 } } : { other: which }];
    return [{ id: "a", name: N[0], what: caster ? "Spells, and the power behind them" : "Blows, and where they land", nodes: off.concat([cap("a5", 1)]) },
      { id: "b", name: N[1], what: "Standing up to it", nodes: def.concat([cap("b5", 2)]) }, { id: "c", name: N[2], what: "Luck, learning, and the spoils", nodes: luck.concat([cap("c5", 3)]) }]; };
  ST.node = (cls, id) => { for (const B of ST.branches(cls)) for (const [k, ...rest] of B.nodes.map((n) => n)) if (k === id) return [k, ...rest]; return null; };
  ST.points = (h) => Math.max(0, (h.level || 1) - 1);
  ST.spent = (h) => Object.values(h.tree || {}).reduce((a, b) => a + b, 0);
  ST.inBranch = (h, b) => Object.entries(h.tree || {}).filter(([k]) => k[0] === b).reduce((a, [, v]) => a + v, 0);
  // the path the hero didn't take, and its trait for a capstone
  ST.otherTrait = (h, which) => { const P = CM.PATHS[h.cls]; if (!P || !h.path) return null; const other = Object.keys(P).find((k) => k !== h.path); const T = other && P[other][which === 1 ? "t1" : "t2"]; return T || null; };
  // can this rank be taken now? "" if so, else why not
  ST.why = (h, id) => { const n = ST.node(h.cls, id); if (!n) return "No such skill."; const [k, , , max] = n, tier = Number(k[1]) - 1, have = (h.tree || {})[k] || 0;
    if (have >= max) return "Learned in full."; if (ST.spent(h) >= ST.points(h)) return "No skill points left - one comes with each level gained.";
    if (ST.inBranch(h, k[0]) < ST.tiers[tier]) return `Spend ${ST.tiers[tier]} points in this branch to reach it.`;
    if (tier === 4 && h.level < ST.capLevel) return `The capstone opens at level ${ST.capLevel}.`; if (n[4].other && !ST.otherTrait(h, n[4].other)) return "Choose your path first (at level 5): this teaches a trait of the other one.";
    return ""; };
  // what the tree gives a hero, summed
  ST.sum = (h) => { const t = h && h.tree; if (!t || !Object.keys(t).length) return null; const out = { stat: {}, prop: {}, atk: 0, df: 0, hp: 0, mp: 0, traits: [] };
    for (const [k, r] of Object.entries(t)) { if (!r) continue; const n = ST.node(h.cls, k); if (!n) continue; const E = n[4];
      for (const [s, v] of Object.entries(E.stat || {})) out.stat[s] = (out.stat[s] || 0) + v * r; for (const [p, v] of Object.entries(E.prop || {})) out.prop[p] = (out.prop[p] || 0) + v * r;
      out.atk += (E.atk || 0) * r; out.df += (E.df || 0) * r; out.hp += (E.hp || 0) * r; out.mp += (E.mp || 0) * r; if (E.other) { const T = ST.otherTrait(h, E.other); if (T) out.traits.push(T.id); } }
    return out; };
  // ---- into the game's own reckonings ----
  { const hs0 = CM.heroStat; CM.heroStat = function (h, s) { const v = hs0(h, s), S = ST.sum(h); return S && S.stat[s] ? v + S.stat[s] : v; }; }
  { const gp0 = CM.gearProp; CM.gearProp = (h, prop) => { const v = gp0(h, prop), S = ST.sum(h); return S && S.prop[prop] ? v + S.prop[prop] : v; }; }
  { const tr0 = CM.trait; CM.trait = function (h, id) { if (tr0(h, id)) return true; const S = ST.sum(h); return !!(S && S.traits.includes(id)); }; }
  { const rc0 = CM.recompute; CM.recompute = function (h) { rc0(h); const S = ST.sum(h); if (S) { h.atk += S.atk; h.df += S.df; h.max += S.hp; if (h.maxmp || S.mp) h.maxmp += S.mp; h.hp = Math.min(h.hp, h.max); h.mp = Math.min(h.mp, h.maxmp); } return h; }; }
  Object.assign(CM.Game.prototype, {
    tsLearn(hero, id) { const h = typeof hero === "number" ? this.party[hero] : hero; if (!h) return "No such hero."; const why = ST.why(h, id); if (why) return why;
      this.logAct && this.logAct("tsLearn", this.party.indexOf(h), id); h.tree = h.tree || {}; h.tree[id] = (h.tree[id] || 0) + 1; const ratio = h.max ? h.hp / h.max : 1; CM.recompute(h); h.hp = Math.max(1, Math.round(h.max * ratio)); this.sound && this.sound("spell"); this.emit && this.emit("change"); return ""; },
    tsReset(hero) { const h = typeof hero === "number" ? this.party[hero] : hero; if (!h) return "No such hero."; if (this.inTown && !this.inTown()) return "Unlearning a tree takes quiet: in town, at home."; if (!ST.spent(h)) return "Nothing learned yet.";
      this.logAct && this.logAct("tsReset", this.party.indexOf(h)); h.tree = {}; CM.recompute(h); this.emit && this.emit("change"); return ""; },
  });
}
