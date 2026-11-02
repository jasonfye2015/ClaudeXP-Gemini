"use strict";
// The house furnished (v32.3, UPGRADE_PLAN_27.md): furnishings bought for the party's house with gold - each a small
// good that every run setting out from it carries - and the guardians' trophies mounted on the trophy wall, as many as
// the house has levels: each mounted trophy gives every hero who sets out +1 to its guardian's stat. Kept in the
// village; the house's trophy wall (its second level) is where they hang.
//   CM.FURNISH[id] -> {name, gold, what};  CM.TROPHY_GIFT[guardian] -> stat
//   game.furnished(); game.buyFurnish(id); game.mounted(); game.mountTrophy(id) / unmountTrophy(id); game.homeGifts()
{ const FN = CM.FURNISH = {
    rug: { name: "A hearth rug", gold: 120, what: "the party sets out in good heart (+8 morale)" },
    pantry: { name: "A pantry shelf", gold: 140, what: "two rations more in the pack at the start" },
    lamp: { name: "A brass lamp", gold: 150, what: "the first torch is trimmed to last a hundred steps longer" },
    strongbox: { name: "A strongbox", gold: 180, what: "sixty gold more at the start" },
    bookcase: { name: "A bookcase", gold: 220, what: "+1 Intelligence for every hero" },
    shrine: { name: "A shrine nook", gold: 220, what: "+1 Wisdom for every hero" },
    rack: { name: "A weapon rack", gold: 260, what: "+1 Strength for every hero" },
    stand: { name: "An armour stand", gold: 260, what: "+1 Constitution for every hero" },
  };
  CM.TROPHY_GIFT = { rat: "luck", knight: "con", forge: "str", queen: "dex", mind: "int", tyrant: "str", master: "dex", patriarch: "wis", root: "con" };
  const G = CM.Game.prototype;
  Object.assign(G, {
    furnished() { return this.vext("furnish"); },
    mounted() { const M = this.vext("mounted"); M.list = M.list || []; return M.list; },
    furnishWhy(id) { if (!FN[id]) return "No such thing."; if (!this.inTown()) return "Furnishings are bought for the house, in town."; if (this.homeLevel() < 1) return "The house has no roof yet.";
      if (this.furnished()[id]) return "The house has it already."; if (this.gold < FN[id].gold) return `${FN[id].gold} gold.`; return ""; },
    buyFurnish(id) { const why = this.furnishWhy(id); if (why) return why; this.logAct && this.logAct("buyFurnish", id); this.gold -= FN[id].gold; this.spend && this.spend("home", FN[id].gold);
      this.furnished()[id] = { day: CM.dayOf ? CM.dayOf(this) : 0 }; this.saveVillage(); this.sound && this.sound("coin"); this.say(`${FN[id].name} for the house: ${FN[id].what}, every run from now.`);
      if (Object.keys(FN).every((k) => this.furnished()[k]) && this.achieve) this.achieve("furnished"); this.saveRun(); this.emit("change"); return ""; },
    mountRoom() { return Math.max(0, this.homeLevel() - 1) * 2; },
    mountWhy(id) { if (!this.inTown()) return "The trophy wall is at home."; if (this.homeLevel() < 2) return "The house has no trophy wall yet."; if (!(this.trophies || {})[id] || !CM.TROPHY_GIFT[id]) return "That trophy hasn't been won.";
      if (this.mounted().includes(id)) return "It hangs there already."; if (this.mounted().length >= this.mountRoom()) return `The wall has room for ${this.mountRoom()}; take one down, or raise the house.`; return ""; },
    mountTrophy(id) { const why = this.mountWhy(id); if (why) return why; this.logAct && this.logAct("mountTrophy", id); this.mounted().push(id); this.saveVillage();
      this.say(`${CM.GUARDIANS[id].name}'s trophy goes up on the wall: every hero who sets out from here has +1 ${CM.STAT_NAMES[CM.TROPHY_GIFT[id]]}.`); this.emit("change"); return ""; },
    unmountTrophy(id) { if (!this.inTown()) return "The trophy wall is at home."; const L = this.mounted(), i = L.indexOf(id); if (i < 0) return "It isn't on the wall."; this.logAct && this.logAct("unmountTrophy", id); L.splice(i, 1); this.saveVillage(); this.emit("change"); return ""; },
    homeGifts() { const F = this.furnished(), stats = {}; const add = (s) => { stats[s] = (stats[s] || 0) + 1; };
      if (F.bookcase) add("int"); if (F.shrine) add("wis"); if (F.rack) add("str"); if (F.stand) add("con"); for (const id of this.mounted()) if (CM.TROPHY_GIFT[id] && (this.trophies || {})[id]) add(CM.TROPHY_GIFT[id]);
      return { stats, morale: F.rug ? 8 : 0, rations: F.pantry ? 2 : 0, torch: F.lamp ? 100 : 0, gold: F.strongbox ? 60 : 0 }; },
  });
  CM.ACHIEVEMENTS.furnished = { name: "A Home Fit for Heroes", what: "Furnish the house with everything there is", title: "of the Hearth" };
  // a run setting out carries what the house gives
  const ng0 = G.newGame; G.newGame = function (...a) { const out = ng0.apply(this, a); if (this.replaying || this.film) return out; const H = this.homeLevel && this.homeLevel() >= 1 ? this.homeGifts() : null; if (!H) return out;
    for (const h of this.party || []) { let any = false; for (const [s, n] of Object.entries(H.stats)) { if (h.stats && h.stats[s] !== undefined) { h.stats[s] = Math.min(25, h.stats[s] + n); any = true; } } if (any) CM.recompute(h); }
    if (H.morale) this.morale = Math.min(100, (this.morale === undefined ? CM.MORALE.start : this.morale) + H.morale);
    for (let i = 0; i < H.rations; i++) this.bag.push(CM.ration()); if (H.torch && this.light && this.light.kind === "torch") this.light.left += H.torch; this.gold += H.gold;
    const n = Object.keys(this.furnished()).length + this.mounted().length; if (n) this.say(`From the house: ${[Object.keys(H.stats).length ? Object.entries(H.stats).map(([s, k]) => `+${k} ${CM.STAT_NAMES[s]}`).join(", ") + " for every hero" : "", H.morale ? "good heart" : "", H.rations ? "two rations more" : "", H.torch ? "a trimmed torch" : "", H.gold ? "sixty gold" : ""].filter(Boolean).join("; ")}.`);
    return out; };
}
