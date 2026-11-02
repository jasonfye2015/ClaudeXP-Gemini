"use strict";
// Scars and stories (v34.2, UPGRADE_PLAN_29.md): a hero brought to a tenth of their health or less in a fight, and
// still standing when it is won, keeps a scar - three at most - with where it is, what gave it and on which floor. A
// scar is a small trait for good, one of six, two of them double-edged: Hardened (+1 Constitution), Watchful (+1
// Dexterity), Lucky to be Alive (+1 Luck), Grim (+1 Strength, -1 Wisdom), Shaken (+1 Wisdom, -1 Dexterity), Slow to
// Heal (+1 Intelligence, -1 Constitution). The portrait shows it; the sheet tells it (76zzzzzzd-scars.js).
//   h.marks = [{where, by, floor, trait}] (v37.5: their own list - h.scars is the camp's healed-wound scars, 63-camp.js);  CM.SCAR_TRAITS
{ CM.SCAR_TRAITS = {
    hardened: { name: "Hardened", stats: { con: 1 }, what: "+1 Constitution" }, watchful: { name: "Watchful", stats: { dex: 1 }, what: "+1 Dexterity" },
    lucky: { name: "Lucky to be Alive", stats: { luck: 1 }, what: "+1 Luck" }, grim: { name: "Grim", stats: { str: 1, wis: -1 }, what: "+1 Strength, -1 Wisdom" },
    shaken: { name: "Shaken", stats: { wis: 1, dex: -1 }, what: "+1 Wisdom, -1 Dexterity" }, slow: { name: "Slow to Heal", stats: { int: 1, con: -1 }, what: "+1 Intelligence, -1 Constitution" } };
  CM.SCAR_PLACES = ["across the brow", "down the cheek", "along the jaw", "through the eyebrow", "under the eye", "at the temple"];
  CM.SCARS_MOST = 3; CM.SCAR_AT = 0.1;
  const G = CM.Game.prototype;
  const hurt0 = G.hurt; G.hurt = function (h, dmg, by, opts) { const out = hurt0.call(this, h, dmg, by, opts);
    if (h && !h.thrall && h.hp > 0 && h.hp <= h.max * CM.SCAR_AT && !h.nearDeath) h.nearDeath = { by: by ? (by.name || by.kind || "something") : "something", floor: this.floor ? this.floor.number : 0, element: opts && opts.element };
    return out; };
  G.giveScar = function (h, why) { h.marks = h.marks || []; if (h.marks.length >= CM.SCARS_MOST) return null;
    const ids = Object.keys(CM.SCAR_TRAITS), k = CM.hashSeed(`${this.seed}:scar:${h.name}:${h.marks.length}:${why.floor}`), trait = ids[k % ids.length], where = CM.SCAR_PLACES[(k >>> 4) % CM.SCAR_PLACES.length];
    const T = CM.SCAR_TRAITS[trait]; for (const [s, d] of Object.entries(T.stats)) h.stats[s] = Math.max(1, Math.min(25, h.stats[s] + d)); CM.recompute(h);
    const S = { where, by: why.by, floor: why.floor, trait, burn: why.element === "fire" }; h.marks.push(S); this.tally.marks = (this.tally.marks || 0) + 1;
    this.say(`${h.name} lived through it, and will carry it: a scar ${where}, from ${why.by.startsWith("The ") ? why.by : CM.the ? CM.the({ name: why.by }) : why.by} on floor ${why.floor}. ${T.name}: ${T.what}.`);
    if (h.marks.length >= CM.SCARS_MOST && this.achieve) this.achieve("scarred"); return S; };
  CM.ACHIEVEMENTS.scarred = { name: "Map of Old Wounds", what: "A hero with three scars", title: "the Scarred" };
  const wf0 = G.wonFight; G.wonFight = function (...a) { const near = (this.party || []).map((h) => h.nearDeath), out = wf0.apply(this, a); (this.party || []).forEach((h, i) => { if (near[i] && h.hp > 0) this.giveScar(h, near[i]); delete h.nearDeath; }); return out; };
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "mode" && a[0] === "explore") for (const h of this.party || []) delete h.nearDeath; return em0.call(this, ev, ...a); };   /* (a fight fled or lost: no scar from it) */
  // (v37.5) a hero from v34.2 - v37.4 kept these in h.scars, beside the camp's ids: moved to their own list
  CM.splitMarks = (h) => { if (!h || !Array.isArray(h.scars) || !h.scars.some((s) => s && typeof s === "object")) return h; h.marks = (h.marks || []).concat(h.scars.filter((s) => s && typeof s === "object")); h.scars = h.scars.filter((s) => typeof s === "string"); return h; };
  const up0 = CM.upgradeHero; if (up0) CM.upgradeHero = function (h, ...a) { return up0.call(this, CM.splitMarks(h), ...a); };
}
