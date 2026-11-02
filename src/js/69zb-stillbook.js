"use strict";
// Brewing at the still (v32.2, UPGRADE_PLAN_27.md): recipe pages lie in the dungeon - one chest in eight from the
// second floor down, and a fallen party's remains one time in three - each a still recipe of a crop of the South Fields
// and a band's ingredient, copied into the village's book the moment it is found. At the still in the fields' shed a
// known recipe makes its potion, oil, flask or elixir from the two, and asks no gold. The pages run deeper with the
// bands (a page is of a band the party has reached).
//   CM.STILLBOOK[id] -> {name, crop, ing, makes, what};  game.stillKnown(); game.stillBrewWhy(id); game.stillBrew(id)
{ const SB = CM.STILLBOOK = {
    tomatotonic: { name: "Tomato Tonic", crop: "tomato", ing: "gravemoss", makes: "heal2", what: "two healing potions" },
    garlicdraught: { name: "Garlic Draught", crop: "garlic", ing: "drownedweed", makes: "antidote2", what: "two antidotes" },
    pumpkinspirit: { name: "Pumpkin Spirit", crop: "pumpkin", ing: "forgesoot", makes: "oil:fire", what: "an oil of fire" },
    roseholy: { name: "Rosewater, blessed", crop: "rose", ing: "bonedust", makes: "flask:holy", what: "a flask of holy water" },
    melonquick: { name: "Melon Quickwine", crop: "melon", ing: "saltweed", makes: "elixir:haste", what: "an elixir of haste" },
    blueberryeyes: { name: "Blueberry Clear-eye", crop: "blueberry", ing: "sporecap", makes: "elixir:owleyes", what: "an elixir of owl's eyes" },
    potatostone: { name: "Potato Stone-wine", crop: "potato", ing: "crystaldust", makes: "elixir:stoneskin", what: "an elixir of stoneskin" },
    chilifire: { name: "Chili Fire-pot", crop: "chili", ing: "slag", makes: "bomb", what: "a firepot" },
    lettucesleep: { name: "Lettuce Night-milk", crop: "lettuce", ing: "gravesalt", makes: "elixir:night", what: "the night's draught" },
    cauligreater: { name: "Cauliflower Cordial", crop: "cauliflower", ing: "rootsap", makes: "greaterheal", what: "a greater healing potion" },
    grapemana: { name: "Grape Spirit", crop: "grapes", ing: "crystaldust", makes: "mana2", what: "two mana potions" },
    cucumberrime: { name: "Cucumber Rime", crop: "cucumber", ing: "drownedweed", makes: "oil:frost", what: "an oil of rime" },
  };
  CM.STILL_PAGE = { chest: 8, remains: 3, from: 2 };
  const bandOf = (id) => (CM.INGREDIENTS[SB[id].ing] || { band: 0 }).band;
  const make = (makes, fl) => { if (makes === "heal2") return [{ name: "Healing Potion", kind: "heal", power: 45, value: 35 }, { name: "Healing Potion", kind: "heal", power: 45, value: 35 }];
    if (makes === "mana2") return [{ name: "Mana Potion", kind: "mana", power: 30, value: 40 }, { name: "Mana Potion", kind: "mana", power: 30, value: 40 }];
    if (makes === "antidote2") return [CM.antidote(), CM.antidote()]; if (makes === "bomb") return [CM.bomb()];
    if (makes === "greaterheal") return [{ name: "Greater Healing Potion", kind: "greaterheal", power: 2 * (20 + Math.max(1, fl) * 3), value: 60 }];
    if (makes.startsWith("oil:")) return [CM.oil(makes.slice(4))]; if (makes.startsWith("flask:")) return [CM.flask(makes.slice(6))]; if (makes.startsWith("elixir:")) return [CM.elixir(makes.slice(7))]; return []; };
  const G = CM.Game.prototype;
  Object.assign(G, {
    stillKnown() { return this.vext("stillbook"); },
    stillPageFor(salt) { const fl = this.floor; if (!fl || fl.number < CM.STILL_PAGE.from || fl.number >= 1000) return null; const band = CM.themeIndex ? CM.themeIndex(fl.number) : 0, K = this.stillKnown();
      const open = Object.keys(SB).filter((id) => !K[id] && bandOf(id) <= Math.max(band, 1)); if (!open.length) return null; return open[CM.hashSeed(`${this.seed}:page:${salt}`) % open.length]; },
    learnStill(id, how) { const K = this.stillKnown(); if (K[id]) return; K[id] = true; this.saveVillage && this.saveVillage(); this.tally.pages = (this.tally.pages || 0) + 1;
      this.say(`${how || "Among it all"}, a stained page in a careful hand: a still recipe - ${SB[id].name}: a ${CM.CROPS[SB[id].crop].name.toLowerCase()} and ${CM.INGREDIENTS[SB[id].ing].name.toLowerCase()} make ${SB[id].what}. Copied into the book.`);
      if (Object.keys(SB).every((k) => K[k]) && this.achieve) this.achieve("stillbook"); },
    stillBrewWhy(id) { const R = SB[id]; if (!R) return "No such recipe."; if (!this.stillKnown()[id]) return "That page hasn't been found."; if (!this.atFields || !this.atFields()) return "The still is in the fields' shed.";
      const has = (k) => this.bag.some((it) => it.kind === "ingredient" && it.ingredient === k); if (!has(R.crop)) return `It wants a ${CM.CROPS[R.crop].name.toLowerCase()}.`; if (!has(R.ing)) return `It wants ${CM.INGREDIENTS[R.ing].name.toLowerCase()}.`;
      if (R.makes === "greaterheal" && this.asc && this.asc("nogreater")) return "No greater potions, this high on the ladder."; return ""; },
    stillBrew(id) { const why = this.stillBrewWhy(id); if (why) return why; this.logAct && this.logAct("stillBrew", id); const R = SB[id];
      for (const k of [R.crop, R.ing]) this.bag.splice(this.bag.findIndex((it) => it.kind === "ingredient" && it.ingredient === k), 1);
      const made = make(R.makes, this.deepestReached ? this.deepestReached() : 1); this.gain(made, "fields"); this.countUse && this.countUse("brew"); this.tally.stilled = (this.tally.stilled || 0) + 1;
      this.sound && this.sound("spell"); this.say(`The still ticks and runs: ${R.name} - ${R.what}.`); if (R.makes.startsWith("elixir:") && this.achieve) this.achieve("distilled");
      this.saveRun && this.saveRun(); this.emit && this.emit("change"); return ""; },
  });
  CM.ACHIEVEMENTS.stillbook = { name: "The Whole Book", what: "Find every page of the still's recipe book", title: "the Distiller" };
  // pages in chests and among the fallen's remains
  const gain0 = G.gain; G.gain = function (items, how) {
    if ((how === "chest" || how === "remains") && this.floor && Array.isArray(items)) { const fl = this.floor, salt = `${how}:${fl.number}:${fl.pos.join(",")}:${(this.tally && this.tally.chests) || 0}`;
      if (CM.hashSeed(`${this.seed}:pagechance:${salt}`) % CM.STILL_PAGE[how] === 0) { const id = this.stillPageFor(salt); if (id) this.learnStill(id, how === "chest" ? "Under the lid" : "In a dead alchemist's satchel"); } }
    return gain0.call(this, items, how); };
}
