"use strict";
// The ways between (v18.3): the game's places trade with each other more.
// - Haven's potions come home: the potions a hero found in Claudeablo (beyond those they went in with, which stay
//   there, as the gold does) become the party's own - healing, mana, and the full ones as strong healing.
// - The party's relics go in: a relic, unique or heirloom a hero wears through the red portal is echoed in Haven - a
//   rare piece of the same kind, made for the hero's level and bearing the relic's name - once for each relic.
// - The pipe's coins count at the Joker: beside the gold, every five coins carried out of the pipe is a prize ticket.
// - Island tempering at the smith: a metal bar from the island (or the smelter) and an essence from the dungeon put
//   +1 on a worn weapon or armour, once a piece - the two places' stuff meeting at one anvil.
// The window's side (the smith's new row) is 76zzze-links.js.
{ const LK = CM.LINKS = { coinsPerTicket: 5, temper: { power: 1, gold: 40 } };
  const P = CM.Game.prototype, leaveA0 = P.leaveClaudeablo, enterA0 = P.enterClaudeablo, leaveB0 = P.leaveBros;
  const potCount = (inv) => inv.reduce((n, it) => n + (it && CM.AB.kind(it) === "potion" ? it.qty || 1 : 0), 0);
  const potionFor = (base, lvl) => /Mana/.test(base) ? { name: /Full/.test(base) ? "Greater Mana Potion" : "Mana Potion", kind: "mana", power: (/Full/.test(base) ? 30 : 14) + lvl, value: 25 }
    : { name: /Full|Rejuvenation/.test(base) ? "Greater Healing Potion" : "Healing Potion", kind: "heal", power: (/Full|Rejuvenation/.test(base) ? 60 : 25) + lvl * 2, value: 20 };
  Object.assign(P, {
    leaveClaudeablo(...a) { const w = this.abloWorld, h = w && this.party[this.abloHero], home = [];
      if (w && h) { const inv = w.player.inv; let extra = potCount(inv) - (w.potsIn || 0);   // (as with the gold: what they came with stays in Haven; what was found comes home)
        for (let k = inv.length - 1; k >= 0 && extra > 0; k--) { const it = inv[k]; if (!it || CM.AB.kind(it) !== "potion") continue; const n = Math.min(extra, it.qty || 1); for (let q = 0; q < n; q++) home.push(potionFor(it.base, h.level)); extra -= n; it.qty = (it.qty || 1) - n; if (it.qty <= 0) inv[k] = null; } }
      const out = leaveA0.apply(this, a); if (home.length) { this.gain(home, "claudeablo"); this.say(`${home.length} potion${home.length > 1 ? "s" : ""} from Haven come home in the pack.`); } return out; },
    enterClaudeablo(i) { const why = enterA0.call(this, i); if (why) return why; const h = this.party[i], w = this.abloWorld; w.potsIn = potCount(w.player.inv); const A = this.abloStore(), key = CM.abloKey(h); A.echoes = A.echoes || {}; const done = A.echoes[key] = A.echoes[key] || [];
      const relics = CM.equipped(h).filter((it) => it.props && !it.unknown && (it.props.relic || it.props.unique || it.props.heirloom) && !done.includes(it.name)); const AB = CM.AB, made = [];
      for (const it of relics) { const slot = it.kind === "shield" ? "shield" : it.kind === "weapon" ? "weapon" : it.kind === "armor" ? "armor" : it.kind === "helm" ? "helm" : it.kind === "ring" ? "ring" : it.kind === "amulet" ? "amulet" : null; if (!slot) continue;
        const want = slot === "weapon" ? { warrior: ["sword", "axe", "mace"], rogue: ["bow"], sorcerer: ["staff"] }[w.player.cls] || ["sword"] : null;
        const bases = Object.entries(AB.BASES).filter(([, B]) => B[1] === slot && B[2] <= h.level + 2 && (!want || want.includes(B[0]))).sort((a, b) => b[1][2] - a[1][2]); if (!bases.length) continue;
        const R = new AB.Rng(CM.hashSeed(`${this.seed}:echo:${key}:${it.name}`)), echo = AB.make(bases[0][0], h.level + 2, "rare", R, true); echo.rare_name = it.name;
        if (w.player.addItem(echo)) { done.push(it.name); made.push(it.name); } }
      if (made.length) { w.say(`Something of home came through with ${h.name}: ${made.join(", ")} - echoed here, in the pack.`, "#F0C060"); this.saveVillage && this.saveVillage(); } return ""; },
    leaveBros(how) { const r = this.brosRun, coins = r ? r.coins || 0 : 0, out = leaveB0.call(this, how), tk = Math.floor(coins / LK.coinsPerTicket); if (tk > 0 && this.tkAdd && this.cgStore) { this.tkAdd(tk, "bros"); this.say(`${coins} coins out of the pipe: ${tk} prize ticket${tk > 1 ? "s" : ""} at the Joker besides.`); } return out; },
    // ---- island tempering ----
    islandTemperWhy(hero, slot) { const h = typeof hero === "number" ? this.party[hero] : hero, it = h && h[slot]; if (!it || !["weapon", "armor"].includes(slot)) return "Only a worn weapon or armour takes tempering.";
      if (it.unknown) return "The smith wants to know what it is first."; if (it.props && it.props.fists) return "Bare hands don't temper."; if (it.props && it.props.tempered) return "Tempered already.";
      if (!this.bag.some((x) => x.kind === "bar")) return "It wants a metal bar (from the island, or the smelter)."; if (!this.bag.some((x) => x.kind === "essence")) return "It wants an essence (from the dungeon's deep things).";
      if (this.gold < LK.temper.gold) return `The smith's fee is ${LK.temper.gold} gold.`; return ""; },
    islandTemper(hero, slot) { const hi = typeof hero === "number" ? hero : this.party.indexOf(hero), h = this.party[hi], why = this.islandTemperWhy(h, slot); if (why) return why; this.logAct && this.logAct("islandTemper", hi, slot);
      this.bag.splice(this.bag.findIndex((x) => x.kind === "bar"), 1); this.bag.splice(this.bag.findIndex((x) => x.kind === "essence"), 1); this.gold -= LK.temper.gold;
      const it = h[slot]; it.props = Object.assign({}, it.props, { tempered: true }); it.power = (it.power || 0) + LK.temper.power; it.value = Math.round((it.value || 0) * 1.15); CM.recompute(h); this.sound && this.sound("anvil"); this.emit && this.emit("change"); return ""; },
  });
}
