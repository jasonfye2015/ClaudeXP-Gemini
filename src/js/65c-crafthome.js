"use strict";
// The island and home (the nineteenth update, phase 4 - v12.4). What comes home through the Neather Gate is the main
// game's own: ore chunks, bars and charcoal into the bag for the Smith (61k-gate.js), meat for the cook, the island's
// gold into the purse and its finds into the bag (64o-craftlife.js). What stays is the island's: blocks, its tools,
// torches - in the hero's satchel for the next visit. The satchel's building stuff has a use at home too: the merchant
// buys timber and stone by the stack, and the Guildhall's builders take blocks towards the village's next build (the
// village builds with renown, so a hundred blocks count as ten renown off it). Into the island the party's bag goes
// with the hero: their picks and lantern work there, a healing potion is drunk (Q), and a ration or the island's meat
// is eaten (G) for a little mending.
CM.CH = { stack: 16, stackGold: 1, builderBlocks: 100, builderRenown: 10, ration: 0.15, meat: 0.08 };
CM.CC.TIMBER = new Set([CM.CC.B.LOG, CM.CC.B.PLANKS]);
CM.CC.STONEWORK = new Set([CM.CC.B.STONE, CM.CC.B.COBBLE, CM.CC.B.BRICK]);
CM.CC.BUILDING = new Set([1, 2, 3, 4, 5, 7, 8, 10, 11, 13, 14]);           // (plain building blocks the builders take)

Object.assign(CM.Game.prototype, {
  // what the heroes' satchels hold of a kind of block (the satchels come home with their heroes)
  islandStock(set) { const K = this.craftStore(); let n = 0; for (const S of Object.values(K.satchels)) for (const s of S || []) if (s && set.has(s.b)) n += s.n; return n; },
  islandTake(set, n) {
    const K = this.craftStore();
    for (const key of Object.keys(K.satchels)) { const S = K.satchels[key] || []; for (let i = S.length - 1; i >= 0 && n > 0; i--) { const s = S[i]; if (!s || !set.has(s.b)) continue; const k = Math.min(n, s.n); s.n -= k; n -= k; if (!s.n) S[i] = null; } }
    this.saveVillage && this.saveVillage(); return n === 0;
  },
  // the merchant: timber and stone by the stack of sixteen
  islandSellable() { const both = new Set([...CM.CC.TIMBER, ...CM.CC.STONEWORK]), n = this.islandStock(both), stacks = Math.floor(n / CM.CH.stack); return { n, stacks, gold: stacks * CM.CH.stackGold, set: both }; },
  sellIslandStone() {
    const o = this.islandSellable(); if (!o.stacks) return `The merchant buys island timber and stone by the stack of ${CM.CH.stack}; the satchels hold ${o.n}.`;
    this.islandTake(o.set, o.stacks * CM.CH.stack); this.gold += o.gold; this.tally.islandSold = (this.tally.islandSold || 0) + o.stacks;
    this.emit("change"); return `The merchant takes ${o.stacks * CM.CH.stack} blocks of island timber and stone for ${o.gold} gold. "Good square stuff. Odd, but good."`;
  },
  // the Guildhall's builders: every hundred blocks are ten renown off the next build
  builderCredit() { return (this.village && this.village.buildCredit) || 0; },
  giveBuilders() {
    const n = this.islandStock(CM.CC.BUILDING), lots = Math.floor(n / CM.CH.builderBlocks);
    if (!lots) return `The builders take island blocks a hundred at a time; the satchels hold ${n}.`;
    this.islandTake(CM.CC.BUILDING, lots * CM.CH.builderBlocks); this.village.buildCredit = this.builderCredit() + lots * CM.CH.builderRenown; this.saveVillage();
    this.emit("change"); return `The builders cart off ${lots * CM.CH.builderBlocks} blocks from the island: ${lots * CM.CH.builderRenown} renown off the village's next build (${this.village.buildCredit} in hand).`;
  },
  // on the island: a healing potion from the bag (the smallest that will do), or a mana potion for a caster at full health
  craftDrink() {
    const cr = this.craft; if (!cr) return ""; const h = cr.hero, lack = h.max - h.hp;
    const heals = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "heal" || it.kind === "greaterheal").sort((a, b) => (a[0].power || 0) - (b[0].power || 0));
    if (lack > 0 && heals.length) { const [it, i] = heals.find(([x]) => (x.power || 0) >= lack) || heals[heals.length - 1]; this.bag.splice(i, 1); const got = Math.min(lack, it.power || 0); h.hp += got; this.craftSay(`${h.name} drinks a ${it.name.toLowerCase()}: +${got}.`); (this.craftLife().events = this.craftLife().events || []).push({ kind: "drink" }); return "heal"; }
    const mana = this.bag.findIndex((it) => it.kind === "mana");
    if (h.maxmp && h.mp < h.maxmp && mana >= 0) { const it = this.bag.splice(mana, 1)[0], got = Math.min(h.maxmp - h.mp, it.power || 0); h.mp += got; this.craftSay(`${h.name} drinks a mana potion: +${got} magic.`); (this.craftLife().events = this.craftLife().events || []).push({ kind: "drink" }); return "mana"; }
    this.craftSay(lack > 0 ? "No healing potion in the bag." : `${h.name} is not hurt.`); return "";
  },
  // a ration from the bag, or the island's own meat from the satchel: a little mending
  craftEat() {
    const cr = this.craft; if (!cr) return ""; const h = cr.hero; if (h.hp >= h.max) { this.craftSay(`${h.name} is not hungry enough to eat now.`); return ""; }
    const r = this.bag.findIndex((it) => it.kind === "ration");
    if (r >= 0) { this.bag.splice(r, 1); const got = Math.min(h.max - h.hp, Math.max(1, Math.round(h.max * CM.CH.ration))); h.hp += got; this.craftSay(`${h.name} eats a ration: +${got}.`); return "ration"; }
    const S = cr.satchel, slot = S.slots.findIndex((s) => s && CM.CC.ITEM[s.b] && CM.CC.ITEM[s.b].meat);
    if (slot >= 0) { const b = S.slots[slot].b; S.take(slot); const got = Math.min(h.max - h.hp, Math.max(1, Math.round(h.max * CM.CH.meat))); h.hp += got; this.craftSay(`${h.name} roasts a little ${CM.CC.NAMES[b].toLowerCase()} over a torch and eats it: +${got}.`); return "meat"; }
    this.craftSay("Nothing to eat: a ration from the bag, or meat from the island's deer and boar."); return "";
  },
});
// (v12.5) at the Smith: three like gems from the island (the main game's own) set in a ring or an amulet
CM.GEM_JEWEL = { ruby: 14, sapphire: 14, sunstone: 16, diamond: 24 };
Object.assign(CM.Game.prototype, {
  setGems(gem, slot) {
    const rows = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "gem" && it.gem === gem);
    if (rows.length < 3) return `Three like gems for a ${slot}: the bag has ${rows.length} ${gem}.`;
    if (!["ring", "amulet"].includes(slot)) return "A ring or an amulet.";
    for (const [, i] of rows.slice(0, 3).reverse()) this.bag.splice(i, 1);
    const depth = CM.GEM_JEWEL[gem] || 14, R = new CM.Random(CM.hashSeed(`${this.seed}:gemjewel:${(this.tally.gemJewels || 0)}:${gem}`)); let it = CM.makeItem(depth, R, slot); if (CM.affix) it = CM.affix(it, depth + 2, R) || it; it.unknown = false;
    this.tally.gemJewels = (this.tally.gemJewels || 0) + 1; this.gain([it], "smith"); this.emit("change");
    return `The Smith sets three ${CM.GEMS[gem].name.toLowerCase()}s in ${/^[aeiou]/i.test(it.name) ? "an" : "a"} ${it.name}.`;
  },
});
// the village's builds take the builders' credit first
{ const build0 = CM.Game.prototype.build, renown0 = CM.Game.prototype.renown;
  CM.Game.prototype.build = function (id) {
    const credit = this.builderCredit(); if (!credit) return build0.call(this, id);
    const B = CM.VILLAGE[id], lvl = this.villageLevel(id); if (!B || lvl >= B.costs.length) return build0.call(this, id);
    const cost = B.costs[lvl], used = Math.min(credit, cost);
    this.village.spent = (this.village.spent || 0) - used; const why = build0.call(this, id);   // (the credit stands in for that much renown)
    if (why) { this.village.spent += used; return why; }
    this.village.buildCredit = credit - used; this.saveVillage(); return "";
  };
  void renown0; }
