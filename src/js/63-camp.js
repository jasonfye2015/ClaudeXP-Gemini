"use strict";
// The bag and the camp: what the party carries, wears, drinks and reads; the merchant, the temple, the scribe, the
// tavern, the smith and the vault.
{
const keyOf = CM.keyOf;
Object.assign(CM.Game.prototype, {
  // ---- the bag, the merchant, the camp ----
  openBag(shop = false) {
    if (!this.peddling) this.logAct("openBag", shop ? 1 : 0);
    this.shopping = shop;
    if (shop && !this.stock) {
      const rnd = this.rnd, depth = this.floor.number === 0 ? Math.max(3, this.partyLevel() + 1) : this.floor.number + 3;
      this.stock = ["weapon", "weapon", "weapon", "armor", "armor", "armor", "shield", "helm"].map((k) => { const it = CM.makeItem(depth, rnd, k); it.unknown = false; return it; });
      const heal = CM.healPotion(depth); if (heal.kind === "greaterheal" && this.asc("nogreater")) { heal.kind = "heal"; heal.name = "Healing Potion"; heal.power = 20 + depth * 3; heal.value = 20; }
      this.stock.push(heal, CM.manaPotion(depth), CM.lesserFeather(),
        { name: "Phoenix Feather", kind: "revive", power: 0, value: 120 }, CM.antidote(), CM.torch(), CM.lantern(), CM.lampOil(), CM.scroll("identify"), CM.scroll("mapping"), CM.scroll("recall"), CM.rope(), CM.ration(), CM.flask("oil"));
      this.stock.push(CM.lockpick(), CM.lockpick(), CM.bar(), CM.bait());
      if (depth >= 6 && !this.bag.some((i) => i.kind === "grapnel")) this.stock.push(CM.grapnel());
      if (depth >= 7 && !this.bag.some((i) => i.kind === "trapkit")) this.stock.push(CM.trapKit());
      if (depth >= 10) this.stock.push(CM.flask("smoke"), CM.elixir("stoneskin"));
      if (depth >= 14) this.stock.push(CM.lockpick(true));
      const staples = ["weapon", "armor", "shield", "helm", "heal", "greaterheal", "torch", "ration", "antidote"];   // the rest rotates: a third of it is not on the table at this camp
      if (this.floor.number > 0) this.stock = this.stock.filter((it, i) => staples.includes(it.kind) || CM.hashSeed(`${this.seed}:stock:${this.floor.number}:${i}:${it.kind}`) % 3 !== 0);   // (the Merchant's House in town carries it all)
      for (const it of this.stock) it.value = CM.priceAt(it.value, this.floor.number);
      this.deliverOrders();
      if (depth >= 13 && !this.bag.some((i) => i.kind === "kit")) this.stock.push(CM.fieldKit());
      const house = this.villageLevel("merchant");                       // (the village's merchant's house: what the camps' merchant has learned to carry)
      if (house >= 1 && !this.asc("nogreater")) this.stock.push({ name: "Greater Healing Potion", kind: "greaterheal", power: 2 * (20 + depth * 3), value: 70 });
      if (house >= 2) for (const el of ["fire", "frost", "holy"]) this.stock.push(CM.oil(el));
      if (house >= 3) { const r2 = new CM.Random(CM.hashSeed(`${this.seed}:house:${this.floor.number}`)), rare = CM.affix(CM.makeItem(depth + 2, r2, r2.pick(["weapon", "armor", "helm", "shield"])), 99, r2); rare.unknown = false; rare.value = Math.floor(rare.value * 1.4); this.stock.push(rare); }
      if (house >= 4 || this.village.cheaper) for (const it of this.stock) it.value = Math.max(1, Math.floor(it.value * 0.8));   // (or the Root was left dreaming, and the village prospered)
    }
    this.emit("bag", true);
  },

  closeBag() {
    this.logAct("closeBag");
    if (this.peddling) { this.stock = null; this.peddling = null; this.say("The peddler folds the cloth over what's left, and waits for whoever comes next."); }
    this.emit("bag", false);
    this.saveRun();
    this.emit("change");
  },

  describe(item) {
    const plain = { heal: "heals", mana: "restores magic", revive: "raises the fallen", torch: "light, for a while", lantern: "light that lasts",
      key: "opens a locked door", antidote: "cures poison, sleep, paralysis and blindness", rope: "down a pit without the fall, and back up again",
      bones: "someone's, gathered up for a ghost who asked", greaterheal: "heals, twice over", bomb: "thrown in a fight: fire on every foe", revive0: "raises the fallen to half, once a floor", lampoil: "oil for the lantern", glowstone: "a light that never goes out" }[item.kind];
    return plain || CM.itemLabel(item);
  },

  // what the hero wears in that slot goes back to the pack - unless a curse holds it
  takeOff(n, slot) {
    this.logAct("takeOff", n, slot);
    const hero = this.party[n], item = hero && hero[slot];
    if (!item) return "Nothing there.";
    if (slot === "weapon" || slot === "armor") return "Swap it for another instead: no one goes bare-handed down here.";
    if (item.props && item.props.cursed) return `${item.name} is cursed: it won't come off. The camp's temple can lift it.`;
    hero[slot] = null;
    this.bag.push(item);
    CM.recompute(hero);
    this.sound("chest");
    this.emit("change");
    return "";
  },

  // an unknown thing is known: its name, its bonus, its properties
  reveal(item) {
    if (!item.unknown) return false;
    item.unknown = false;
    this.noteKnown(item);
    return true;
  },

  identify(row) {
    this.logAct("identify", row);
    const item = this.bag[row];
    if (!this.identifying || !item) return "Pick a thing from the pack.";
    if (!item.unknown) return "That one is known already. Pick an unknown thing.";
    const scroll = this.bag.findIndex((i) => i.kind === "scroll" && i.spell === "identify");
    if (scroll < 0) { this.identifying = false; return "The scroll is gone."; }
    this.reveal(item);
    this.bag.splice(scroll, 1);
    this.identifying = false;
    this.sound("spell");
    this.say(`The scroll crumbles: it's ${item.name} (${CM.itemLabel(item)}).`);
    this.emit("change");
    return "";
  },

  // a scroll read or a wand waved, between fights; "" when it worked, else why not
  useMagicOutside(row, n) {
    const item = this.bag[row], hero = this.party[n], fl = this.floor;
    const spec = item.kind === "scroll" ? CM.SCROLLS[item.spell] : CM.WANDS[item.spell];
    if (!spec.outside) return `${item.name} is for a fight.`;
    if (item.spell === "identify") {
      if (!this.bag.some((i) => i.unknown)) return "Nothing in the pack is unknown.";
      this.identifying = true;
      return "Now pick the unknown thing in the pack to identify.";
    }
    if (item.spell === "recall") {                                      // to the last camp reached, and back by the same scroll
      if (item.back) {
        if (this.mode !== "camp") return "The scroll remembers a square on floor " + item.back.floor + ": read it at the camp to go back.";
        const back = item.back; this.bag.splice(row, 1);
        this.stock = null; this.recruits = null; this.leaveFloor(); this.floor = this.floorAt(back.floor);
        if (CM.passable(this.floor, back.pos[0], back.pos[1])) this.floor.pos = back.pos.slice();
        this.setMode("explore"); this.look(); this.emit("floor", this.floor); this.saveRun();
        this.say("The scroll crumbles, and the party stands where it stood.");
        return "";
      }
      if (this.mode !== "explore") return "Read it on a floor, to be recalled from it.";
      const camps = this.camps || [];
      if (!camps.length) return "No camp has been reached to be recalled to.";
      const camp = camps.filter((n) => n < fl.number).pop() || camps[0];
      item.back = { floor: fl.number, pos: fl.pos.slice() };
      this.stock = null; this.recruits = null; this.leaveFloor(); this.floor = this.floorAt(camp);
      const ladder = this.cellOf(this.floor, "ladder"); if (ladder) this.floor.pos = ladder.slice();
      this.setMode("camp"); this.emit("floor", this.floor); this.sound("stairs"); this.saveRun();
      this.say(`The scroll takes the party up to the camp below floor ${camp}. Read it again there, and it takes them back.`);
      return "";
    }
    if (item.spell === "knowledge") {
      const wall = Object.values(fl.features).find((f) => f.type === "carving" && !f.read && typeof f.text === "number" && f.text >= 0);
      if (!wall) return "This floor's wall is read already, or there is none.";
      wall.read = true;
      const text = CM.loreText(wall.text, this.seed, wall.telling), lkey = CM.loreKey(wall.text);
      this.markRead(lkey); this.remember("carving", text, { key: lkey }); this.originLines(lkey);
      this.emit("lore", text);
      this.say("The scroll shows the floor's carving, letter by letter, as if the wall stood before you.");
    } else if (item.spell === "sharpen") {
      if (!hero || !hero.weapon || (hero.weapon.props || {}).fists) return "Pick a hero with a weapon to sharpen.";
      hero.weapon.sharpUntil = fl.number; this.buffs = this.buffs || {}; this.buffs.sharpen = fl.number;
      this.say(`${hero.name}'s ${CM.baseName(hero.weapon)} takes an edge that will last the floor (+2).`);
    } else if (item.spell === "lostpage") return "The page is blank until there is something to read it at.";
    if (item.spell === "mapping") {
      fl.seen = [];
      for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) fl.seen.push([x, y]);
      for (const f of Object.values(fl.features)) if ("known" in f) f.known = true;
      this.say("The scroll crumbles, and the whole floor is drawn on the automap.");
    } else if (item.spell === "teleport") {
      const open = [];
      for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) {
        const k = keyOf(x, y), f = fl.features[k];
        if (CM.passable(fl, x, y) && !fl.things[k] && !(f && ["pit", "trapdoor", "teleporter", "spinner"].includes(f.type))) open.push([x, y]);
      }
      if (!open.length) return "The scroll fizzles.";
      fl.pos = this.rnd.pick(open);
      this.look();
      this.emit("teleported", fl.pos[0], fl.pos[1]);
      this.say("The scroll crumbles - and the party is somewhere else on this floor.");
    } else if (item.spell === "healing") {
      if (!hero || hero.hp <= 0) return "Not on the fallen.";
      const n2 = 15 + 3 * (this.floor ? Math.floor(this.floor.number / 2) : 1);
      hero.hp = Math.min(hero.max, hero.hp + n2);
      this.say(`${hero.name} is mended by the wand (+${n2}).`);
    }
    this.sound("spell");
    this.countUse(item.kind);
    if (item.kind === "scroll") this.bag.splice(row, 1);
    else this.spendWand(item, row);
    this.saveRun();
    this.emit("change");
    return "";
  },

  // a scroll or wand in the thick of it
  useMagicInBattle(h, row, who) {
    const item = this.bag[row], foes = this.living(), L = this.floor ? this.floor.number : 1;
    const spec = item.kind === "scroll" ? CM.SCROLLS[item.spell] : CM.WANDS[item.spell];
    if (spec.outside && item.spell !== "healing") { this.say(`${item.name} is for between fights.`); return false; }
    if (item.kind === "wand" && item.spell === "fire" && !this.foeAt(who)) { this.say("Nothing left to aim at."); return false; }
    this.sound("spell");
    this.emit("fx", { kind: "cast", id: item.spell, hero: h, item: item.kind, foes, foe: item.kind === "wand" && item.spell === "fire" ? this.foeAt(who) : null,
      ally: item.spell === "healing" ? this.allyAt(who, false) : null });
    if (item.spell === "banish") {
      const called = foes.filter((m) => m.summoned && m.hp > 0);
      if (!called.length) { this.say("Nothing here was called: the scroll has nothing to send back."); return false; }
      const m = called[called.length - 1]; m.hp = 0; m.fled = true; m.dead = true;
      this.say(`${h.name} reads the scroll, and ${CM.the(m)} is gone as if it had never come.`);
    } else if (item.spell === "silence") {
      if (this.combat) this.combat.silence = true;
      this.say(`${h.name} reads the scroll, and the words die in every mouth: no spell, no breath, this fight.`);
    } else if (item.spell === "lostpage") {
      const el = ["fire", "frost", "storm"][L % 3], dmg = 12 + 2 * L;
      for (const m of foes) this.spellHit(m, dmg, "", el);
      this.say(`${h.name} reads the lost page aloud: ${CM.ELEMENT_NAMES[el] || el} on every foe, ${dmg} each. The page is blank after.`);
    } else if (item.spell === "fire") {
      if (item.kind === "wand") { const t = this.foeAt(who); if (!t) { this.say("Nothing left to aim at."); return false; } this.spellHit(t, 10 + 2 * L, `${h.name}'s wand spits fire:`, "fire"); }
      else { const dmg = 10 + 2 * L; for (const m of foes) this.spellHit(m, dmg, "", "fire"); this.say(`${h.name} reads the scroll: fire on every foe, ${dmg} each.`); }
    } else if (item.spell === "frost") {
      const dmg = 6 + 2 * L;
      let held = 0;
      for (const m of foes) { this.spellHit(m, dmg, "", "frost"); if (m.hp > 0) m.chilled = 2; if (m.hp > 0 && !CM.unmoved(m) && this.rnd.chance(0.3)) { m.held = Math.max(m.held || 0, 1); held++; } }
      this.say(`${h.name} ${item.kind === "wand" ? "waves the wand" : "reads the scroll"}: cold on every foe, ${dmg} each${held ? `, ${CM.plural(held, "foe")} frozen fast` : ""}.`);
    } else if (item.spell === "sleep") {
      let asleep = 0;
      for (const m of foes) if (!CM.unmoved(m) && this.rnd.chance(0.5)) { m.asleep = 3; asleep++; }
      this.say(`${h.name} waves the wand: ${asleep ? CM.plural(asleep, "foe") + " slump where they stand" : "none of them so much as yawns"}.`);
    } else if (item.spell === "protection") {
      if (this.combat) this.combat.protect = true;
      this.say(`${h.name} reads the scroll: every blow on the party does less, this fight.`);
    } else if (item.spell === "healing") {
      const ally = this.allyAt(who, false);
      if (!ally) return false;
      const n2 = 15 + 3 * Math.floor(L / 2);
      ally.hp = Math.min(ally.max, ally.hp + n2);
      this.say(`${h.name} touches ${ally.name} with the wand: +${n2}.`);
    } else return false;
    this.countUse(item.kind);
    if (item.kind === "scroll") this.bag.splice(row, 1);
    else this.spendWand(item, row);
    this.emit("change");
    return true;
  },

  // what the party wears: the thing in the slot goes back to the pack; wearing an unknown thing is how you learn it
  equip(hero, row) {
    const item = this.bag[row];
    if (!this.inGive) this.logAct("equip", this.party.indexOf(hero), row);
    const why = CM.cantWear(hero, item);
    if (why) return why;
    const slot = this.offhandWanted && CM.canDualWield(hero, item) ? "offhand" : item.slot || (item.kind === "shield" ? "offhand" : item.kind);
    const old = hero[slot];
    if (old && old.props && old.props.cursed) return `${hero.name}'s ${old.name} is cursed and won't come off. The camp's temple can lift it.`;
    if (!old || (item.power || 0) > (old.power || 0)) { this.tally.firstUpgrade = this.tally.firstUpgrade || {}; if (this.tally.firstUpgrade[slot] === undefined && old) this.tally.firstUpgrade[slot] = this.floor ? this.floor.number : 0; }   // (for the simulator: floors to the first better thing in each slot)
    if (slot === "weapon" && hero.offhand && hero.offhand.kind === "weapon" && CM.weaponClass(item) !== "dagger") { this.bag.push(hero.offhand); this.say(`${hero.name} sheathes the second knife.`); hero.offhand = null; }
    hero[slot] = item;
    this.bag.splice(row, 1);
    if (old) this.bag.push(old);
    if (slot === "weapon" && item.props && item.props.twohanded && hero.offhand) {
      if (hero.offhand.props && hero.offhand.props.cursed) { hero[slot] = old; this.bag.splice(row, 0, item); if (old) this.bag.pop(); return `${hero.name}'s shield is cursed to the arm: no room for a two-handed weapon.`; }
      this.bag.push(hero.offhand);
      this.say(`${hero.name} slings the shield: the ${CM.baseName(item)} takes both hands.`);
      hero.offhand = null;
    }
    if (item.bearers && !item.bearers.includes(hero.name)) { item.bearers.push(hero.name); if (item.bearers.length >= 3 && !(item.props || {}).relic && !(item.props || {}).unique) { item.props = item.props || {}; item.props.heirloom = true; this.say(`${item.name} has been borne by three now: it is an heirloom, and counts among the relics.`); } }
    const learned = this.reveal(item);
    const ratio = hero.hp / hero.max;
    CM.recompute(hero);
    hero.hp = Math.max(1, Math.round(hero.max * ratio));
    this.sound("chest");
    if (item.props && item.props.cursed) this.say(`${hero.name} takes up the ${CM.baseName(item)} - and it clings! It's cursed.`);
    else if (learned) this.say(`${hero.name} tries the ${CM.baseName(item)}: it's ${item.name} (${CM.itemLabel(item)}).`);
    if (item.kind === "weapon" && !(item.props || {}).fists && !CM.atHome(hero, item)) this.say(`${hero.name} is not at home with a ${CM.WEAPON_CLASSES[CM.weaponClass(item)].name}: blows land less often, and the ${CM.WEAPON_CLASSES[CM.weaponClass(item)].name}'s own trick is lost.`);
    this.emit("change");
    return "";
  },
  // a second knife to the off hand (the bag's second button for a Rogue or a Ranger)
  equipOffhand(hero, row) { this.offhandWanted = true; try { return this.equip(hero, row); } finally { this.offhandWanted = false; } },

  give(row, n) {                                                        // returns a note for the bag screen, "" when it worked
    if (row < 0 || row >= this.bag.length) return "Pick something from your pack first.";
    this.logAct("give", row, n);
    const item = this.bag[row], hero = this.party[n];
    if (item.kind === "key") return "Keys turn in locks, not in hands. Walk into the locked door.";
    if (item.kind === "rope") return "The rope is for a pit: walk into one with it in the pack.";
    if (item.kind === "tome") return this.readTome(row, hero);
    if (["heal", "greaterheal", "mana", "revive", "antidote", "oil"].includes(item.kind)) this.countUse(item.kind);
    if (item.kind === "gem") return "A gem is for the camp's smith: he sets it into gear, for gold.";
    if (item.kind === "boxkey") return `That key is for the strongbox on floor ${item.box}. Walk up to the box and use it.`;
    if (item.kind === "lockpick") return "A pick is tried on a lock: walk into the locked door, or up to the strongbox, with it in the pack.";
    if (this.mode !== "explore" && ["trapkit", "trapparts", "bar", "bait", "grapnel", "pick"].includes(item.kind)) return "That is a thing for the dungeon's floors.";
    if (item.kind === "trapkit") return this.disarmPlate(hero);
    if (item.kind === "trapparts") return this.setTrap(row, hero);
    if (item.kind === "bar") return this.barDoor(row, hero);
    if (item.kind === "bait") return this.dropBait(row, hero);
    if (item.kind === "grapnel") return this.useGrapnel();
    if (item.kind === "pick") return this.usePick(row);
    if (item.kind === "ration") {
      this.bag.splice(row, 1); this.countUse("ration");
      this.fed = CM.partyProp(this.party, "spoon") ? -100 : 0;
      this.cheer(2);
      this.sound("heal");
      this.say(`The party eats. ${hero.name} hands the last of it round.`);
      this.emit("change");
      return "";
    }
    if (item.kind === "ingredient") return "The camp's alchemist wants that. Keep it for her.";
    if (item.kind === "scrap") return "Scrap is for the camp's smith: five stand in for a diamond.";
    if (item.kind === "bomb") return "A firepot is for a fight: Item, then throw it.";
    if (item.kind === "oil") {
      if (hero.hp <= 0) return `${hero.name} has fallen.`;
      if (!hero.weapon) return `${hero.name} has nothing to rub it on.`;
      this.bag.splice(row, 1);
      hero.oil = { element: item.element, fights: CM.OIL_FIGHTS };
      this.sound("spell");
      this.say(`${hero.name} rubs the ${item.name} into the ${CM.baseName(hero.weapon)}: it ${item.element === "fire" ? "smokes" : item.element === "frost" ? "frosts over" : "gleams"}. For the next ${CM.OIL_FIGHTS} fights, ${CM.ELEMENT_NAMES[item.element]}.`);
      this.emit("change");
      return "";
    }
    if (item.kind === "bones") return "They're not yours to use. Someone on this floor wants them back.";
    if (item.kind === "page") { this.markRead("thing.page"); this.remember("carving", CM.PAGE.text, { key: "thing.page" }); this.emit("talk", { title: CM.PAGE.name, text: CM.PAGE.text }); return ""; }
    if (item.kind === "scroll" || item.kind === "wand") return this.useMagicOutside(row, n);
    if (item.kind === "torch") {
      this.bag.splice(row, 1);
      this.light = { kind: "torch", left: CM.TORCH_STEPS };
      this.sound("spell");
      this.say(`${hero.name} lights a fresh torch.`);
      this.emit("change");
      return "";
    }
    if (item.kind === "lantern") {
      this.bag.splice(row, 1);
      this.light = { kind: "lantern", left: CM.LANTERN_OIL }; this.lanternHeld = true;
      this.sound("spell");
      this.say(`${hero.name} lights the lantern: a flask of oil in it, which burns slow and reaches far. Lamp oil keeps it lit.`);
      this.emit("change");
      return "";
    }
    if (item.kind === "meat") return this.cook(row);
    if (item.kind === "kit") return "The field kit works through the alchemist's list: C (cast or use) out of a fight, or the camp's door.";
    if (item.kind === "salve") { this.bag.splice(row, 1); this.countUse("salve"); this.buffs = this.buffs || {}; this.buffs.salve = this.floor ? this.floor.number : 0; this.sound("heal"); this.say(`${hero.name} rubs the salve into everyone's cuts: they will close as the party walks, this floor.`); this.emit("change"); return ""; }
    if (item.kind === "bread") { this.bag.splice(row, 1); this.countUse("bread"); this.fed = 0; this.cheer(3); for (const h of this.alive()) h.hp = Math.min(h.max, h.hp + 20); this.sound("heal"); this.say("The party eats the dwarven bread, which is hard going and does them good (+20 each)."); this.emit("change"); return ""; }
    if (item.kind === "liniment") { if (hero.hp <= 0) return `${hero.name} has fallen.`; this.bag.splice(row, 1); this.countUse("liniment"); this.cure(hero, CM.CURABLE); hero.hp = Math.min(hero.max, hero.hp + 10); if (hero.wound) this.healWound(hero); this.sound("heal"); this.say(`${hero.name}'s hurts close under the liniment (+10).`); this.emit("change"); return ""; }
    if (item.kind === "lampoil") {
      if (!this.lanternHeld && this.light.kind !== "lantern") return "No lantern to pour it into.";
      this.bag.splice(row, 1); this.countUse("lampoil");
      if (this.light.kind === "lantern") this.light.left += CM.LANTERN_OIL; else this.light = { kind: "lantern", left: CM.LANTERN_OIL };
      this.sound("spell"); this.say(`${hero.name} fills the lantern.`); this.emit("change");
      return "";
    }
    if (item.kind === "glowstone") {
      this.bag.splice(row, 1);
      if (this.light.kind === "torch") this.bag.push(Object.assign(CM.torch(), { power: this.light.left }));
      this.light = { kind: "glow", left: 0 };
      this.sound("spell"); this.say(`${hero.name} holds up the glow stone: a cold light that never goes out, and does not reach far.`); this.emit("change");
      return "";
    }
    if (item.kind === "elixir") {
      if (hero.hp <= 0) return `${hero.name} has fallen.`;
      this.bag.splice(row, 1); this.countUse("elixir"); this.buffs = this.buffs || {};
      const fl = this.floor ? this.floor.number : 0;
      if (item.elixir === "stoneskin") { this.buffs.stoneskin = fl; hero.stoneskin = true; this.say(`${hero.name}'s skin goes grey and hard: three off every blow, this floor.`); }
      else if (item.elixir === "haste") { this.buffs.haste = hero.name; this.say(`${hero.name} is quick as thought: first in every round of the next fight.`); }
      else if (item.elixir === "owleyes") { this.buffs.owleyes = 3; this.say("The party's eyes go wide and gold: no dark holds them, for three floors."); }
      else if (item.elixir === "night") { this.buffs.night = fl; this.say("The night's draught: no sleep, no surprise, this floor."); }
      this.sound("heal"); this.emit("change");
      return "";
    }
    if (item.kind === "revive0") {
      if (hero.hp > 0) return `${hero.name} is standing.`;
      if (this.featherFloor === (this.floor ? this.floor.number : 0)) return "A lesser feather works once a floor.";
      this.bag.splice(row, 1); this.countUse("revive0"); this.featherFloor = this.floor ? this.floor.number : 0;
      hero.hp = Math.max(1, Math.floor(hero.max / 2)); this.sound("heal"); this.say(`${hero.name} rises, half-mended, with the lesser feather's warmth in them.`); this.woundHero(hero); this.emit("change");
      return "";
    }
    if (item.kind === "antidote") {
      if (hero.hp <= 0) return `${hero.name} has fallen. Raise them first.`;
      const cured = this.cure(hero, CM.CURABLE);
      if (!cured.length) return `${hero.name} has nothing an antidote would cure.`;
      this.bag.splice(row, 1);
      this.sound("heal");
      this.say(`${hero.name} drinks the antidote, and is no longer ${cured.map((s) => CM.STATUSES[s].name.toLowerCase()).join(" or ")}.`);
      this.emit("change");
      return "";
    }
    if (item.kind === "revive") {
      if (hero.hp > 0) return "The Phoenix Feather is for the fallen.";
      if (this.asc("ironbound") && this.mode === "combat") return "Ironbound: the fallen rise only at the temple.";
      hero.hp = Math.floor(hero.max / 2);
      this.bag.splice(row, 1);
      this.sound("heal");
      this.woundHero(hero);
    } else if (hero.hp <= 0) {
      return `${hero.name} has fallen. Raise them first.`;
    } else if (item.kind === "heal" || item.kind === "greaterheal") {
      hero.hp = Math.min(hero.max, hero.hp + item.power);
      this.bag.splice(row, 1);
      this.sound("heal");
    } else if (item.kind === "mana") {
      if (!hero.maxmp) return `${hero.name} has no magic to restore.`;
      hero.mp = Math.min(hero.maxmp, hero.mp + item.power);
      this.bag.splice(row, 1);
      this.sound("heal");
    } else {
      this.inGive = true;
      try { return this.equip(hero, row); } finally { this.inGive = false; }
    }
    this.emit("change");
    return "";
  },

  buy(row) {
    if (!this.stock || row < 0 || row >= this.stock.length) return "Pick something from the merchant's wares first.";
    this.logAct("buy", row);
    const item = this.stock[row];
    if (this.gold < item.value) return "You can't afford that.";
    this.gold -= item.value;
    this.spend(this.peddling ? "peddler" : "merchant", item.value);
    this.gain([Object.assign({}, item, item.props ? { props: Object.assign({}, item.props) } : {})], this.peddling ? "peddler" : "merchant");
    if (this.peddling || ["weapon", "armor", "shield", "helm", "lantern"].includes(item.kind)) this.stock.splice(row, 1);   // (the merchant's potions never run out; a peddler's cloth does)
    this.sound("coin");
    this.emit("change");
    return "";
  },

  sell(row) {
    if (row < 0 || row >= this.bag.length) return "Pick something from your pack to sell.";
    this.logAct("sell", row);
    const item = this.bag.splice(row, 1)[0];
    this.gold += item.unknown ? 10 : Math.floor(item.value / 2);       // (the merchant pays a pittance for what no one can name)
    this.sound("coin");
    this.emit("change");
    return "";
  },

  rest() {
    const bed = this.asc("leancamps") ? 40 : 20;
    if (this.gold < bed) { this.say(`The merchant wants ${bed} gold for a bedroll by the fire.`); return; }
    this.logAct("rest");
    this.gold -= bed; this.spend("rest", bed);
    this.sleepTillDawn();
    for (const m of this.alive()) { m.hp = m.max; m.mp = m.maxmp; this.cure(m, CM.CURABLE); }
    this.fed = 0; if ((this.morale || 0) < 80) this.morale = 80;
    this.sound("heal");
    this.say("The party rests by the fire. Wounds close, magic returns, and the small ailments pass. Everyone eats.");
    const bond = (this.bonds || [])[Math.floor((this.tally.fights || 0) / 7) % Math.max(1, (this.bonds || []).length)];
    if (bond && (this.tally.fights || 0) % 3 === 0) this.say(CM.BANTER[(this.tally.fights || 0) % CM.BANTER.length].replace("{a}", bond[0]).replace("{b}", bond[1]));
    else this.banter("camp");
    this.campTale();
    this.saveRun();
  },

  // ---- the tools of the floor: a plate disarmed for its parts, a trap set behind the party, a door barred, bait dropped ----
  // the trap kit: the found plate the party stands on or faces is taken apart for its parts. The Artificer never fails; a
  // Rogue or a steady hand may (half, and Dexterity), and a failure springs it.
  disarmPlate(hero) {
    const fl = this.floor, [x, y] = fl.pos, [dx, dy] = CM.DIRS[fl.facing];
    const spots = [CM.keyOf(x, y), CM.keyOf(x + dx, y + dy)].filter((k) => { const f = fl.features[k]; return f && f.type === "plate" && f.trap && !f.spent && !f.gate && f.known; });
    if (!spots.length) return "The kit wants a trap plate you have found: stand on it, or face it.";
    const k = spots[0], f = fl.features[k], who = this.alive().find((h) => h.cls === "Artificer" || h.second === "Artificer") || this.alive().find((h) => h.cls === "Rogue") || hero;
    const sure = who.cls === "Artificer" || who.second === "Artificer";
    this.countUse("trapkit");
    if (!sure && !this.rnd.chance(CM.clamp(0.5 + CM.mod(this.stat(who, "dex")) * 0.1 + (who.cls === "Rogue" ? 0.2 : 0), 0.1, 0.95))) {
      f.spent = true; this.sound("trap"); this.say(`${who.name} has the plate half up when it goes: ${CM.TRAPS[f.trap]}!`); this.springTrap(f.trap, k); this.emit("change"); return "";
    }
    const parts = CM.trapParts(f.trap); f.spent = true; f.disarmed = true; this.bag.push(parts);
    this.sound("lever"); this.say(`${who.name} lifts the plate and takes the works out of it: ${parts.name} (${CM.TRAPS[f.trap]}).`); this.saveRun(); this.emit("change");
    return "";
  },
  // the parts, set: on the open square behind the party, with a kit in the pack; a band that walks onto it takes it
  setTrap(row, hero) {
    if (!this.bag.some((i) => i.kind === "trapkit")) return "Setting a trap takes a trap kit, and there is none in the pack.";
    const fl = this.floor, [x, y] = fl.pos, [dx, dy] = CM.DIRS[fl.facing], bx = x - dx, by = y - dy, k = CM.keyOf(bx, by);
    if (!CM.passable(fl, bx, by) || fl.features[k] || fl.things[k]) return "The square behind the party must be open floor, with nothing on it.";
    const parts = this.bag[row]; this.bag.splice(row, 1);
    fl.features[k] = { type: "plate", trap: parts.trap, set: true, known: true, spent: false, byParty: true };
    this.countUse("settrap"); this.sound("lever"); this.say(`${hero.name} sets ${CM.TRAPS[parts.trap]} under a loose flag behind the party. Mind the step.`); this.dirty = true; this.saveRun(); this.emit("change");
    return "";
  },
  // a bar: the open door beside the party is shut and held for the floor (wanderers don't pass; hungry hordes break it in
  // three turns); at a door already barred, the bar is kept and the party rests there instead
  barDoor(row, hero) {
    const fl = this.floor, [x, y] = fl.pos;
    const here = fl.features[CM.keyOf(x, y)]; if (here && here.type === "door") return "Step out of the doorway first: a bar goes across a door, not a party.";
    const doors = CM.DIRS.map(([dx, dy]) => CM.keyOf(x + dx, y + dy)).filter((k) => fl.features[k] && fl.features[k].type === "door" && fl.features[k].riddle === undefined);
    if (!doors.length) return "A bar wants a door beside the party.";
    const barredHere = doors.find((k) => fl.features[k].barred);
    if (barredHere) return this.restAtDoor(fl.features[barredHere]);
    const k = doors.find((d) => fl.features[d].open) || doors[0], f = fl.features[k];
    if (fl.things[k]) return "Something stands in the doorway.";
    this.bag.splice(row, 1); f.open = false; f.locked = false; f.barred = fl.number; f.hits = 0;
    this.countUse("bar"); this.sound("door"); this.say(`${hero.name} swings the door to and drops the bar across it. Nothing comes through that way tonight${this.has("hordes") ? " - unless it is hungry enough" : ""}. (Use another bar here to rest against it.)`);
    this.dirty = true; this.saveRun(); this.emit("change");
    return "";
  },
  // bait: dropped where the party stands; the nearest wanderers come to it for ten steps and stop to eat
  dropBait(row, hero) {
    const fl = this.floor, k = CM.keyOf(...fl.pos);
    if (fl.bait) return "There is bait down already. Walk away from it.";
    const it = this.bag[row]; this.bag.splice(row, 1);
    fl.bait = { at: k, until: (this.steps || 0) + CM.BAIT_STEPS, poisoned: Boolean(it.poisoned) };
    this.countUse("bait"); this.say(`${hero.name} drops the ${it.poisoned ? "poisoned ration" : "ration"} on the flags and the party moves off. Something has smelt it already.`); this.saveRun(); this.emit("change");
    return "";
  },

  // ---- wounds and scars ----
  // a hero who fell and rises carries a wound: a stat down by one; a second before the first heals is a grave wound (two)
  woundHero(h) {
    if (!h || h.hp <= 0) return;
    const open = CM.STATS.filter((s) => !(h.wound && h.wound.stats.includes(s)));
    const stat = this.rnd.pick(open);
    if (h.wound) { if (h.wound.stats.length < 2) { h.wound.stats.push(stat); h.wound.grave = true; this.say(`${h.name} rises with a grave wound: ${CM.STAT_NAMES[stat]} too, until it is seen to.`); } }
    else { h.wound = { stats: [stat], grave: false }; this.say(`${h.name} rises wounded: ${CM.STAT_NAMES[stat]} down by one until the temple or a liniment.`); }
    this.tally.wounds = (this.tally.wounds || 0) + 1;
    CM.recompute(h);
  },
  // a wound healed; the third leaves a scar, which is a trait with a touch of good in it
  healWound(h) {
    if (!h.wound) return false;
    delete h.wound; h.woundsHealed = (h.woundsHealed || 0) + 1; CM.recompute(h);
    if (h.woundsHealed % 3 === 0) {
      const ids = Object.keys(CM.SCARS).filter((id) => !(h.scars || []).includes(id));
      if (ids.length) { const id = ids[CM.hashSeed(`${this.seed}:scar:${h.name}:${h.woundsHealed}`) % ids.length]; h.scars = (h.scars || []).concat(id); this.tally.scars = (this.tally.scars || 0) + 1; this.say(`${h.name}'s wound closes for the third time, and leaves ${CM.SCARS[id].name}: ${CM.SCARS[id].what}.`); }
    }
    return true;
  },
  templeWounds() {
    const who = this.party.filter((h) => h.wound), cost = this.townPrice(CM.WOUND_HEAL * who.length * (this.asc("costlytemple") ? 2 : 1));
    if (!who.length) { this.say("No one here carries a wound."); return false; }
    if (this.gold < cost) { this.say(`The old priest asks ${cost} gold to close ${who.length === 1 ? "the wound" : "the wounds"}.`); return false; }
    this.logAct("temple", "wounds");
    this.gold -= cost; this.spend("temple", cost);
    for (const h of who) this.healWound(h);
    this.sound("heal"); this.say(`Clean linen and a long prayer: ${who.map((h) => h.name).join(", ")} ${who.length === 1 ? "is" : "are"} whole again.`);
    this.saveRun();
    return true;
  },
  // a tithe: a tenth of the purse for a blessing on the band (+1 defence, blows land a twentieth more, five floors)
  tithe() {
    if (!this.atShop()) return "The tithe is given at the temple.";
    const cost = Math.max(10, Math.floor(this.gold / 10));
    if (this.gold < cost) return "The priest wants at least ten gold for the candles.";
    if (this.blessed()) return "The band is blessed already. The priest says once is enough.";
    this.logAct("tithe");
    this.gold -= cost; this.spend("tithe", cost);
    this.blessedUntil = this.floor.number + CM.TITHE_FLOORS;
    this.sound("heal"); this.say(`${cost} gold goes into the box, and the priest blesses the party for the band: a little harder to hurt, a little surer of hand, until floor ${this.blessedUntil}.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  blessed() { return Boolean(this.floor && this.blessedUntil && this.floor.number <= this.blessedUntil); },
  // ---- the merchant's orders and insurance ----
  // an order: a thing from the merchant's list, paid now at a tenth over, delivered at the next camp
  order(what) {
    if (!this.atShop() || !this.shopping) return "Orders are placed with the merchant.";
    const make = CM.ORDERABLE[what]; if (!make) return "The merchant has never heard of it.";
    const item = make(this.floor.number + 3), price = Math.ceil(CM.priceAt(item.value, this.floor.number) * CM.ORDER_OVER);
    if (this.gold < price) return `An order for ${item.name} is ${price} gold, paid now.`;
    this.logAct("order", what);
    this.gold -= price; this.spend("orders", price);
    this.orders = (this.orders || []).concat({ item, from: this.floor.number });
    this.sound("coin"); this.say(`The merchant writes it down: ${item.name}, ${price} gold, to be waiting at the next camp.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  deliverOrders() {
    const due = (this.orders || []).filter((o) => o.from < this.floor.number);
    if (!due.length) return;
    this.orders = this.orders.filter((o) => !due.includes(o));
    this.gain(due.map((o) => o.item), "order");
    this.say(`The merchant has your order${due.length > 1 ? "s" : ""} waiting: ${due.map((o) => o.item.name).join(", ")}.`);
    this.tally.ordersDelivered = (this.tally.ordersDelivered || 0) + due.length;
  },
  // insurance: a tenth of a thing's value, and if the party falls it goes to the vault for the next
  insure(row, slot) {                                                   // (row: a bag row; with a slot, row is the hero whose worn thing it is)
    if (!this.atShop()) return "Insurance is bought from the merchant.";
    const item = slot ? (this.party[row] || {})[slot] : this.bag[row]; if (!item) return "Pick something from your pack.";
    if (item.insured) return `${item.name} is insured already.`;
    if (!item.value || ["torch", "ration", "key", "boxkey", "bones", "rope"].includes(item.kind)) return "The merchant won't insure that.";
    const cost = Math.max(5, Math.ceil(item.value * CM.INSURE_RATE));
    if (this.gold < cost) return `Insuring ${item.name} is ${cost} gold.`;
    if (slot) this.logAct("insure", row, slot); else this.logAct("insure", row);
    this.gold -= cost; this.spend("insurance", cost); item.insured = true;
    this.sound("coin"); this.say(`${item.name} is insured for ${cost} gold: if the party falls, it goes to the vault.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  payInsurance() {
    const worn = this.party.flatMap((h) => CM.equipped(h)), all = this.bag.concat(worn).filter((it) => it && it.insured);
    if (!all.length) return 0;
    this.vaults = (this.vaults || []).concat(all.map((it) => Object.assign({}, it, { insured: false, bearers: it.bearers || [] })));
    CM.store.set("vaults", this.vaults); CM.store.remove("vault");
    this.say(`The merchant's word is good: ${all.map((it) => it.name).join(", ")} ${all.length === 1 ? "goes" : "go"} to the vault for whoever comes after.`);
    this.tally.insured = (this.tally.insured || 0) + all.length;
    return all.length;
  },
  // ---- bounties: three of a kind, for gold and renown, at every camp ----
  bountyKind() {
    const n = this.floor.number, kinds = n <= CM.LAST_FLOOR ? (() => { const top = Math.min(CM.SHALLOW - 1, Math.floor(n * CM.SHALLOW / CM.LAST_FLOOR)); return CM.MONSTERS.slice(Math.max(0, top - 2), top + 1); })() : CM.MONSTERS.filter((m) => m.deep === CM.themeIndex(n));
    const pool = kinds.length ? kinds : CM.MONSTERS.slice(0, 3);
    return pool[CM.hashSeed(`${this.seed}:bounty:${n}`) % pool.length].name;
  },
  takeBounty() {
    if (!this.atShop()) return "The bounty board is at the camp, and at the Hanged Lantern.";
    if (this.bounty) return this.bountyDone() ? "The bounty is earned: claim it." : `A bounty is open already: ${CM.plural(CM.BOUNTY_NEED, this.bounty.kind)} (${this.bountyProgress()} so far).`;
    const kind = this.bountyKind(); this.logAct("takeBounty");
    this.bounty = { kind, from: ((this.bestiary || {})[kind] || {}).slain || 0, floor: this.floor.number, reward: 60 + 40 * this.floor.number, renown: 1 };
    this.say(`The board: ${CM.plural(CM.BOUNTY_NEED, kind)}, ${this.bounty.reward} gold and a word in the village. Taken.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  bountyProgress() { return this.bounty ? Math.min(CM.BOUNTY_NEED, (((this.bestiary || {})[this.bounty.kind] || {}).slain || 0) - this.bounty.from) : 0; },
  bountyDone() { return Boolean(this.bounty) && this.bountyProgress() >= CM.BOUNTY_NEED; },
  claimBounty() {
    if (!this.atShop()) return "Bounties are paid at the camp, and at the Hanged Lantern.";
    if (!this.bounty) return "No bounty is open.";
    if (!this.bountyDone()) return `Not yet: ${this.bountyProgress()} of ${CM.plural(CM.BOUNTY_NEED, this.bounty.kind)}.`;
    this.logAct("claimBounty");
    const b = this.bounty; this.bounty = null;
    this.gold += b.reward; this.count("goldFound", b.reward); this.tally.bounties = (this.tally.bounties || 0) + 1;
    this.village = this.village || {}; this.village.renown = (this.village.renown || 0) + b.renown; this.saveVillage();
    this.sound("coin"); this.say(`${b.reward} gold for the ${b.kind}s, and the village will hear of it (+${b.renown} renown).`);
    this.saveRun(); this.emit("change");
    return "";
  },
  // ---- the fence, at the tavern: unknowns at half, cursed things taken for nothing, and rumours of strongboxes sold ----
  fence(row) {
    if (!this.inTown()) return "The fence drinks at the Hanged Lantern, in town.";
    const item = this.bag[row]; if (!item) return "Pick something from your pack.";
    const cursed = item.props && item.props.cursed;
    if (!item.unknown && !cursed) return "The fence only wants what the merchant won't take: what no one can name, and what is cursed.";
    this.logAct("fence", row);
    this.bag.splice(row, 1);
    const paid = cursed ? 0 : Math.floor(item.value / 2);
    this.gold += paid; this.tally.fenced = (this.tally.fenced || 0) + 1;
    this.sound("coin"); this.say(cursed ? `The fence takes ${item.name} off your hands for nothing, and does not ask what it did.` : `The fence turns ${CM.baseName(item)} over once and pays ${paid} gold for it, no questions.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  fenceRumour() {
    if (!this.inTown()) return "The fence drinks at the Hanged Lantern, in town.";
    if (this.gold < CM.RUMOUR_PRICE) return `A rumour is ${CM.RUMOUR_PRICE} gold.`;
    if (this.rumourBox) return `The fence has told you what he knows: floor ${this.rumourBox}.`;
    let found = 0;
    for (let n = this.floor.number + 1; n <= this.floor.number + 6 && !found; n++) { const f = CM.makeFloor(n, this.seed, this.gen || 1); if (Object.values(f.things).some((t) => t.type === "strongbox")) found = n; }
    this.logAct("buyRumour");
    this.gold -= CM.RUMOUR_PRICE; this.spend("fence", CM.RUMOUR_PRICE);
    if (!found) { this.say("The fence takes the gold and admits, after it, that he knows of no strongbox on the next six floors."); this.saveRun(); return ""; }
    this.rumourBox = found;
    this.say(`The fence leans in: an iron strongbox on floor ${found}, and its key two floors above it. It will be on your map when you get there.`);
    this.saveRun(); this.emit("change");
    return "";
  },

  // the night passes: the clock goes to the next dawn (six), a full day if it is dawn already
  sleepTillDawn() { const m = CM.minuteOf(this), to = m < CM.CLOCK.start ? CM.CLOCK.start - m : CM.CLOCK.day - m + CM.CLOCK.start; this.clock = (this.clock || 0) + to; return to; },
  // the camp's temple: ailments cured, a curse lifted (from the party, and from what they wear), stone made flesh - for a price
  temple(service) {
    if (service === "wounds") return this.templeWounds();
    const cost = this.townPrice(Math.ceil({ cure: 30, uncurse: 60, unstone: 150 }[service] * (this.asc("costlytemple") ? 2 : 1) * (this.party.some((h) => h.quirk === "pious" && h.hp > 0) ? 0.5 : 1)));
    const which = service === "cure" ? CM.CURABLE : service === "uncurse" ? ["curse"] : ["stone"];
    const cursedGear = service === "uncurse" ? this.party.flatMap((h) => CM.equipped(h).filter((it) => it.props && it.props.cursed)) : [];
    const who = this.party.filter((h) => which.some((s) => (h.status || {})[s]));
    if (!who.length && !cursedGear.length) {
      this.say({ cure: "No one here is ailing.", uncurse: "No curse lies on the party, nor on what they carry.", unstone: "No one here is stone." }[service]);
      return false;
    }
    if (this.gold < cost) { this.say(`The old priest asks ${cost} gold for that.`); return false; }
    this.logAct("temple", service);
    this.gold -= cost; this.spend("temple", cost);
    for (const h of who) this.cure(h, which);
    for (const it of cursedGear) { it.props.cursed = false; if (it.props.curse === "weak" && it.props.stats) { for (const st of Object.keys(it.props.stats)) if (it.props.stats[st] < 0) { it.props.stats[st] += 2; if (!it.props.stats[st]) delete it.props.stats[st]; } } delete it.props.curse; if (!it.props.tier) it.power += 3; if (it.props.rarity === "cursed") it.props.rarity = (it.props.affixes || []).length === 2 ? "rare" : "fine"; }
    this.sound("heal");
    this.say({ cure: "Herbs and prayers: the party's ailments pass.",
      uncurse: "The priest's chant lifts the curse" + (cursedGear.length ? `, and ${cursedGear.map((i) => i.name).join(", ")} can be put down at last.` : "."),
      unstone: `Stone becomes flesh again: ${who.map((h) => h.name).join(", ")} can move.` }[service]);
    this.saveRun();
    return true;
  },

  // the priest's scribe names everything unknown in the pack and on the party's backs
  scribe() {
    const unknown = [...this.bag, ...this.party.flatMap(CM.equipped)].filter((i) => i.unknown);
    if (!unknown.length) { this.say("Nothing you carry is unknown to you."); return false; }
    if (this.gold < 25) { this.say("The scribe asks 25 gold to name what you carry."); return false; }
    this.logAct("scribe");
    this.gold -= 25; this.spend("temple", 25);
    for (const it of unknown) this.reveal(it);
    this.sound("spell");
    this.say(`The scribe squints and names them: ${unknown.map((i) => i.name).join(", ")}.`);
    this.saveRun();
    return true;
  },

  // the tavern: three who'd come along, for a price - one of them for a hero who has fallen
  tavern() {
    if (!this.recruits || this.recruits.floor !== this.floor.number) {
      const level = Math.max(1, Math.round(this.party.reduce((s, h) => s + h.level, 0) / Math.max(1, this.party.length)) - 1 + (this.villageLevel("tavern") >= 2 ? 1 : 0));   // (the Hanged Lantern's better bench)
      const rnd = new CM.Random(CM.hashSeed(`${this.seed}:tavern:${this.floor.number}`));
      this.recruits = { floor: this.floor.number, who: [0, 1, 2].map(() => CM.makeRecruit(level, rnd, this.classesAvailable())) };
      const met = ((this.village || {}).met || []);                      // (guildhall level 3: the third is someone rescued in a run before)
      if (this.villageLevel("guildhall") >= 3 && met.length) { const old = Object.assign({}, met[CM.hashSeed(`${this.seed}:met:${this.floor.number}`) % met.length]); old.level = Math.max(old.level, level); CM.recompute(old); old.hp = old.max; old.mp = old.maxmp; old.price = 20 + 40 * old.level; this.recruits.who[2] = old; }
      if (this.villageLevel("shrine") >= 4) { const back = (this.memorial || []).find((m) => m.candle && !m.returned); if (back && !this.recruits.who.some((r) => r.name === back.name)) { const h = CM.makeHero(back.cls, back.name, CM.rollStats(back.cls, new CM.Random(CM.hashSeed(back.name)))); h.level = Math.max(1, back.level); CM.recompute(h); h.hp = h.max; h.mp = h.maxmp; h.price = 0; h.remembered = true; this.recruits.who[0] = h; } }
    }
    return (this.rescued || []).length ? this.rescued.concat(this.recruits.who) : this.recruits.who;   // (the rescued first, and free)
  },

  hire(i, replace) {
    const recruit = this.tavern()[i];
    if (!recruit) return "No one by that name.";
    const fallen = this.party.map((h, idx) => idx).filter((idx) => this.party[idx].hp <= 0 || (this.party[idx].status || {}).stone);
    if (!fallen.length) return "The party is whole. The recruits drink to that.";
    const idx = replace === undefined ? fallen[0] : replace;
    if (!fallen.includes(idx)) return `${this.party[idx].name} is still standing.`;
    if (this.gold < recruit.price) return `${recruit.name} wants ${recruit.price} gold to come along.`;
    this.logAct("hire", i, replace === undefined ? null : replace);
    this.gold -= recruit.price; this.spend("tavern", recruit.price);
    const rescued = (this.rescued || []).length;
    const gone = this.party[idx];
    for (const slot of CM.SLOTS) if (gone[slot] && !(slot === "weapon" || slot === "armor")) this.bag.push(gone[slot]);   // (their trinkets stay with the party)
    this.remember2(gone);
    this.bonds = (this.bonds || []).filter((b) => !b.includes(gone.name));
    const h = Object.assign({}, recruit);
    delete h.price;
    if (h.remembered) { const m = (this.memorial || []).find((x) => x.name === h.name && x.candle && !x.returned); if (m) { m.returned = true; CM.store.set("memorial", this.memorial); } delete h.remembered; }
    this.party[idx] = h;
    this.applyBonds();
    if (i < rescued) this.rescued.splice(i, 1); else this.recruits.who.splice(i - rescued, 1);
    this.sound("coin");
    this.say(`${gone.name} is laid to rest by the fire. ${h.name} the ${h.cls} takes up their place${recruit.price ? "" : ", owing you their life"}.`);
    this.saveRun();
    this.emit("change");
    return "";
  },

  // the camp's smith: a diamond and gold put +1 on a piece of gear (up to +3 of his work); a ruby, sapphire or sunstone
  // and gold put fire, frost or holiness into a weapon. "" when it worked, else why not.
  smith(service, heroIndex, slot) {
    if (!this.atShop()) return "The smith works at the camp, and at the forge in town.";
    this.logAct("smith", service, heroIndex, slot);
    const hero = this.party[heroIndex], item = hero && hero[slot];
    if (service !== "recharge" && (!item || !["weapon", "armor", "offhand", "helm"].includes(slot))) return "Pick a weapon, armour, a shield or a helm.";
    if (item && item.unknown && service !== "recharge") return "The smith won't work on a thing nobody can name. Have it identified first.";
    const p = item ? (item.props = item.props || {}) : {};
    if (service === "enchant") {
      const n = p.enchant || 0, cost = CM.SMITH.enchant * (n + 1), gem = this.bag.findIndex((i) => i.kind === "gem" && i.gem === "diamond");
      const scrap = this.bag.map((i, idx) => (i.kind === "scrap" ? idx : -1)).filter((idx) => idx >= 0);
      if (n >= CM.SMITH.most) return `${item.name} has had all the smith's work it can take.`;
      if (gem < 0 && scrap.length < 5) return "The smith wants a diamond for the work (or five pieces of scrap).";
      if (this.gold < cost) return `The smith wants ${cost} gold, and the diamond.`;
      this.gold -= cost; this.spend("smith", cost);
      if (gem >= 0) this.bag.splice(gem, 1); else for (const idx of scrap.slice(0, 5).reverse()) this.bag.splice(idx, 1);
      p.enchant = n + 1;
      p.bonus = (p.bonus || 0) + 1;
      item.power += 1;
      item.value += 60;
      item.name = CM.itemName(item);
      CM.recompute(hero);
      this.sound("lever");
      this.say(`The smith works ${hero.name}'s ${CM.baseName(item)} by the fire, and sets the diamond in it: ${item.name}.`);
      if (p.enchant >= CM.SMITH.most) this.achieve("smith");
    } else if (service === "gem") {
      if (slot !== "weapon") return "A gem of fire, frost or holiness goes into a weapon.";
      const gem = this.bag.findIndex((i) => i.kind === "gem" && CM.GEMS[i.gem].element);
      if (gem < 0) return "The smith wants a ruby, a sapphire or a sunstone for a weapon.";
      if (this.gold < CM.SMITH.gem) return `The smith wants ${CM.SMITH.gem} gold to set a gem.`;
      const el = CM.GEMS[this.bag[gem].gem].element, name = this.bag[gem].name;
      this.gold -= CM.SMITH.gem; this.spend("smith", CM.SMITH.gem);
      this.bag.splice(gem, 1);
      p.element = el;
      item.value += 80;
      item.name = CM.itemName(item);
      this.sound("lever");
      this.say(`The smith sets the ${name.toLowerCase()} into ${hero.name}'s blade, and it takes: ${item.name}.`);
    } else if (service === "reroll") {                                  // a gem of any kind and gold: the suffix is struck off and another worked in
      if (!["weapon", "armor", "offhand", "helm"].includes(slot)) return "The smith reworks a weapon, armour, a shield or a helm.";
      const gem = this.bag.findIndex((i) => i.kind === "gem"), cost = 100, ess = this.bag.map((i, idx) => (i.kind === "essence" ? idx : -1)).filter((idx) => idx >= 0);
      const essenceHeld = ess.reduce((n, idx) => n + (this.bag[idx].power || 1), 0);
      if (gem < 0 && essenceHeld < CM.ESSENCE_FOR_GEM) return `The smith wants a gem of any kind to rework an affix (or ${CM.ESSENCE_FOR_GEM} essence).`;
      if (this.gold < cost) return `The smith wants ${cost} gold, and a gem.`;
      this.gold -= cost; this.spend("smith", cost);
      if (gem >= 0) this.bag.splice(gem, 1); else { let need = CM.ESSENCE_FOR_GEM; for (const idx of ess.slice().reverse()) { if (need <= 0) break; const e = this.bag[idx]; if ((e.power || 1) <= need) { need -= e.power || 1; this.bag.splice(idx, 1); } else { e.power -= need; need = 0; } } }
      const rnd = this.rnd, deep = this.floor.number > CM.LAST_FLOOR;
      const old = (p.affixes || []).find((w) => w.startsWith("of ")), prefix = (p.affixes || []).find((w) => !w.startsWith("of "));
      if (old) { const a = CM.AFFIXES.suffix[old]; if (a) for (const [k, v] of Object.entries(a)) { if (k === "stats") for (const [st, d] of Object.entries(v)) { p.stats[st] -= d; if (!p.stats[st]) delete p.stats[st]; } else if (k === "element") delete p.element; else if (k !== "deep" && k !== "weapon") delete p[k]; } }
      const choices = Object.entries(CM.AFFIXES.suffix).filter(([w, a]) => w !== old && (!a.deep || deep) && (!a.weapon || item.kind === "weapon") && !(a.element && p.element));
      const [word, a] = rnd.pick(choices);
      for (const [k, v] of Object.entries(a)) { if (k === "deep" || k === "weapon") continue; if (k === "stats") { p.stats = p.stats || {}; for (const [st, d] of Object.entries(v)) p.stats[st] = (p.stats[st] || 0) + d; } else if (k === "element") p.element = v; else p[k] = v; }
      p.affixes = [prefix, word].filter(Boolean); p.rarity = p.affixes.length === 2 ? "rare" : "fine";
      item.base = item.base || CM.baseName(item);
      item.name = `${prefix ? prefix + " " : ""}${p.element ? CM.ELEMENTS[p.element].prefix + " " : ""}${item.base} ${word}${p.bonus ? ` +${p.bonus}` : ""}`;
      CM.recompute(hero);
      this.sound("lever");
      this.say(`The smith strikes the old work off ${hero.name}'s ${item.base} and works the gem in: ${item.name}.`);
    } else if (service === "recharge") {                                // a gem of any kind and 60 gold: three charges into a wand in the pack
      const wand = this.bag.findIndex((i) => i.kind === "wand"), gem = this.bag.findIndex((i) => i.kind === "gem"), cost = 60;
      if (wand < 0) return "No wand in the pack to charge.";
      if (gem < 0) return "The smith wants a gem of any kind to charge a wand.";
      if (this.gold < cost) return `The smith wants ${cost} gold, and a gem.`;
      this.gold -= cost; this.spend("smith", cost); this.bag.splice(gem, 1);
      const w = this.bag[wand < gem ? wand : wand - 1]; w.charges = (w.charges || 0) + 3;
      this.sound("lever"); this.say(`The smith grinds the gem into the ${w.name}: ${CM.plural(w.charges, "charge")}.`);
    } else if (service === "move") {                                    // a prefix moved from a thing in the pack to the worn one; the pack's thing is scrap
      const from = this.bag.findIndex((i) => ["weapon", "armor", "shield", "helm"].includes(i.kind) && !i.unknown && (i.props || {}).affixes && i.props.affixes.some((w) => !w.startsWith("of ")) && !(i.props.relic || i.props.unique) && (i.kind === "weapon") === (item.kind === "weapon"));
      if (from < 0) return "The smith wants a thing in the pack with a prefix to move, of the same kind of make (a weapon's word for a weapon, armour's for the rest).";
      const cost = 150; if (this.gold < cost) return `The smith wants ${cost} gold to move a word.`;
      const src = this.bag[from], word = src.props.affixes.find((w) => !w.startsWith("of ")), table = CM.AFFIXES.prefix[item.kind === "weapon" ? "weapon" : "armor"], a = table[word];
      if (!a) return "The smith can't read that word.";
      const oldPrefix = (p.affixes || []).find((w) => !w.startsWith("of "));
      if (oldPrefix && table[oldPrefix]) { const old = CM.scaledAffix(table[oldPrefix], p.tier || 1); for (const [k, v] of Object.entries(old)) { if (k === "power") item.power -= v; else if (k === "stats") { for (const [st, d] of Object.entries(v)) { p.stats[st] -= d; if (!p.stats[st]) delete p.stats[st]; } } else if (typeof v === "number" && typeof p[k] === "number") { p[k] -= v; if (!p[k]) delete p[k]; } else delete p[k]; } }
      this.gold -= cost; this.spend("smith", cost);
      const tier = src.props.tier || 1;
      CM.applyProps(item, CM.scaledAffix(a, tier));
      p.affixes = [word].concat((p.affixes || []).filter((w) => w.startsWith("of "))); p.tier = Math.max(p.tier || 1, tier); p.rarity = p.affixes.length === 2 ? "rare" : "fine";
      this.bag.splice(from, 1, CM.scrap());
      item.name = CM.itemName(item);
      CM.recompute(hero);
      this.sound("lever");
      this.say(`The smith lifts the word ${word} off the ${CM.baseName(src)} and works it into ${hero.name}'s ${CM.baseName(item)}: ${item.name}. The ${CM.baseName(src)} is scrap.`);
    } else return "The smith doesn't do that.";
    this.saveRun();
    this.emit("change");
    return "";
  },

  // the guildhall at a camp: a hero at twenty takes a second calling, for renown - its first two spells or skills
  secondCalling(heroIndex, cls) {
    if (!this.atShop()) return "The guild's letter is read at a camp, or at the guildhall in town.";
    const h = this.party[heroIndex];
    if (!h || h.hp <= 0) return "Only a hero standing.";
    if (this.villageLevel("guildhall") < 2) return "The guildhall must be of the second level.";
    if (h.level < CM.SECOND_AT) return `${h.name} must be level ${CM.SECOND_AT}.`;
    if (h.second) return `${h.name} is a ${h.second} already, besides.`;
    if (!CM.CLASSES[cls] || cls === h.cls || !this.classUnlocked(cls)) return "Not that calling.";
    if (this.renown() < CM.SECOND_COST) return `The guild asks ${CM.SECOND_COST} renown.`;
    this.logAct("secondCalling", heroIndex, cls);
    this.village.spent = (this.village.spent || 0) + CM.SECOND_COST; this.saveVillage();
    h.second = cls;
    if (CM.CLASSES[cls].mp && !h.maxmp) { h.maxmp = 6; h.mp = 6; }
    this.sound("level");
    this.say(`${h.name} reads the guild's letter, and is a ${cls} too: ${CM.abilitiesFor(h).filter((id) => CM.ABILITIES[id].cls[cls] !== undefined && CM.ABILITIES[id].cls[cls] <= 2).map((id) => CM.ABILITIES[id].name).join(", ")}.`);
    this.saveRun(); this.emit("change");
    return "";
  },

  // a piece of gear from the pack goes into the smith's fire for scrap (one each; five stand in for a diamond)
  salvage(row) {
    if (!this.atShop()) return "The smith works at the camp, and at the forge in town.";
    this.logAct("salvage", row);
    const item = this.bag[row];
    if (!item || !["weapon", "armor", "shield", "helm"].includes(item.kind)) return "The smith breaks down a weapon, armour, a shield or a helm.";
    if (item.props && (item.props.relic || item.props.unique)) return "The smith won't put that in the fire. Nor should you.";
    this.bag.splice(row, 1);
    const n = 1 + (item.props && item.props.rarity === "rare" ? 1 : 0);
    for (let i = 0; i < n; i++) this.bag.push(CM.scrap());
    const ess = item.unknown ? 0 : (item.props || {}).rarity === "rare" || (item.props || {}).cursed ? 2 : (item.props || {}).rarity === "fine" ? 1 : 0;   // essence: what a worded thing leaves besides scrap
    if (ess) { const have = this.bag.find((i) => i.kind === "essence"); if (have) have.power += ess; else this.bag.push(CM.essence(ess)); }
    this.sound("lever");
    this.say(`The ${item.unknown ? CM.baseName(item) : item.name} goes into the fire and comes out as ${CM.plural(n, "piece")} of scrap${ess ? `, and ${CM.plural(ess, "essence")}` : ""}.`);
    this.saveRun();
    this.emit("change");
    return "";
  },

  // the kitchen: meat cooked at a camp, or on the floor for a torch, into a meal that feeds the party and lasts the next floor
  cook(row) {
    const item = this.bag[row]; if (!item || item.kind !== "meat") return "Nothing to cook.";
    const M = CM.MEALS[item.meat]; if (!M) return "Nobody would eat that.";
    if (this.mode !== "camp") { const torch = this.bag.findIndex((i) => i.kind === "torch"); if (torch < 0) return "A fire wants a torch from the pack, down here."; this.bag.splice(torch, 1); if (torch < row) row -= 1; }
    this.logAct("cook", row);
    this.bag.splice(row, 1); this.countUse("meal");
    this.fed = 0; this.cheer(4);
    this.meal = { kind: item.meat, floor: (this.floor ? this.floor.number : 0) + 1 };
    for (const h of this.party) { h.mealLuck = M.luck || 0; CM.recompute(h); }
    this.sound("heal");
    this.say(`The party eats ${M.name}: ${M.what}, until the floor after next is reached.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  // the alchemist's request: three of the band's ingredient this camp, and the next brew is free
  alchemistWants() { const band = CM.themeIndex(this.floor ? this.floor.number : 1); return Object.keys(CM.INGREDIENTS).find((id) => CM.INGREDIENTS[id].band === band && !CM.INGREDIENTS[id].rare) || "gravemoss"; },
  deliver() {
    if (!(this.mode === "camp" || (this.inTown() && this.villageLevel("garden") >= 3))) return "The alchemist is at the camp, and in the garden once it has three beds.";
    const want = this.alchemistWants(), rows = this.bag.map((i, idx) => (i.kind === "ingredient" && i.ingredient === want ? idx : -1)).filter((i) => i >= 0);
    if (rows.length < 3) return `She wants three of ${CM.INGREDIENTS[want].name}; the pack has ${rows.length}.`;
    if (this.alchemistFree) return "The next brew is free already.";
    this.logAct("deliver");
    for (const idx of rows.slice(0, 3).reverse()) this.bag.splice(idx, 1);
    this.alchemistFree = true;
    this.sound("coin"); this.say(`The alchemist takes the ${CM.INGREDIENTS[want].name} gladly: the next thing she brews is on the house.`); this.saveRun(); this.emit("change");
    return "";
  },
  // the vault: one thing left at the camp waits for the next party (saved between runs); what was there comes out
  leaveHeirloom(row) {
    if (this.mode !== "camp") return "The vault is at the camp.";
    this.logAct("leaveHeirloom", row);
    const item = this.bag[row];
    if (!item) return "Pick something from your pack.";
    if (["key", "bones", "rope", "torch"].includes(item.kind)) return "The merchant won't keep that. Something worth the keeping.";
    this.vaults = this.vaults || [];
    const old = this.vaultRoom() || item.named ? null : this.vaults.splice(this.vaults.findIndex((it) => !it.named), 1)[0];
    this.bag.splice(row, 1);
    this.vaults.push(item);
    CM.store.set("vaults", this.vaults);
    if (old) this.bag.push(old);
    this.sound("chest");
    this.say(`The merchant locks ${item.name} in the vault for whoever comes after${old ? `, and hands back ${old.name}` : ""}.`);
    this.saveRun();
    this.emit("change");
    return "";
  },
  takeHeirloom(i = 0) {
    if (this.mode !== "camp") return "The vault is at the camp.";
    this.logAct("takeHeirloom", i);
    if (!(this.vaults || []).length) return "The vault is empty.";
    const item = this.vaults.splice(Math.min(i, this.vaults.length - 1), 1)[0];
    CM.store.set("vaults", this.vaults);
    CM.store.remove("vault");
    item.bearers = item.bearers || [];                                   // (an heirloom remembers who wore it; the third bearer wears it as a relic)
    this.gain([item], "vault");
    this.sound("chest");
    this.say(`The merchant unlocks the vault: ${item.name}, left by a party before you.`);
    this.saveRun();
    this.emit("change");
    return "";
  },

  raiseDead() {
    const fallen = this.party.filter((m) => m.hp <= 0);
    if (!fallen.length) { this.say("No one needs raising."); return; }
    const hero = fallen[0], cost = this.townPrice(100 * hero.level * (this.asc("costlytemple") ? 2 : 1));
    if (this.gold < cost) { this.say(`The old priest asks ${cost} gold to raise the ${hero.cls}.`); return; }
    this.logAct("raiseDead");
    this.gold -= cost; this.spend("temple", cost);
    hero.hp = hero.max;
    this.sound("heal");
    this.say(`For ${cost} gold, the priest raises the ${hero.cls}!`);
    this.woundHero(hero);
    this.saveRun();
  },

  leaveCamp() {
    this.logAct("leaveCamp");
    this.stock = null;
    this.enterFloor(this.floor.number + 1, "down");
  },

  backUp() {                                                             // from the camp, back onto the floor above it
    this.logAct("backUp");
    this.stock = null;
    const ladder = this.cellOf(this.floor, "ladder");
    if (ladder) this.floor.pos = ladder.slice();
    this.setMode("explore");
    this.look();
    this.emit("floor", this.floor);
    this.saveRun();
    this.say(`Back up the shaft to floor ${this.floor.number}.`);
  },

  potionCount() { return this.bag.filter((i) => ["heal", "mana", "revive", "antidote"].includes(i.kind)).length; },
});
}

// ---- waystones: every camp reached is a waystone, and from any camp the party may go to another it has reached
// (the floors between stay as they were left) ----
{
Object.assign(CM.Game.prototype, {
  reachCamp(n) {
    this.camps = this.camps || [];
    if (!this.camps.includes(n)) { this.camps.push(n); this.camps.sort((a, b) => a - b); if (this.camps.length > 1) this.say("The merchant chalks a mark by the fire: a waystone. From any camp you can walk the old road to another."); }
  },
  // to the camp below floor n, from a camp
  // from a camp, back up to the town (the shaft's mouth); the shaft brings the party down again to the deepest camp reached
  goHome() {
    if (this.mode !== "camp") return "The way home is from a camp.";
    this.logAct("goHome");
    this.stock = null; this.recruits = null;
    const town = this.floorAt(0), shaft = this.cellOf(town, "ladder") || CM.TOWN_AT.shaft.slice();
    this.enterFloor(0, "rope", shaft);
    this.say("The long climb, and daylight: Caer Duin above, and the shaft's mouth behind you. The shaft goes down again to the deepest camp you reached.");
    this.emit("change");
    return "";
  },
  waystone(n) {
    if (this.mode !== "camp") return "The waystones are at the camps.";
    this.logAct("waystone", n);
    if (!(this.camps || []).includes(n)) return "No camp there that you have reached.";
    if (this.floor && this.floor.number === n) return "You are there already.";
    this.stock = null; this.recruits = null;
    const above = this.floorAt(n);
    this.leaveFloor();
    this.floor = above;
    const ladder = this.cellOf(above, "ladder");
    if (ladder) above.pos = ladder.slice();
    this.emit("floor", above);
    this.sound("stairs");
    this.say(`The old road between the camps: a long walk in the dark, and the merchant's lantern below floor ${n} again.`);
    this.saveRun();
    this.emit("change");
    return "";
  },
});
}

// ---- the pack, looked after: what a thing would change for a hero, and the pack in order ----
{
const RANK = { weapon: 0, armor: 1, shield: 2, helm: 3, ring: 4, amulet: 5, heal: 6, mana: 7, revive: 8, antidote: 9, scroll: 10, wand: 11, tome: 12, gem: 13, torch: 14, lantern: 15, rope: 16, key: 17, bones: 18 };
Object.assign(CM.Game.prototype, {
  // {text, cls, why} for the bag's buttons: "+2" against what the hero wears, "can't" with the reason, nothing for a potion
  compare(h, item) {
    if (!item || !["weapon", "armor", "shield", "helm", "ring", "amulet", "trinket", "boots", "cloak"].includes(item.kind)) return null;
    const why = CM.cantWear(h, item);
    if (why) return { text: "can't", cls: "bad", why };
    if (item.unknown) return { text: "?", cls: "", why: "Unknown until worn, read with a scroll, or shown to the scribe" };
    const slot = item.slot || (item.kind === "shield" ? "offhand" : item.kind), old = h[slot];
    if (item.kind === "ring" || item.kind === "amulet" || item.kind === "trinket") {
      const same = old && !old.unknown && CM.itemLabel(old) === CM.itemLabel(item);
      return { text: same ? "same" : old ? "swap" : "new", cls: same ? "" : "good", why: old ? `Wears ${old.unknown ? CM.baseName(old) : old.name} (${CM.itemLabel(old)})` : "Nothing there now" };
    }
    const d = item.power - (old ? old.power : 0);
    if (item.kind === "weapon" && !(item.props || {}).fists && !CM.atHome(h, item)) return { text: d > 0 ? `+${d}?` : String(d), cls: d > 0 ? "" : "bad", why: `${h.cls}s are not at home with a ${CM.WEAPON_CLASSES[CM.weaponClass(item)].name}: blows land less often${old ? `; wears ${old.unknown ? CM.baseName(old) : old.name} (+${old.power})` : ""}` };
    return { text: d > 0 ? `+${d}` : d < 0 ? String(d) : "same", cls: d > 0 ? "good" : d < 0 ? "bad" : "", why: old ? `Wears ${old.unknown ? CM.baseName(old) : old.name} (+${old.power})` : "Nothing there now" };
  },
  sortBag() {
    this.logAct("sortBag");
    this.bag.sort((a, b) => (RANK[a.kind] === undefined ? 99 : RANK[a.kind]) - (RANK[b.kind] === undefined ? 99 : RANK[b.kind]) || (b.power || 0) - (a.power || 0) || String(a.name).localeCompare(String(b.name)));
    this.dirty = true;
    this.emit("change");
  },
});
}

// ---- the alchemist: a woman with a copper still by the camp fire, who makes things of what the monsters drop ----
{
Object.assign(CM.Game.prototype, {
  // what a recipe needs that the pack hasn't: "" when it can be brewed
  recipeLacks(id) {
    const r = CM.RECIPES[id];
    if (!r) return "No such recipe.";
    const have = (kinds, used) => this.bag.findIndex((i, idx) => !used.includes(idx) && (i.kind === "ingredient" ? kinds.includes(i.ingredient) : kinds.includes(i.kind)));
    const used = [];
    for (const key of ["ingredient", "ingredient2", "kind"]) {
      if (!r.needs[key] || r.needs.triple) continue;
      const idx = have(r.needs[key], used);
      if (idx < 0) return `She wants ${r.needs[key].map((k) => (CM.INGREDIENTS[k] ? CM.INGREDIENTS[k].name : { heal: "a Healing Potion" }[k] || k)).join(" or ")}.`;
      used.push(idx);
    }
    if (r.needs.triple) { const count = {}; for (const i of this.bag) if (i.kind === "ingredient" && !CM.INGREDIENTS[i.ingredient].rare) count[i.ingredient] = (count[i.ingredient] || 0) + 1; if (!Object.values(count).some((n) => n >= 3)) return "She wants three of one band's ingredient, alike."; }
    const price = this.alchemistFree ? 0 : Math.ceil(r.gold * (this.mode !== "camp" && !this.inTown() ? CM.KIT_PRICE : 1));
    if (this.gold < price) return `She asks ${price} gold for the ${r.name}.`;
    if (r.makes === "greaterheal" && this.asc("nogreater")) return "No greater potions, this high on the ladder.";
    return "";
  },
  brew(id) {
    const kit = this.bag.some((i) => i.kind === "kit");
    if (this.inTown() && this.villageLevel("garden") < 1) return "The garden has no bench yet.";
    if (this.mode !== "camp" && !(this.mode === "explore" && kit) && !this.inTown()) return "The alchemist is at the camp.";
    const lacks = this.recipeLacks(id);
    if (lacks) return lacks;
    this.logAct("brew", id);
    const r = CM.RECIPES[id], used = [], onFloor = this.mode !== "camp" && !this.inTown();
    if (r.needs.triple) {                                                // transmutation: three alike into one of the band below's
      const count = {}; for (const i of this.bag) if (i.kind === "ingredient" && !CM.INGREDIENTS[i.ingredient].rare) count[i.ingredient] = (count[i.ingredient] || 0) + 1;
      const from = Object.keys(count).find((k) => count[k] >= 3), band = CM.INGREDIENTS[from].band, to = Object.keys(CM.INGREDIENTS).find((k) => CM.INGREDIENTS[k].band === Math.min(9, band + 1) && !CM.INGREDIENTS[k].rare);
      let left = 3; for (let i = this.bag.length - 1; i >= 0 && left; i--) if (this.bag[i].kind === "ingredient" && this.bag[i].ingredient === from) { this.bag.splice(i, 1); left--; }
      const price = this.alchemistFree ? 0 : Math.ceil(r.gold * (onFloor ? CM.KIT_PRICE : 1)); this.gold -= price; this.spend("alchemist", price); this.alchemistFree = false;
      const made = CM.ingredient(to); this.bag.push(made); this.countUse("brew");
      this.sound("spell"); this.say(`Three of ${CM.INGREDIENTS[from].name} go into the still and one ${made.name} comes out.`); this.saveRun(); this.emit("change");
      return "";
    }
    const take = (kinds) => { const idx = this.bag.findIndex((i, j) => !used.includes(j) && (i.kind === "ingredient" ? kinds.includes(i.ingredient) : kinds.includes(i.kind))); used.push(idx); return idx; };
    for (const key of ["ingredient", "ingredient2", "kind"]) if (r.needs[key]) take(r.needs[key]);
    for (const idx of used.sort((a, b) => b - a)) this.bag.splice(idx, 1);
    const price = this.alchemistFree ? 0 : Math.ceil(r.gold * (onFloor ? CM.KIT_PRICE : 1)); this.gold -= price; this.spend("alchemist", price); this.alchemistFree = false; this.countUse("brew");
    const fl = this.floor ? this.floor.number : 1;
    let made;
    if (r.makes === "greaterheal") { made = { name: "Greater Healing Potion", kind: "greaterheal", power: 2 * (20 + fl * 3), value: 60 }; this.bag.push(made); }
    else if (r.makes.startsWith("oil:")) { made = CM.oil(r.makes.slice(4)); this.bag.push(made); }
    else if (r.makes === "bomb") { made = CM.bomb(); this.bag.push(made); }
    else if (r.makes === "bait:poison") { made = CM.bait(true); this.bag.push(made); }
    else if (r.makes === "antidote2") { this.bag.push(CM.antidote(), CM.antidote()); made = { name: "two Antidotes" }; }
    else if (r.makes === "ration3") { this.bag.push(CM.ration(), CM.ration(), CM.ration()); made = { name: "three rations" }; }
    else if (r.makes.startsWith("flask:")) { made = CM.flask(r.makes.slice(6)); this.bag.push(made); }
    else if (r.makes === "salve") { made = { name: "Salve", kind: "salve", power: 0, value: 50 }; this.bag.push(made); }
    else if (r.makes === "bread") { made = { name: "Dwarven Bread", kind: "bread", power: 20, value: 40 }; this.bag.push(made); }
    else if (r.makes === "liniment") { made = { name: "Liniment", kind: "liniment", power: 10, value: 80 }; this.bag.push(made); }
    else if (r.makes.startsWith("elixir:") && CM.ELIXIRS[r.makes.slice(7)]) { made = CM.elixir(r.makes.slice(7)); this.bag.push(made); }
    else if (r.makes.startsWith("elixir:")) {
      const stat = r.makes.slice(7), h = this.alive().reduce((a, b) => (a.stats[stat] <= b.stats[stat] ? a : b));   // (whoever has least of it)
      h.stats[stat] = Math.min(25, h.stats[stat] + 1);
      CM.recompute(h);
      made = { name: `${r.name}: ${h.name} has +1 ${CM.STAT_NAMES[stat]}, for good` };
    }
    this.sound("spell");
    this.say(`The alchemist's still bubbles and runs clear: ${made.name}.`);
    if (r.makes.startsWith("elixir:")) this.achieve("distilled");
    this.saveRun();
    this.emit("change");
    return "";
  },
});
}

