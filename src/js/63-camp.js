"use strict";
// The bag and the camp: what the party carries, wears, drinks and reads; the merchant, the temple, the scribe, the
// tavern, the smith and the vault.
{
const keyOf = CM.keyOf;
Object.assign(CM.Game.prototype, {
  // ---- the bag, the merchant, the camp ----
  openBag(shop = false) {
    this.shopping = shop;
    if (shop && !this.stock) {
      const rnd = this.rnd, depth = this.floor.number + 3;
      this.stock = ["weapon", "weapon", "weapon", "armor", "armor", "armor", "shield", "helm"].map((k) => { const it = CM.makeItem(depth, rnd, k); it.unknown = false; return it; });
      this.stock.push({ name: "Healing Potion", kind: "heal", power: 20 + depth * 3, value: 20 },
        { name: "Mana Potion", kind: "mana", power: 12 + depth, value: 25 },
        { name: "Phoenix Feather", kind: "revive", power: 0, value: 120 }, CM.antidote(), CM.torch(), CM.lantern(), CM.scroll("identify"), CM.scroll("mapping"), CM.rope());
    }
    this.emit("bag", true);
  },

  closeBag() {
    this.emit("bag", false);
    this.saveRun();
    this.emit("change");
  },

  describe(item) {
    const plain = { heal: "heals", mana: "restores magic", revive: "raises the fallen", torch: "light, for a while", lantern: "light that lasts",
      key: "opens a locked door", antidote: "cures poison, sleep, paralysis and blindness", rope: "down a pit without the fall, and back up again",
      bones: "someone's, gathered up for a ghost who asked" }[item.kind];
    return plain || CM.itemLabel(item);
  },

  // what the hero wears in that slot goes back to the pack - unless a curse holds it
  takeOff(n, slot) {
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
    return true;
  },

  identify(row) {
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
    if (item.kind === "scroll") this.bag.splice(row, 1);
    else { item.charges -= 1; if (item.charges <= 0) { this.bag.splice(row, 1); this.say(`The ${item.name} is spent, and crumbles.`); } }
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
    if (item.spell === "fire") {
      if (item.kind === "wand") { const t = this.foeAt(who); if (!t) { this.say("Nothing left to aim at."); return false; } this.spellHit(t, 10 + 2 * L, `${h.name}'s wand spits fire:`, "fire"); }
      else { const dmg = 10 + 2 * L; for (const m of foes) this.spellHit(m, dmg, "", "fire"); this.say(`${h.name} reads the scroll: fire on every foe, ${dmg} each.`); }
    } else if (item.spell === "frost") {
      const dmg = 6 + 2 * L;
      let held = 0;
      for (const m of foes) { this.spellHit(m, dmg, "", "frost"); if (m.hp > 0 && !CM.unmoved(m) && this.rnd.chance(0.3)) { m.held = Math.max(m.held || 0, 1); held++; } }
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
    if (item.kind === "scroll") this.bag.splice(row, 1);
    else { item.charges -= 1; if (item.charges <= 0) { this.bag.splice(row, 1); this.say(`The ${item.name} is spent, and crumbles.`); } }
    this.emit("change");
    return true;
  },

  // what the party wears: the thing in the slot goes back to the pack; wearing an unknown thing is how you learn it
  equip(hero, row) {
    const item = this.bag[row];
    const why = CM.cantWear(hero, item);
    if (why) return why;
    const slot = item.slot || (item.kind === "shield" ? "offhand" : item.kind);
    const old = hero[slot];
    if (old && old.props && old.props.cursed) return `${hero.name}'s ${old.name} is cursed and won't come off. The camp's temple can lift it.`;
    hero[slot] = item;
    this.bag.splice(row, 1);
    if (old) this.bag.push(old);
    if (slot === "weapon" && item.props && item.props.twohanded && hero.offhand) {
      if (hero.offhand.props && hero.offhand.props.cursed) { hero[slot] = old; this.bag.splice(row, 0, item); if (old) this.bag.pop(); return `${hero.name}'s shield is cursed to the arm: no room for a two-handed weapon.`; }
      this.bag.push(hero.offhand);
      this.say(`${hero.name} slings the shield: the ${CM.baseName(item)} takes both hands.`);
      hero.offhand = null;
    }
    const learned = this.reveal(item);
    const ratio = hero.hp / hero.max;
    CM.recompute(hero);
    hero.hp = Math.max(1, Math.round(hero.max * ratio));
    this.sound("chest");
    if (item.props && item.props.cursed) this.say(`${hero.name} takes up the ${CM.baseName(item)} - and it clings! It's cursed.`);
    else if (learned) this.say(`${hero.name} tries the ${CM.baseName(item)}: it's ${item.name} (${CM.itemLabel(item)}).`);
    this.emit("change");
    return "";
  },

  give(row, n) {                                                        // returns a note for the bag screen, "" when it worked
    if (row < 0 || row >= this.bag.length) return "Pick something from your pack first.";
    const item = this.bag[row], hero = this.party[n];
    if (item.kind === "key") return "Keys turn in locks, not in hands. Walk into the locked door.";
    if (item.kind === "rope") return "The rope is for a pit: walk into one with it in the pack.";
    if (item.kind === "tome") return this.readTome(row, hero);
    if (item.kind === "gem") return "A gem is for the camp's smith: he sets it into gear, for gold.";
    if (item.kind === "bones") return "They're not yours to use. Someone on this floor wants them back.";
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
      this.light = { kind: "lantern", left: 0 };
      this.sound("spell");
      this.say(`${hero.name} lights the lantern. It won't run out.`);
      this.emit("change");
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
      hero.hp = Math.floor(hero.max / 2);
      this.bag.splice(row, 1);
      this.sound("heal");
    } else if (hero.hp <= 0) {
      return `${hero.name} has fallen. Raise them first.`;
    } else if (item.kind === "heal") {
      hero.hp = Math.min(hero.max, hero.hp + item.power);
      this.bag.splice(row, 1);
      this.sound("heal");
    } else if (item.kind === "mana") {
      if (!hero.maxmp) return `${hero.name} has no magic to restore.`;
      hero.mp = Math.min(hero.maxmp, hero.mp + item.power);
      this.bag.splice(row, 1);
      this.sound("heal");
    } else {
      return this.equip(hero, row);
    }
    this.emit("change");
    return "";
  },

  buy(row) {
    if (!this.stock || row < 0 || row >= this.stock.length) return "Pick something from the merchant's wares first.";
    const item = this.stock[row];
    if (this.gold < item.value) return "You can't afford that.";
    this.gold -= item.value;
    this.bag.push(Object.assign({}, item, item.props ? { props: Object.assign({}, item.props) } : {}));
    if (["weapon", "armor", "shield", "helm", "lantern"].includes(item.kind)) this.stock.splice(row, 1);
    this.sound("coin");
    this.emit("change");
    return "";
  },

  sell(row) {
    if (row < 0 || row >= this.bag.length) return "Pick something from your pack to sell.";
    const item = this.bag.splice(row, 1)[0];
    this.gold += item.unknown ? 10 : Math.floor(item.value / 2);       // (the merchant pays a pittance for what no one can name)
    this.sound("coin");
    this.emit("change");
    return "";
  },

  rest() {
    if (this.gold < 20) { this.say("The merchant wants 20 gold for a bedroll by the fire."); return; }
    this.gold -= 20;
    for (const m of this.alive()) { m.hp = m.max; m.mp = m.maxmp; this.cure(m, CM.CURABLE); }
    this.sound("heal");
    this.say("The party rests by the fire. Wounds close, magic returns, and the small ailments pass.");
    this.saveRun();
  },

  // the camp's temple: ailments cured, a curse lifted (from the party, and from what they wear), stone made flesh - for a price
  temple(service) {
    const cost = { cure: 30, uncurse: 60, unstone: 150 }[service];
    const which = service === "cure" ? CM.CURABLE : service === "uncurse" ? ["curse"] : ["stone"];
    const cursedGear = service === "uncurse" ? this.party.flatMap((h) => CM.equipped(h).filter((it) => it.props && it.props.cursed)) : [];
    const who = this.party.filter((h) => which.some((s) => (h.status || {})[s]));
    if (!who.length && !cursedGear.length) {
      this.say({ cure: "No one here is ailing.", uncurse: "No curse lies on the party, nor on what they carry.", unstone: "No one here is stone." }[service]);
      return false;
    }
    if (this.gold < cost) { this.say(`The old priest asks ${cost} gold for that.`); return false; }
    this.gold -= cost;
    for (const h of who) this.cure(h, which);
    for (const it of cursedGear) { it.props.cursed = false; it.power += 3; }
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
    this.gold -= 25;
    for (const it of unknown) this.reveal(it);
    this.sound("spell");
    this.say(`The scribe squints and names them: ${unknown.map((i) => i.name).join(", ")}.`);
    this.saveRun();
    return true;
  },

  // the tavern: three who'd come along, for a price - one of them for a hero who has fallen
  tavern() {
    if (!this.recruits || this.recruits.floor !== this.floor.number) {
      const level = Math.max(1, Math.round(this.party.reduce((s, h) => s + h.level, 0) / Math.max(1, this.party.length)) - 1);
      const rnd = new CM.Random(CM.hashSeed(`${this.seed}:tavern:${this.floor.number}`));
      this.recruits = { floor: this.floor.number, who: [0, 1, 2].map(() => CM.makeRecruit(level, rnd)) };
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
    this.gold -= recruit.price;
    const rescued = (this.rescued || []).length;
    const gone = this.party[idx];
    for (const slot of CM.SLOTS) if (gone[slot] && !(slot === "weapon" || slot === "armor")) this.bag.push(gone[slot]);   // (their trinkets stay with the party)
    const h = Object.assign({}, recruit);
    delete h.price;
    this.party[idx] = h;
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
    if (this.mode !== "camp") return "The smith works at the camp.";
    const hero = this.party[heroIndex], item = hero && hero[slot];
    if (!item || !["weapon", "armor", "offhand", "helm"].includes(slot)) return "Pick a weapon, armour, a shield or a helm.";
    if (item.unknown) return "The smith won't work on a thing nobody can name. Have it identified first.";
    const p = item.props = item.props || {};
    if (service === "enchant") {
      const n = p.enchant || 0, cost = CM.SMITH.enchant * (n + 1), gem = this.bag.findIndex((i) => i.kind === "gem" && i.gem === "diamond");
      if (n >= CM.SMITH.most) return `${item.name} has had all the smith's work it can take.`;
      if (gem < 0) return "The smith wants a diamond for the work.";
      if (this.gold < cost) return `The smith wants ${cost} gold, and the diamond.`;
      this.gold -= cost;
      this.bag.splice(gem, 1);
      p.enchant = n + 1;
      p.bonus = (p.bonus || 0) + 1;
      item.power += 1;
      item.value += 60;
      item.name = `${p.element ? CM.ELEMENTS[p.element].prefix + " " : ""}${CM.baseName(item)} +${p.bonus}`;
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
      this.gold -= CM.SMITH.gem;
      this.bag.splice(gem, 1);
      p.element = el;
      item.value += 80;
      item.name = `${CM.ELEMENTS[el].prefix} ${CM.baseName(item)}${p.bonus ? ` +${p.bonus}` : ""}`;
      this.sound("lever");
      this.say(`The smith sets the ${name.toLowerCase()} into ${hero.name}'s blade, and it takes: ${item.name}.`);
    } else return "The smith doesn't do that.";
    this.saveRun();
    this.emit("change");
    return "";
  },

  // the vault: one thing left at the camp waits for the next party (saved between runs); what was there comes out
  leaveHeirloom(row) {
    if (this.mode !== "camp") return "The vault is at the camp.";
    const item = this.bag[row];
    if (!item) return "Pick something from your pack.";
    if (["key", "bones", "rope", "torch"].includes(item.kind)) return "The merchant won't keep that. Something worth the keeping.";
    const old = this.vault;
    this.bag.splice(row, 1);
    this.vault = item;
    CM.store.set("vault", item);
    if (old) this.bag.push(old);
    this.sound("chest");
    this.say(`The merchant locks ${item.name} in the vault for whoever comes after${old ? `, and hands back ${old.name}` : ""}.`);
    this.saveRun();
    this.emit("change");
    return "";
  },
  takeHeirloom() {
    if (this.mode !== "camp") return "The vault is at the camp.";
    if (!this.vault) return "The vault is empty.";
    const item = this.vault;
    this.vault = null;
    CM.store.remove("vault");
    this.bag.push(item);
    this.sound("chest");
    this.say(`The merchant unlocks the vault: ${item.name}, left by a party before you.`);
    this.saveRun();
    this.emit("change");
    return "";
  },

  raiseDead() {
    const fallen = this.party.filter((m) => m.hp <= 0);
    if (!fallen.length) { this.say("No one needs raising."); return; }
    const hero = fallen[0], cost = 100 * hero.level;
    if (this.gold < cost) { this.say(`The old priest asks ${cost} gold to raise the ${hero.cls}.`); return; }
    this.gold -= cost;
    hero.hp = hero.max;
    this.sound("heal");
    this.say(`For ${cost} gold, the priest raises the ${hero.cls}!`);
    this.saveRun();
  },

  leaveCamp() {
    this.stock = null;
    this.enterFloor(this.floor.number + 1, "down");
  },

  backUp() {                                                             // from the camp, back onto the floor above it
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
