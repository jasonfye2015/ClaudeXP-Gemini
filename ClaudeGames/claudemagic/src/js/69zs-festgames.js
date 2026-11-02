"use strict";
// Festivals, kept (v36.1, UPGRADE_PLAN_31.md): in a festival's week the town holds three games for the party, once
// each a festival - a test of arm (the strongest hero's Strength), of eye (the best Dexterity) and of wit (the best
// Intelligence), each the hero's stat and a throw of a twenty against the festival's mark. Each won pays gold and a
// little renown; all three won take the festival's favour, a charm only it gives, once a year. The town's dressing and
// its tune are the window's (76zzzzzzk-festival.js).
//   CM.FEST_GAMES; game.festKey(); game.festPlay(id) -> {won, roll, total} or {error}; game.festFavour(fest)
{ const FG = CM.FEST_GAMES = { arm: { name: "the tug and the stone", stat: "str", what: "a test of arm" }, eye: { name: "the butts", stat: "dex", what: "a test of eye" }, wit: { name: "the riddle-tent", stat: "int", what: "a test of wit" } };
  CM.FEST_MARK = 28; CM.FEST_GOLD = 60; CM.FEST_RENOWN = 3;
  const G = CM.Game.prototype;
  CM.festFavour = (fest) => { const F = CM.FESTIVALS[fest] || { name: "the fair" }; return { name: `Favour of ${F.name.replace(/^the /, "the ")}`.replace("Favour of Midwinter", "Midwinter's Favour"), base: "Festival Favour", kind: "amulet", slot: "amulet", power: 0, value: 400, unknown: false,
      props: { rarity: "unique", df: 1, stats: { str: 1, dex: 1, con: 1, int: 1, wis: 1, luck: 1 }, festival: fest } }; };
  CM.BASES["Festival Favour"] = { id: "Festival Favour", kind: "amulet", slot: "amulet", tier: 2, group: "amulet" };
  Object.assign(G, {
    festKey() { const f = CM.festival(this); return f ? `${new Date().getFullYear()}:${f}` : null; },
    festRecord() { const k = this.festKey(); if (!k) return null; const V = this.vext("festgames"); return (V[k] = V[k] || { played: {}, won: {}, favour: false }); },
    festWhy(id) { if (!CM.festival(this)) return "There's no festival this week."; if (!this.inTown || !this.inTown()) return "The games are in town."; if (!FG[id]) return "No such game."; if (this.festRecord().played[id]) return "Played already, this festival."; return ""; },
    festPlay(id) { const why = this.festWhy(id); if (why) return { error: why }; this.logAct && this.logAct("festPlay", id);
      const R = this.festRecord(), stat = FG[id].stat, hero = this.party.filter((h) => h.hp > 0).sort((a, b) => this.stat(b, stat) - this.stat(a, stat))[0];
      const roll = 1 + (CM.hashSeed(`${this.seed}:fest:${this.festKey()}:${id}:${hero ? hero.name : ""}`) % 20), total = (hero ? this.stat(hero, stat) : 10) + roll, won = total >= CM.FEST_MARK;
      R.played[id] = true; if (won) { R.won[id] = true; this.gold += CM.FEST_GOLD; this.village.renown = (this.village.renown || 0) + CM.FEST_RENOWN; }
      this.say(`${hero ? hero.name : "Someone"} tries ${FG[id].name}: ${total} against the mark of ${CM.FEST_MARK} - ${won ? `won! ${CM.FEST_GOLD} gold and the crowd's cheer.` : "not this year, to friendly jeers."}`);
      if (Object.keys(FG).every((k) => R.won[k]) && !R.favour) { R.favour = true; const it = CM.festFavour(CM.festival(this)); this.gain([it], "festival"); this.sound && this.sound("toll"); this.say(`All three games won: the festival's own favour - ${it.name}.`); if (this.achieve) this.achieve("festive"); }
      this.saveVillage && this.saveVillage(); this.saveRun && this.saveRun(); this.emit("change"); return { won, roll, total, hero: hero ? hero.name : "" }; },
  });
  CM.ACHIEVEMENTS.festive = { name: "Champion of the Fair", what: "Win all three of a festival's games", title: "the Festive" };
}
