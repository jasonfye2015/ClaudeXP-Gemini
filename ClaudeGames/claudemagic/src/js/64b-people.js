"use strict";
// The people's part (the eleventh update, phase 5): a fifth place behind the heroes for one follower, and the
// townsfolk's errands.
//
// A follower (this.follower) is not a hero: no level, no gear, no turn in a fight. Each has a trade that acts by
// itself (CM.FOLLOWERS). It can be struck - a blow that misses a hero in the back row may catch it instead - and it can
// die: a line in the log, its remains on the floor, a name on the memorial, and the tavern will not hire to this party
// for the rest of the run. It mends between floors. One at a time; let go at any time (no gold back).
//
// Errands (CM.ERRANDS) are asked by six of the townsfolk, kept between runs in the village store (village.errands):
// three taken at a time, one from each giver a season. A fetch errand lays its thing on its floor (the floor is the
// giver's and the season's, by hash) the first time the party is on that floor after taking it; read and slay errands
// look at what the party did after taking them. Handed in in the town (the Journal's Errands page), each pays in the
// giver's own coin: gold, renown, a thing, and a lasting favour (village.perks).
CM.FOLLOWERS = {
  porter: { name: "porter", hire: "tavern", price: 30, hp: 22, what: "carries forty more", carry: 40 },
  torchbearer: { name: "torchbearer", hire: "tavern", price: 20, hp: 14, what: "the light burns at half the rate, and is seen a square further" },
  dog: { name: "dog", hire: "farm", price: 0, hp: 18, what: "smells an ambush before it comes; will not go below the tenth floor", deepest: 10 },
  wizard: { name: "hedge-wizard", hire: "library", price: 40, hp: 12, what: "a Light on each new floor, and a Mend after a fight once a floor", library: 3 },
  adventurer: { name: "rescued adventurer", hire: "rescue", price: 0, hp: 24, what: "picks the first lock of each floor; tells her story over three floors, then goes her way with a gift" },
};
CM.FOLLOWER_NAMES = { porter: ["Brannoc", "Hew", "Old Sef", "Marra"], torchbearer: ["Lin", "Tam", "Wren", "Pip"], dog: ["Grip"], wizard: ["Mother Ysolde", "Cadoc", "Aunt Breda"], adventurer: ["the one you cut loose"] };
CM.FOLLOWER_STORY = [
  "\"I came down with three others,\" she says, on the stair. \"The Guild said floor four was clear. The Guild says a lot of things.\"",
  "\"They didn't kill me,\" she says, picking at a knot in the dark. \"They argued about whether I'd fetch more alive. I fetched nothing. I waited.\"",
  "\"I'll go my own way from the next camp,\" she says. \"Not ungrateful - just done with the dark for a while. Here. You'll get more use from it than me.\"",
];
CM.ERRANDS = {
  tavern: { giver: "the tavern-keeper", building: "tavern", kind: "fetch", floors: [3, 8], thing: "a tarnished ring",
    ask: "\"My brother went down the shaft with a ring of mine on his finger and didn't come up. Floor {n}, they said. Bring the ring home.\"",
    done: "\"That's his.\" She turns it over twice. \"The round's half price for you from now on, and that's for good.\"", reward: { gold: 60, renown: 12, perk: "tavern" } },
  merchant: { giver: "the merchant", building: "merchant", kind: "fetch", floors: [5, 12], thing: "the merchant's sealed crate",
    ask: "\"A crate of mine went down the shaft with a fool who thought he'd sell it below. Floor {n}. My seal's on it.\"",
    done: "\"Seal unbroken. Well.\" He makes a note in a book. \"A tenth off at my counter, from now on.\"", reward: { gold: 120, renown: 12, perk: "merchant" } },
  smith: { giver: "the smith", building: "smith", kind: "bring", ore: "iron", n: 4,
    ask: "\"Bring me four lumps of iron ore - good ore, from the caves or below - and I'll make something of them for you.\"",
    done: "\"Good iron.\" The forge roars. \"There. A blade with a bit of the hill in it.\"", reward: { gold: 0, renown: 10, thing: "blade" } },
  library: { giver: "the librarian", building: "library", kind: "read", floors: [4, 14],
    ask: "\"The carving on floor {n} - read it, and tell me what it says. Word for word, if you can.\"",
    done: "\"So that's what it says.\" The librarian writes it down, slowly. \"Take this. It was gathering dust.\"", reward: { gold: 30, renown: 15, thing: "tome" } },
  temple: { giver: "the priest", building: "temple", kind: "champion",
    ask: "\"There are champions leading the packs below the sixth floor, and the dead lie badly while they walk. Put one down.\"",
    done: "\"One less.\" The priest lights a candle for it anyway. \"These are blessed. Carry them.\"", reward: { gold: 40, renown: 15, thing: "potions" } },
  farm: { giver: "the farmer's hand", building: "garden", kind: "fetch", floors: [2, 6], thing: "an old sickle",
    ask: "\"My grandad's sickle went down the shaft the year the dead came up. Floor {n}, he always said. Silly to want it back. I want it back.\"",
    done: "\"That's it, that's the one.\" He holds it like a baby. \"The dog's taken to you, too - he'll come along, if you'll have him.\"", reward: { gold: 25, renown: 10, perk: "dog" } },
};
CM.ERRANDS_MOST = 3;
CM.errandSeason = (d) => { d = d || new Date(); return `${d.getFullYear()}-${CM.seasonOfDate(d)}`; };   // (one from each giver a season)
CM.errandFloor = (giver, season) => { const E = CM.ERRANDS[giver]; if (!E.floors) return null; const [a, b] = E.floors; return a + (CM.hashSeed(`errand:${giver}:${season}`) % (b - a + 1)); };

Object.assign(CM.Game.prototype, {
  // ---- the follower ----
  followerIs(id) { const f = this.follower; return Boolean(f && f.id === id && !f.away && f.hp > 0); },
  followerCarry() { return this.followerIs("porter") ? CM.FOLLOWERS.porter.carry : 0; },
  followerName() { const f = this.follower; return f ? `${f.name} the ${CM.FOLLOWERS[f.id].name}` : ""; },
  canHire(id) {
    const F = CM.FOLLOWERS[id];
    if (!F) return "No one by that trade.";
    if (this.follower) return `${this.followerName()} is with you already; one follower at a time.`;
    if (F.hire === "tavern" && this.tavernBarred) return "The tavern won't hire to you again this run. Not after the last one.";
    if (F.hire === "library" && this.villageLevel("library") < F.library) return `The library has no one to spare until it has grown (level ${F.library}).`;
    if (F.hire === "farm" && !(this.villageLevel("farm") >= 5 || ((this.village || {}).perks || {}).dog)) return "The farm has no dog to spare yet: when there's a cow to mind, there's a dog.";
    if (this.gold < F.price) return `A ${F.name} wants ${F.price} gold for the run.`;
    return "";
  },
  hireFollower(id) {
    const no = this.canHire(id);
    if (no) return no;
    this.logAct("hireFollower", id);
    const F = CM.FOLLOWERS[id], names = CM.FOLLOWER_NAMES[id];
    this.gold -= F.price; if (F.price) this.spend(F.hire, F.price);
    this.follower = { id, name: names[CM.hashSeed(`${this.seed}:follower:${id}:${this.tally.steps || 0}`) % names.length], hp: F.hp, max: F.hp, floors: 0 };
    this.say(`${this.followerName()} falls in behind the party: ${F.what}.`);
    this.emit("change");
    return "";
  },
  dismissFollower() {
    if (!this.follower) return false;
    this.logAct("dismissFollower");
    this.say(`${this.followerName()} goes back the way you came.`);
    this.follower = null; this.emit("change");
    return true;
  },
  // a floor: the follower mends; the dog stops at the tenth; the hedge-wizard lights the way; the adventurer tells her story
  followerOnFloor(number, fresh) {
    const f = this.follower;
    if (!f) return;
    f.hp = f.max;
    if (f.id === "dog") { const away = number > CM.FOLLOWERS.dog.deepest; if (away && !f.away) this.say(`${f.name} stops at the top of the stair below the tenth floor, and won't come on. He'll be waiting up there.`); if (!away && f.away) this.say(`${f.name} comes bounding back.`); f.away = away; }
    if (f.id === "wizard" && CM.isDeep(number) && fresh && (this.spellLight || 0) < 20) { this.spellLight = 60; this.say(`${f.name} says a word, and a cold light gathers over the party.`); }
    if (f.id === "adventurer" && number >= 1 && fresh) { f.floors = (f.floors || 0) + 1; const line = CM.FOLLOWER_STORY[f.floors - 1]; if (line) this.say(line); if (f.floors >= CM.FOLLOWER_STORY.length) f.leaving = true; }
    f.mended = null; f.picked = null;
  },
  // at a camp, the adventurer goes her way with a gift
  followerAtCamp() {
    const f = this.follower;
    if (!f || f.id !== "adventurer" || !f.leaving) return;
    const rnd = new CM.Random(CM.hashSeed(`${this.seed}:gift:${this.floor.number}`)), gift = CM.affix(CM.makeItem(this.floor.number + 3, rnd, rnd.pick(["weapon", "armor", "ring", "amulet"])), this.floor.number + 6, rnd);
    gift.unknown = false; this.bag.push(gift);
    this.say(`${f.name} shoulders a pack at the camp and goes her own way, up. She leaves you ${gift.name} (${CM.itemLabel(gift)}).`);
    this.village = this.village || {}; this.village.followerTales = (this.village.followerTales || []).concat({ name: f.name, floor: this.floor.number, date: new Date().toLocaleDateString() }).slice(-12); if (this.saveVillage) this.saveVillage();
    this.follower = null;
  },
  // after a fight: the hedge-wizard's Mend, once a floor
  followerAfterFight() {
    const f = this.follower;
    if (!this.followerIs("wizard") || f.mended === this.floor.number) return;
    const hurt = this.alive().filter((h) => h.hp < h.max * 0.7).sort((a, b) => a.hp / a.max - b.hp / b.max)[0];
    if (!hurt) return;
    const back = Math.max(4, Math.ceil(hurt.max / 4)); hurt.hp = Math.min(hurt.max, hurt.hp + back); f.mended = this.floor.number;
    this.say(`${f.name} lays a hand on ${hurt.name}: +${back}.`);
  },
  // a blow that misses a hero in the back row may catch the follower behind instead
  followerTakes(m) {
    const f = this.follower;
    if (!f || f.away || f.hp <= 0 || !this.rnd.chance(0.25)) return false;
    const dmg = Math.max(1, this.damage(Math.floor(m.atk / 2), 0, 1));
    f.hp -= dmg;
    this.say(`${CM.The(m)}'s blow goes past, and catches ${this.followerName()} (-${dmg}).`);
    if (f.hp <= 0) this.followerDies(m);
    return true;
  },
  followerDies(m) {
    const f = this.follower;
    this.say(`${this.followerName()} falls, and doesn't get up. You hadn't known them long.`);
    this.trace("bones", ...this.floor.pos);
    this.memorial = (this.memorial || []).concat({ name: f.name, cls: CM.FOLLOWERS[f.id].name, floor: this.floor.number, date: new Date().toLocaleDateString(), follower: true });
    if (CM.FOLLOWERS[f.id].hire === "tavern") this.tavernBarred = true;
    this.tally.followersLost = (this.tally.followersLost || 0) + 1;
    this.follower = null;
    this.cheer(-1);
  },

  // ---- errands ----
  errands() { this.village = this.village || {}; const E = this.village.errands = this.village.errands || { taken: {}, done: {} }; E.taken = E.taken || {}; E.done = E.done || {}; return E; },
  errandOffered(giver) {
    const E = this.errands(), season = CM.errandSeason();
    return Boolean(CM.ERRANDS[giver]) && !E.taken[giver] && E.done[giver] !== season && Object.keys(E.taken).length < CM.ERRANDS_MOST;
  },
  takeErrand(giver) {
    if (!this.errandOffered(giver)) return "That errand isn't to be had just now.";
    this.logAct("takeErrand", giver);
    const E = this.errands(), season = CM.errandSeason(), R = CM.ERRANDS[giver];
    E.taken[giver] = { season, floor: CM.errandFloor(giver, season), from: { champions: this.tally.champions || 0 }, found: false };
    if (this.saveVillage) this.saveVillage();
    this.say(`${R.giver.charAt(0).toUpperCase() + R.giver.slice(1)}: ${this.errandAsk(giver)}`);
    if (this.floor && this.floor.number === E.taken[giver].floor) this.layErrand(this.floor);
    this.emit("change");
    return "";
  },
  errandAsk(giver) { const t = this.errands().taken[giver], R = CM.ERRANDS[giver]; return R.ask.replace("{n}", t ? t.floor : CM.errandFloor(giver, CM.errandSeason())); },
  // what is left to do: "" when it can be handed in
  errandLeft(giver) {
    const t = this.errands().taken[giver], R = CM.ERRANDS[giver];
    if (!t) return "not taken";
    if (R.kind === "fetch") return this.bag.some((i) => i.kind === "errand" && i.giver === giver) ? "" : `${R.thing}, on floor ${t.floor}`;
    if (R.kind === "bring") { const have = this.bag.filter((i) => i.kind === "ore" && i.ore === R.ore).length; return have >= R.n ? "" : `${have} of ${R.n} ${CM.ORES[R.ore].name} ore`; }
    if (R.kind === "read") return t.read ? "" : `the carving on floor ${t.floor}`;
    if (R.kind === "champion") return (this.tally.champions || 0) > ((t.from || {}).champions || 0) || t.slain ? "" : "a champion, slain below the sixth floor";
    return "?";
  },
  handInErrand(giver) {
    const t = this.errands().taken[giver], R = CM.ERRANDS[giver];
    if (!t) return "No such errand.";
    if (!this.floor || this.floor.number !== 0) return `${R.giver.charAt(0).toUpperCase() + R.giver.slice(1)} is in the town.`;
    const left = this.errandLeft(giver);
    if (left) return `Still to do: ${left}.`;
    this.logAct("handInErrand", giver);
    if (R.kind === "fetch") { const i = this.bag.findIndex((it) => it.kind === "errand" && it.giver === giver); if (i >= 0) this.bag.splice(i, 1); }
    if (R.kind === "bring") for (let n = 0; n < R.n; n++) { const i = this.bag.findIndex((it) => it.kind === "ore" && it.ore === R.ore); if (i >= 0) this.bag.splice(i, 1); }
    const rw = R.reward, E = this.errands(), rnd = new CM.Random(CM.hashSeed(`${this.seed}:errand:${giver}:${t.season}`));
    if (rw.gold) { this.gold += rw.gold; }
    if (rw.renown) { this.village.renown = (this.village.renown || 0) + rw.renown; }
    if (rw.perk) { this.village.perks = this.village.perks || {}; this.village.perks[rw.perk] = true; }
    let thing = null;
    if (rw.thing === "blade") thing = CM.affix(CM.makeItem(Math.max(4, (this.camps || []).length * 3 + 4), rnd, "weapon"), 12, rnd);
    else if (rw.thing === "tome" && CM.TOMES) { const ids = Object.keys(CM.TOMES); thing = CM.tome(ids[rnd.int(0, ids.length - 1)]); }
    else if (rw.thing === "potions") { const depth = Math.max(5, ...(this.trail || []).map((x) => x[0] || 0)); for (let i = 0; i < 2; i++) this.bag.push({ name: "Blessed Greater Healing Potion", kind: "greaterheal", power: 2 * (20 + depth * 3), value: 70 }); }
    if (thing) { thing.unknown = false; this.bag.push(thing); }
    delete E.taken[giver]; E.done[giver] = t.season;
    this.tally.errands = (this.tally.errands || 0) + 1;
    if (this.saveVillage) this.saveVillage();
    this.journal = (this.journal || []).concat({ kind: "errand", floor: 0, who: R.giver, text: R.done });
    this.say(`${R.giver.charAt(0).toUpperCase() + R.giver.slice(1)}: ${R.done}${rw.gold ? ` (+${rw.gold} gold` : " ("}${rw.renown ? `${rw.gold ? ", " : ""}+${rw.renown} renown` : ""})${thing ? ` - ${thing.name}` : ""}`);
    this.emit("change");
    return "";
  },
  // a fetch errand's thing, laid on its floor the first time the party is there after taking it
  layErrand(fl) {
    const E = this.errands();
    for (const [giver, t] of Object.entries(E.taken)) {
      const R = CM.ERRANDS[giver];
      if (R.kind !== "fetch" || t.floor !== fl.number || this.bag.some((i) => i.kind === "errand" && i.giver === giver) || Object.values(fl.things).some((x) => x.type === "errand" && x.giver === giver)) continue;
      const reach = CM.reachable(fl), cells = [...reach].filter((k) => !fl.things[k] && !fl.features[k] && k !== `${fl.pos[0]},${fl.pos[1]}`).sort();
      if (!cells.length) continue;
      const k = cells[CM.hashSeed(`${this.seed}:errandat:${giver}:${fl.number}`) % cells.length];
      fl.things[k] = { type: "errand", giver };
      this.dirty = true;
    }
  },
  pickUpErrand(thing, k) {
    const R = CM.ERRANDS[thing.giver];
    this.bag.push({ name: R.thing.charAt(0).toUpperCase() + R.thing.slice(1), kind: "errand", giver: thing.giver, weight: 1, value: 0 });
    delete this.floor.things[k];
    this.sound("chest");
    this.say(`${R.thing.charAt(0).toUpperCase() + R.thing.slice(1)}: ${R.giver}'s errand. Into the pack, carefully.`);
    this.emit("change");
  },
  // a carving read: the librarian's errand, if it was this floor's
  errandRead(floorNumber) { const t = this.errands().taken.library; if (t && t.floor === floorNumber && !t.read) { t.read = true; if (this.saveVillage) this.saveVillage(); this.say("Word for word: the librarian will want this."); } },
});
