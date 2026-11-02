"use strict";
// Gear compared (v25.2, UPGRADE_PLAN_20.md): what a hero's numbers would be wearing a thing in place of what they wear
// now - worked out by trying it on (and taking it off again: nothing about the hero changes, health and magic
// included). CM.gearCompare(game, h, item) -> { rows: [[label, before, after, kind]], gain, why } with only the numbers
// that move; CM.gearBest(game, item) -> the hero it suits best and how each of the party would take it. The window's
// tooltip shows them (76zzzzl-tips.js).
{ const GEAR = ["weapon", "armor", "shield", "helm", "ring", "amulet", "trinket", "boots", "cloak"], ARMOUR = ["armor", "offhand", "helm", "boots", "cloak"];
  const slotOf = (it) => it.slot || (it.kind === "shield" ? "offhand" : it.kind);
  const sheet = (g, h) => { const w = h.weapon || {}, s = {}; for (const st of CM.STATS) s[st] = CM.heroStat(h, st);
    return { atk: h.atk, blow: (w.power || 0) + CM.gearProp(h, "power1"), armour: ARMOUR.reduce((a, k) => a + ((h[k] && !h[k].unknown && h[k].power) || 0), 0), hp: h.max, mp: h.maxmp || 0,
      hit: Math.round(g.hitChance(h) * 100), crit: Math.round(g.critChance(h) * 100), block: Math.round(CM.blockChance(h.offhand) * 100), score: CM.itemScore ? CM.gearScore(h) : 0, ...s }; };
  const LABELS = [["atk", "Attack"], ["blow", "Weapon"], ["armour", "Armour"], ["hp", "Health"], ["mp", "Magic"], ["str", "Str"], ["dex", "Dex"], ["con", "Con"], ["int", "Int"], ["wis", "Wis"], ["luck", "Luck"],
    ["hit", "To hit %"], ["crit", "Crit %"], ["block", "Block %"], ["score", "Gear score"]];
  CM.gearCompare = (g, h, item) => {
    if (!item || !GEAR.includes(item.kind) || !h) return null;
    const why = CM.cantWear(h, item); if (why) return { rows: [], gain: null, why };
    if (item.unknown) return { rows: [], gain: null, why: "Unknown: what it does is only known once it is worn or read" };
    const slot = slotOf(item), old = h[slot], off = h.offhand, two = slot === "weapon" && item.props && item.props.twohanded && off, hp = h.hp, mp = h.mp, before = sheet(g, h);
    try { h[slot] = item; if (two) h.offhand = null; CM.recompute(h); var after = sheet(g, h); }
    finally { h[slot] = old; h.offhand = off; CM.recompute(h); h.hp = hp; h.mp = mp; }
    const rows = LABELS.filter(([k]) => before[k] !== after[k]).map(([k, label]) => [label, before[k], after[k], k]);
    return { rows, gain: after.score - before.score, was: old || null, two: Boolean(two), why: "" };
  };
  CM.gearBest = (g, item) => {
    if (!item || !GEAR.includes(item.kind)) return null;
    const each = g.party.map((h) => ({ h, c: CM.gearCompare(g, h, item) }));
    const fit = each.filter((e) => e.c && e.c.gain !== null && e.h.hp > 0).sort((a, b) => b.c.gain - a.c.gain);
    return { best: fit[0] || each.find((e) => e.c && !e.c.why) || each[0], each };
  };
}
