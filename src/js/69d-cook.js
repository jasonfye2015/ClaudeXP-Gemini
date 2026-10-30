"use strict";
// Cooking as a trade (the eighth big update, phase 6): CM.DISHES, thirty-odd dishes from the farm's, the Wood's and the
// dungeon's things, made at the home's kitchen, at a camp's fire, or on the floor by a cook of the third level (a
// torch's fire). A dish travels: it is a thing in the pack that keeps two days, eaten at a camp or on the floor (Give
// it to anyone), and it feeds the party and does one thing besides for a floor count by the dish - the better dishes
// two. One dish at a time: eating another replaces it. A hero may take the apron (h.cook: a level every five dishes
// made; a cook's dishes last a floor longer a level). Every class and origin has a favourite: +2 morale and a line.
//
//   CM.DISHES[id]                      -> { name, needs, floors, effect, what }
//   CM.canCook(bag, id)                -> which rows the dish would take, or null
//   CM.mealOf(game)                    -> the meal's effect (a dish's, or an old meat meal's)
//   game.cookDish(id) / eatDish(row)   -> a dish made; a dish eaten
//   game.takeApron(heroIndex)          -> the cook
CM.DISHES = {
  bread: { name: "Bread", needs: ["flour"], floors: 1, effect: { df: 1 }, what: "+1 defence" },
  porridge: { name: "Porridge", needs: ["barley"], floors: 1, effect: { regen: 1 }, what: "mends 1 a round in fights" },
  omelette: { name: "Omelette", needs: ["egg", "egg"], floors: 1, effect: { hit: 0.05 }, what: "blows land a twentieth more" },
  stew: { name: "Stew", needs: ["meat", "turnip"], floors: 2, effect: { atk: 1 }, what: "+1 attack" },
  pie: { name: "Meat Pie", needs: ["meat", "flour", "egg"], floors: 2, effect: { atk: 1, df: 1 }, what: "+1 attack and +1 defence" },
  applecake: { name: "Apple Cake", needs: ["flour", "apple", "egg"], floors: 2, effect: { morale: 6, luck: 1 }, what: "the party's heart lifts, and +1 Luck" },
  roast: { name: "Roast Venison", needs: ["meat:Deer", "apple"], floors: 2, effect: { df: 2 }, what: "+2 defence" },
  honeycakes: { name: "Honey Cakes", needs: ["flour", "honey"], floors: 2, effect: { wind: true }, what: "a second wind: at a quarter health a hero mends a quarter, once a fight" },
  posset: { name: "Posset", needs: ["milk", "egg", "honey"], floors: 2, effect: { regen: 2, resist: "poison" }, what: "mends 2 a round, and poison finds no purchase" },
  beer: { name: "Beer", needs: ["malt", "hops"], floors: 1, effect: { morale: 10, atk: 1 }, what: "the party's heart high, and +1 attack" },
  cheese: { name: "Cheese", needs: ["milk", "milk"], floors: 3, effect: { torch: true }, what: "the torch burns slower" },
  hunters: { name: "Hunter's Breakfast", needs: ["egg", "meat", "flour"], floors: 2, effect: { atk: 1, hit: 0.05 }, what: "+1 attack, and blows land a twentieth more" },
  pasty: { name: "Miner's Pasty", needs: ["meat", "turnip", "flour"], floors: 3, effect: { df: 1 }, what: "+1 defence, and it keeps three floors" },
  fishsoup: { name: "Fisherman's Soup", needs: ["fish", "turnip"], floors: 2, effect: { torch: true, regen: 1 }, what: "the torch burns slower and the party mends 1 a round" },
  dwarfbread: { name: "Dwarven Bread, remade", needs: ["flour", "malt", "egg"], floors: 3, effect: { df: 1, stat: "con" }, what: "+1 defence and +1 Vigour, three floors" },
  queenscake: { name: "The Queen's Cake", needs: ["flour", "honey", "milk", "apple"], floors: 3, effect: { morale: 10, luck: 2, regen: 1 }, what: "the party's heart high, +2 Luck, and mending" },
  ratstick: { name: "Rat on a Stick", needs: ["meat:Giant Rat"], floors: 1, effect: { luck: 1 }, what: "+1 Luck" },
  koboldstew: { name: "Kobold Stew", needs: ["meat:Kobold", "turnip"], floors: 2, effect: { luck: 1, df: 1 }, what: "+1 Luck and +1 defence" },
  sporefry: { name: "Spore-cap Fry", needs: ["meat:Spore Beast", "mushroom"], floors: 2, effect: { torch: true, resist: "poison" }, what: "the torch burns slower, and poison finds no purchase" },
  trollheart: { name: "Troll's Heart", needs: ["meat:Troll", "honey"], floors: 2, effect: { regen: 2, wind: true }, what: "mends 2 a round, and a second wind" },
  pottage: { name: "Bean Pottage", needs: ["beans", "cabbage"], floors: 1, effect: { stat: "str" }, what: "+1 Might" },
  cabbagesoup: { name: "Cabbage Soup", needs: ["cabbage", "turnip"], floors: 1, effect: { resist: "poison" }, what: "poison finds no purchase" },
  berrytart: { name: "Berry Tart", needs: ["flour", "berries"], floors: 1, effect: { morale: 6, stat: "dex" }, what: "the heart lifts, and +1 Grace" },
  mushroomfry: { name: "Mushroom Fry", needs: ["mushroom", "mushroom"], floors: 1, effect: { stat: "wis" }, what: "+1 Faith" },
  herbbroth: { name: "Herb Broth", needs: ["woodherb", "turnip"], floors: 1, effect: { resist: "sleep", regen: 1 }, what: "sleep finds no purchase, and mending" },
  boarroast: { name: "Roast Boar", needs: ["meat:Boar", "beans"], floors: 2, effect: { atk: 2 }, what: "+2 attack" },
  wolfstew: { name: "Wolf Stew", needs: ["meat:Wolf", "turnip"], floors: 2, effect: { hit: 0.1 }, what: "blows land a tenth more" },
  bearham: { name: "Bear Ham", needs: ["meat:Bear", "honey"], floors: 3, effect: { atk: 1, df: 1, stat: "con" }, what: "+1 attack, +1 defence, +1 Vigour, three floors" },
  venisonpie: { name: "Venison Pie", needs: ["meat:Deer", "flour", "egg"], floors: 3, effect: { df: 2, morale: 4 }, what: "+2 defence, and the heart lifts" },
  pearhoney: { name: "Pears in Honey", needs: ["pear", "honey"], floors: 1, effect: { stat: "int" }, what: "+1 Wit" },
  eggflip: { name: "Egg Flip", needs: ["egg", "milk"], floors: 1, effect: { morale: 4, wind: true }, what: "the heart lifts, and a second wind" },
  fishpie: { name: "Fish Pie", needs: ["fish", "flour", "milk"], floors: 2, effect: { df: 1, torch: true }, what: "+1 defence, and the torch burns slower" },
};
CM.DISH_KEEPS = 2;                                                       // days a dish keeps in the pack
CM.DISH_VALUE = (id) => 10 + 10 * CM.DISHES[id].needs.length + 10 * CM.DISHES[id].floors;
CM.dish = (id) => ({ name: CM.DISHES[id].name, kind: "dish", dish: id, power: 0, value: CM.DISH_VALUE(id) });
for (const [id, D] of Object.entries(CM.DISHES)) CM.BASES[D.name] = { id: D.name, kind: "dish", slot: null, tier: D.floors, group: "stuff" };
CM.GROUP_NAMES.stuff = "Potions, stuff and dishes";
CM.INGREDIENTS.fish = { name: "River Fish", band: -1, food: true, keeps: 7 }; CM.BASES["River Fish"] = { id: "River Fish", kind: "ingredient", slot: null, tier: 0, group: "ingredient" }; CM.FOODS.fish = { name: "River Fish", keeps: 7 };
CM.WOOD_NODES.push(["the river's shallows, where fish rise", "nest"]);
CM.COOK_PER_LEVEL = 5; CM.COOK_MOST = 5; CM.COOK_FIELD = 3;
CM.FAVOURITES = {                                                        // by class and by origin: the dish that is home
  cls: { Knight: "pie", Mage: "pearhoney", Rogue: "ratstick", Cleric: "bread", Ranger: "roast", Necromancer: "koboldstew", Bard: "beer", Artificer: "pasty", Paladin: "posset", Druid: "mushroomfry", Monk: "porridge", Alchemist: "herbbroth", Warden: "stew", Witch: "trollheart", Hunter: "boarroast" },
  origin: { caerduin: "queenscake", dwarffriend: "dwarfbread", east: "fishsoup", order: "bread", lowertown: "eggflip", nobody: "cabbagesoup" },
  lines: { Knight: "a pie like the ones at the muster", Mage: "the college's own sweet", Rogue: "the lower town's supper, and no questions", Cleric: "bread broken, and a word said over it", Ranger: "the hunter's share", Necromancer: "an acquired taste, acquired", Bard: "a song's worth of beer", Artificer: "a pasty: a meal with a handle", Paladin: "the infirmary's posset", Druid: "the Wood's own", Monk: "the cloister's porridge", Alchemist: "a broth that is nearly a brew", Warden: "a stew like the watch-house's", Witch: "the heart of the thing", Hunter: "boar, as the hill does it",
    caerduin: "the Queen's cake, the way grandmother made it", dwarffriend: "the deep halls' bread, near enough", east: "the river soup of home", order: "the order's bread, and a silence", lowertown: "an egg flip, like the dock-tavern's", nobody: "cabbage soup: nobody's, so everybody's" },
};
CM.favouriteOf = (h) => (h.origin && CM.FAVOURITES.origin[h.origin]) || CM.FAVOURITES.cls[h.cls] || null;
// a need is an ingredient id, "meat" (any), or "meat:Kind"
CM.needMatch = (need, it) => { if (!it) return false; if (need === "meat") return it.kind === "meat"; if (need.startsWith("meat:")) return it.kind === "meat" && it.meat === need.slice(5); return it.kind === "ingredient" && it.ingredient === need; };
CM.canCook = function (bag, id) {
  const D = CM.DISHES[id]; if (!D) return null; const rows = [];
  for (const need of D.needs) { const row = bag.findIndex((it, i) => !rows.includes(i) && CM.needMatch(need, it)); if (row < 0) return null; rows.push(row); }
  return rows;
};
CM.needName = (need) => (need === "meat" ? "any meat" : need.startsWith("meat:") ? `${need.slice(5)} meat` : (CM.INGREDIENTS[need] || { name: need }).name.toLowerCase());
CM.mealOf = (game) => { const m = game && game.meal; if (!m) return {}; if (m.dish) return (CM.DISHES[m.kind] || {}).effect || {}; return CM.MEALS[m.kind] || {}; };
CM.ACHIEVEMENTS.cook = { name: "The Apron", what: "Raise a cook to the fifth level", title: "the Cook" };
Object.assign(CM.Game.prototype, {
  cookOf() { return this.party.find((h) => h.cook && h.hp > 0) || null; },
  cookLevel() { const c = this.cookOf(); return c ? Math.min(CM.COOK_MOST, c.cook.level || 0) : 0; },
  takeApron(heroIndex) {
    const h = this.party[heroIndex]; if (!h) return "Nobody by that name.";
    if (h.cook) return `${h.name} wears the apron already (a cook of level ${h.cook.level}, ${h.cook.made} dishes made).`;
    this.logAct("takeApron", heroIndex);
    for (const o of this.party) if (o !== h && o.cook) { o.cookWas = o.cook; delete o.cook; }   // (the apron passes; what the old cook learnt is kept on them)
    h.cook = h.cookWas || { level: 0, made: 0 }; delete h.cookWas;
    this.say(`${h.name} takes the apron.`); this.saveRun(); this.emit("change"); return "";
  },
  whereCook() { if (this.inTown() && this.homeLevel() >= 3) return "home"; if (this.mode === "camp") return "camp"; if (this.cookLevel() >= CM.COOK_FIELD) return "field"; return null; },
  cookDish(id) {
    const D = CM.DISHES[id]; if (!D) return "No such dish.";
    const where = this.whereCook(); if (!where) return this.inTown() ? "The house has no kitchen yet (its third level)." : "A dish is made at the home's kitchen, at a camp's fire, or on the floor by a cook of the third level, for a torch.";
    const rows = CM.canCook(this.bag, id); if (!rows) return `${D.name} wants ${D.needs.map(CM.needName).join(", ")}.`;
    let torch = -1; if (where === "field") { torch = this.bag.findIndex((i) => i.kind === "torch"); if (torch < 0) return "A fire wants a torch from the pack, down here."; }
    this.logAct("cookDish", id);
    for (const r of rows.concat(torch >= 0 ? [torch] : []).sort((a, b) => b - a)) this.bag.splice(r, 1);
    const cook = this.cookOf(); if (cook) { cook.cook.made += 1; if (cook.cook.made % CM.COOK_PER_LEVEL === 0 && cook.cook.level < CM.COOK_MOST) { cook.cook.level += 1; this.say(`${cook.name} is a cook of level ${cook.cook.level}: the dishes last a floor longer.`); if (cook.cook.level >= CM.COOK_MOST) this.achieve("cook"); } }
    const it = CM.dish(id); it.staleDay = CM.dayOf(this) + CM.DISH_KEEPS; if (cook) it.by = cook.name;
    this.gain([it], "cooked"); this.tally.cooked = (this.tally.cooked || 0) + 1; this.countUse("cook");
    this.sound("heal"); this.say(`${D.name}, ${where === "home" ? "from the party's own kitchen" : where === "camp" ? "from the camp's fire" : "over a torch on the floor"}: ${D.what}. It keeps two days.`);
    this.saveRun(); this.emit("change"); return "";
  },
  eatDish(row, hero) {
    const it = this.bag[row]; if (!it || it.kind !== "dish") return "Nothing to eat."; const D = CM.DISHES[it.dish]; if (!D) return "Nobody would eat that.";
    this.bag.splice(row, 1); this.countUse("dish");
    const was = this.meal; this.fed = 0; this.cheer(4 + (D.effect.morale || 0));
    const floors = D.floors + (it.by ? (this.party.find((h) => h.name === it.by && h.cook) || { cook: { level: 0 } }).cook.level : this.cookLevel());
    this.meal = { kind: it.dish, dish: true, floor: (this.floor ? this.floor.number : 0) + floors - 1 + (this.inTown() ? 1 : 0) };
    for (const h of this.party) { h.mealLuck = D.effect.luck || 0; h.mealStat = D.effect.stat || null; CM.recompute(h); }
    const fans = this.party.filter((h) => h.hp > 0 && CM.favouriteOf(h) === it.dish);
    if (fans.length) { this.cheer(2); this.say(`${fans[0].name}: "${CM.FAVOURITES.lines[fans[0].origin && CM.FAVOURITES.origin[fans[0].origin] === it.dish ? fans[0].origin : fans[0].cls] || "that is the one"}." A favourite: the heart lifts.`); this.tally.favourites = (this.tally.favourites || 0) + 1; }
    this.sound("heal"); this.say(`The party eats ${D.name.toLowerCase()}${hero ? `, ${hero.name} serving` : ""}: ${D.what}, for ${CM.plural(floors, "floor")}${was ? " (the last meal is forgotten)" : ""}.`);
    this.saveRun(); this.emit("change"); return "";
  },
  staleDishes() {                                                        // at a floor's start: what has gone stale is thrown out
    const day = CM.dayOf(this); for (let i = this.bag.length - 1; i >= 0; i--) if (this.bag[i].kind === "dish" && this.bag[i].staleDay !== undefined && this.bag[i].staleDay < day) { this.say(`The ${this.bag[i].name.toLowerCase()} has gone stale.`); this.bag.splice(i, 1); }
  },
  secondWind() {                                                         // honey cakes and the like: at a quarter health a hero mends a quarter, once a fight
    if (!CM.mealOf(this).wind) return;
    for (const h of this.alive()) if (h.hp > 0 && h.hp <= h.max / 4 && !h.winded2) { h.winded2 = true; const n = Math.ceil(h.max / 4); h.hp = Math.min(h.max, h.hp + n); this.say(`${h.name} finds a second wind (+${n}).`); }
  },
});
