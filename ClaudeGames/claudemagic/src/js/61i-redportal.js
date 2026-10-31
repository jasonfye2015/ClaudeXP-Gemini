"use strict";
// The red portal (the sixteenth update): in the Keep-yard, a portal the colour of embers, to Haven - Claudeablo's town
// (64l-claudeablo.js). Any one of the party goes through, as a warrior, rogue or sorcerer by their calling, and the
// character they are there is kept with the village (one for each hero: their level, gear, spells and deepest level).
// Haven has a red portal of its own, south of the well: back through it, and
//   - experience earned there is the hero's (a share of it, as the Mage Tower's is),
//   - the gold found there is the party's (what they had in Haven when they arrived stays as their purse there),
//   - every piece of gear in the pack (not what is worn) comes home as a thing of the party's own,
// and what is worn, the potions, scrolls and books stay there for the next time. A death there is Claudeablo's: wake in
// Haven with half the gold.
CM.PORTAL_YARD.ablo = [35, 18];                                           // the red portal, at the yard's north side
CM.ABLO = { xpShare: 0.3 };
CM.abloKey = (h) => `${h.name}:${h.cls}`;
CM.abloClass = (h) => (["Knight", "Paladin", "Monk"].includes(h.cls) ? "warrior" : ["Rogue", "Ranger", "Bard"].includes(h.cls) ? "rogue" : "sorcerer");
// a thing from Claudeablo, as one of the party's own: the same slot, its depth from the item's level, its name kept
CM.abloToItem = function (it, seed) {
  const AB = CM.AB, slot = AB.slot(it); if (!slot) return null;
  const rnd = new CM.Random(CM.hashSeed(`${seed}:${JSON.stringify(it)}`)), depth = Math.max(1, Math.min(CM.BOTTOM || 50, it.ilvl));
  const kind = { weapon: "weapon", armor: "armor", helm: "helm", shield: "shield", ring: "ring", amulet: "amulet" }[slot];
  let item = CM.makeItem(depth, rnd, kind);
  if (["weapon", "armor", "helm", "shield"].includes(kind)) { if (it.rarity === "magic" || it.rarity === "rare") item = CM.affix(item, Math.max(8, depth + (it.rarity === "rare" ? 6 : 2)), rnd); }
  item.unknown = false; it.ident = true; item.name = AB.name(it); item.props = Object.assign({}, item.props || {}, { from: "Claudeablo" });
  return item;
};
Object.assign(CM.Game.prototype, {
  abloStore() { this.village = this.village || {}; const A = this.village.ablo = this.village.ablo || {}; A.heroes = A.heroes || {}; A.seed = A.seed || CM.hashSeed(`${this.seed}:claudeablo`) % 1000000; A.visits = A.visits || 0; return A; },
  // through the red portal: the hero's character there, made on the first visit at the hero's own level
  enterClaudeablo(i) {
    const h = this.party[i]; if (!h) return "No one.";
    if (h.hp <= 0) return `${h.name} has fallen.`;
    if (this.mode !== "explore" || !this.floor || this.floor.number !== 0) return "The red portal is in the Keep-yard.";
    const A = this.abloStore(), key = CM.abloKey(h); let pl;
    if (A.heroes[key]) pl = CM.AB.Player.fromJSON(A.heroes[key]);
    else {
      pl = new CM.AB.Player(CM.abloClass(h), h.name);
      const stat = { warrior: ["str", "vit"], rogue: ["dex", "vit"], sorcerer: ["mag", "vit"] }[pl.cls];
      for (let L = 1; L < h.level; L++) { pl.level += 1; pl.base[stat[0]] += 3; pl.base[stat[1]] += 2; }   // (they arrive as strong as they are here)
      pl.recalc(); pl.hp = pl.maxhp; pl.mana = pl.maxmana;
    }
    A.visits += 1;
    this.logAct && this.logAct("enterClaudeablo", i);
    this.abloHero = i; this.abloWorld = new CM.AB.World(A.seed, pl); this.abloWorld.enter(0, "home"); this.abloWorld.xpGained = 0; this.abloWorld.goldIn = pl.gold;
    this.abloWorld.say(`${h.name} steps out of the red portal into Haven. The cathedral's door waits at the end of the path.`, "#FF9090");
    this.say(`${h.name} steps into the red portal, and is gone.`);
    this.setMode("ablo"); this.emit("ablo", this.abloWorld);
    return "";
  },
  abloKeep() { const w = this.abloWorld; if (!w) return; const h = this.party[this.abloHero]; this.abloStore().heroes[CM.abloKey(h)] = w.player.toJSON(); this.saveVillage && this.saveVillage(); },
  // back through Haven's red portal: the experience, the gold, and the pack's gear come home
  leaveClaudeablo() {
    const w = this.abloWorld; if (!w) return null;
    const h = this.party[this.abloHero], pl = w.player, A = this.abloStore();
    const xp = Math.round((w.xpGained || 0) * CM.ABLO.xpShare); if (xp) { h.xp += xp; this.checkLevels(); }
    const float = Math.min(pl.gold, w.goldIn || 0), gold = pl.gold - float; this.gold += gold; pl.gold = float;   // (what they had in Haven when they came stays there: only the gold found comes home)
    const things = [];
    pl.inv.forEach((it, k) => { if (it && CM.AB.slot(it)) { const item = CM.abloToItem(it, `${A.seed}:${A.visits}:${k}`); if (item) { things.push(item); pl.inv[k] = null; } } });
    if (things.length) this.gain(things, "claudeablo");
    this.tally.abloVisits = (this.tally.abloVisits || 0) + 1; this.tally.abloDeepest = Math.max(this.tally.abloDeepest || 0, pl.maxDepth);
    if (w.flags.diablo_dead) this.achieve && this.achieve("undying");
    A.heroes[CM.abloKey(h)] = pl.toJSON(); this.saveVillage && this.saveVillage();
    this.say(`${h.name} steps back out of the red portal into the Keep-yard.`);
    const bits = [xp ? `${xp} experience` : "", gold ? `${gold} gold` : "", things.length ? things.map((t) => t.name).join(", ") : ""].filter(Boolean);
    if (bits.length) this.say(`From Haven: ${bits.join("; ")}.`);
    this.abloWorld = null; this.abloHero = null;
    this.setMode("explore"); this.floor.pos = CM.PORTAL_YARD.ablo.slice(); this.floor.pos[1] += 1; this.floor.facing = 2;
    this.saveRun(); this.emit("floor", this.floor);
    return { xp, gold, things };
  },
});
