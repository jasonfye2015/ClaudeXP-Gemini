"use strict";
// Cooking, wider (v32.0, UPGRADE_PLAN_27.md): the South Fields' crops and the deep's edible finds into fifteen new
// dishes; a feast at a camp's fire or the home's table - two or three different dishes eaten together, all their good
// at once for as long as the shortest of them lasts; and a recipe book kept in the village (every dish made, ever).
//   game.layFeast(rows)  -> "" or why not;  game.recipesKnown() -> {id: true};  CM.FEAST_MOST
{ const NEW = {
    potatohash: { name: "Potato Hash", needs: ["potato", "onion"], floors: 2, effect: { df: 1 }, what: "+1 defence" },
    leeksoup: { name: "Leek and Potato Soup", needs: ["potato", "leek"], floors: 2, effect: { regen: 1, resist: "sleep" }, what: "mends 1 a round, and sleep finds no purchase" },
    carrotcake: { name: "Carrot Cake", needs: ["flour", "carrot", "egg"], floors: 2, effect: { morale: 6, stat: "dex" }, what: "the heart lifts, and +1 Grace" },
    tomatostew: { name: "Tomato Stew", needs: ["tomato", "beans", "garlic"], floors: 2, effect: { atk: 1, df: 1 }, what: "+1 attack and +1 defence" },
    pumpkin: { name: "Stuffed Pumpkin", needs: ["pumpkin", "meat", "onion"], floors: 3, effect: { atk: 1, df: 1, regen: 1 }, what: "+1 attack, +1 defence and mending, three floors" },
    cornbread: { name: "Corn Bread", needs: ["corn", "egg"], floors: 2, effect: { df: 1, torch: true }, what: "+1 defence, and the torch burns slower" },
    chili: { name: "Chili Pot", needs: ["chili", "beans", "meat"], floors: 2, effect: { atk: 2, morale: 4 }, what: "+2 attack, and the heart lifts" },
    garlicbroth: { name: "Garlic Broth", needs: ["garlic", "celery"], floors: 2, effect: { resist: "poison", regen: 1 }, what: "poison finds no purchase, and mending" },
    strawberries: { name: "Strawberries and Cream", needs: ["strawberry", "milk"], floors: 1, effect: { morale: 8, luck: 1 }, what: "the heart high, and +1 Luck" },
    grapemust: { name: "Grape Must", needs: ["grapes", "honey"], floors: 1, effect: { morale: 4, stat: "wis" }, what: "the heart lifts, and +1 Faith" },
    saltcrisps: { name: "Salt-weed Crisps", needs: ["saltweed", "potato"], floors: 2, effect: { hit: 0.05, torch: true }, what: "blows land a twentieth more, and the torch burns slower" },
    sporepie: { name: "Spore-cap Pie", needs: ["sporecap", "flour", "egg"], floors: 2, effect: { resist: "poison", df: 1 }, what: "poison finds no purchase, and +1 defence" },
    sapham: { name: "Sap-glazed Ham", needs: ["rootsap", "meat"], floors: 3, effect: { regen: 2, atk: 1 }, what: "mends 2 a round, and +1 attack, three floors" },
    ghostsoup: { name: "Ghost-cap Soup", needs: ["ghostcap", "cabbage"], floors: 2, effect: { stat: "int", resist: "sleep" }, what: "+1 Wit, and sleep finds no purchase" },
    harvestpie: { name: "Harvest Pie", needs: ["pumpkin", "flour", "egg", "apple"], floors: 3, effect: { morale: 10, luck: 1, df: 1 }, what: "the heart high, +1 Luck and +1 defence, three floors" },
  };
  for (const [id, D] of Object.entries(NEW)) { CM.DISHES[id] = D; CM.BASES[D.name] = { id: D.name, kind: "dish", slot: null, tier: D.floors, group: "stuff" }; }
  CM.FEAST_MOST = 3;
  // a feast's good: every dish's, together (numbers added, the first stat and the first resistance kept)
  CM.feastEffect = (ids) => { const out = {}; for (const id of ids) { const e = (CM.DISHES[id] || {}).effect || {}; for (const [k, v] of Object.entries(e)) {
      if (typeof v === "number") out[k] = (out[k] || 0) + v; else if (typeof v === "boolean") out[k] = out[k] || v; else if (out[k] === undefined) out[k] = v; } } return out; };
  const meal0 = CM.mealOf; CM.mealOf = (game) => { const m = game && game.meal; if (m && m.feast) return CM.feastEffect(m.feast); return meal0(game); };
  const G = CM.Game.prototype, cook0 = G.cookDish;
  Object.assign(G, {
    recipesKnown() { const v = this.vext("recipes"); return v; },
    cookDish(id) { const out = cook0.call(this, id); if (!out) { const k = this.recipesKnown(); if (!k[id]) { k[id] = true; this.saveVillage && this.saveVillage(); } } return out; },
    feastWhy(rows) { if (!(this.mode === "camp" || (this.inTown() && this.homeLevel && this.homeLevel() >= 3))) return "A feast is laid at a camp's fire or the home's table.";
      if (!Array.isArray(rows) || rows.length < 2 || rows.length > CM.FEAST_MOST) return `A feast is two or three dishes.`;
      const its = rows.map((r) => this.bag[r]); if (its.some((it) => !it || it.kind !== "dish" || !CM.DISHES[it.dish])) return "Only dishes go on the table.";
      if (new Set(its.map((it) => it.dish)).size !== its.length) return "A feast is different dishes."; if (new Set(rows).size !== rows.length) return "Each dish once.";
      return ""; },
    layFeast(rows) {
      const why = this.feastWhy(rows); if (why) return why; this.logAct && this.logAct("layFeast", rows);
      const its = rows.map((r) => this.bag[r]), ids = its.map((it) => it.dish), cookLv = this.cookLevel();
      const floors = Math.min(...its.map((it) => CM.DISHES[it.dish].floors + (it.by ? (this.party.find((h) => h.name === it.by && h.cook) || { cook: { level: 0 } }).cook.level : cookLv)));
      for (const r of rows.slice().sort((a, b) => b - a)) this.bag.splice(r, 1);
      const E = CM.feastEffect(ids), was = this.meal; this.fed = 0; this.cheer(6 + (E.morale || 0));
      this.meal = { kind: ids[0], dish: true, feast: ids, floor: (this.floor ? this.floor.number : 0) + floors - 1 + (this.inTown() ? 1 : 0) };
      for (const h of this.party) { h.mealLuck = E.luck || 0; h.mealStat = E.stat || null; CM.recompute(h); }
      const fans = this.party.filter((h) => h.hp > 0 && ids.includes(CM.favouriteOf(h))); if (fans.length) this.cheer(2 * fans.length);
      this.tally.feasts = (this.tally.feasts || 0) + 1; this.countUse && this.countUse("dish");
      this.sound("heal"); this.say(`A feast: ${ids.map((id) => CM.DISHES[id].name.toLowerCase()).join(", ")}. All of it does its good together, for ${CM.plural(floors, "floor")}${was ? " (the last meal is forgotten)" : ""}.${fans.length ? ` ${fans.map((h) => h.name).join(" and ")} find${fans.length === 1 ? "s" : ""} a favourite on the table.` : ""}`);
      this.saveRun(); this.emit("change"); return ""; },
  });
  CM.ACHIEVEMENTS.feast = { name: "A Groaning Table", what: "Lay a feast of three dishes", title: "the Generous" };
  const lay0 = G.layFeast; G.layFeast = function (rows) { const out = lay0.call(this, rows); if (!out && rows.length === 3 && this.achieve) this.achieve("feast"); return out; };
}
