"use strict";
// Retirement to Legends' Row (v34.4, UPGRADE_PLAN_29.md): a hero of level fifty or more is offered it - to retire from
// the party to a house of their own on Legends' Row in town, and live there (six houses; the oldest legend moves on to
// make room). The party can visit; each legend teaches one hero who asks, once a run: +1 to the legend's calling's own
// stat for good, and to a hero of their own calling their first boon besides, if the hero hasn't it. The guildhall's
// trainers and the house's study are as they were.
//   CM.LEGEND_AT; game.legends(); game.retireLegend(i); game.legendTeach(legendIndex, heroIndex)
{ CM.LEGEND_AT = 50; CM.LEGEND_HOUSES = 6;
  const G = CM.Game.prototype, LINES = { Knight: "Keep your shield up and your back to a wall.", Rogue: "Never open the obvious chest first.", Cleric: "Heal the one who won't ask.", Mage: "Count your magic like coins.", Ranger: "Shoot the one giving orders.", Paladin: "An oath is a weight you choose to carry." };
  Object.assign(G, {
    legends() { const V = this.vext("legends"); V.list = V.list || []; return V.list; },
    retireLegendWhy(i) { if (!this.inTown()) return "Legends' Row is in town."; const h = this.party[i]; if (!h || h.hp <= 0) return "Only a hero on their feet retires.";
      if (h.level < CM.LEGEND_AT) return `A legend is a hero of level ${CM.LEGEND_AT} or more.`; if (this.party.filter((p) => p.hp > 0).length <= 1) return "Someone has to go down."; return ""; },
    retireLegend(i) { const why = this.retireLegendWhy(i); if (why) return why; this.logAct && this.logAct("retireLegend", i); const h = this.party[i], L = this.legends();
      const boon = (h.boons || [])[0] || null, scars = (h.scars || []).length; L.push({ name: h.name, cls: h.cls, level: h.level, origin: h.origin || null, boon, scars, date: CM.today ? CM.today() : "", taught: {} });
      let gone = null; if (L.length > CM.LEGEND_HOUSES) gone = L.shift(); this.saveVillage(); this.party.splice(i, 1);
      this.sound && this.sound("level"); this.say(`${h.name} the ${h.cls}, level ${h.level}, takes the keys to a house on Legends' Row. The town comes out to see.${gone ? ` (${gone.name} has moved on, and left the house to them.)` : ""}`);
      if (this.achieve) this.achieve("legend"); this.saveRun(); this.emit("change"); return ""; },
    legendTeachWhy(li, hi) { if (!this.inTown()) return "Legends' Row is in town."; const Lg = this.legends()[li], h = this.party[hi]; if (!Lg) return "No legend there."; if (!h || h.hp <= 0) return "Bring them on their feet.";
      if ((Lg.taught || {})[this.seed]) return `${Lg.name} has taught someone this run already.`; return ""; },
    legendTeach(li, hi) { const why = this.legendTeachWhy(li, hi); if (why) return why; this.logAct && this.logAct("legendTeach", li, hi); const Lg = this.legends()[li], h = this.party[hi], key = (CM.CLASSES[Lg.cls] || {}).key || "str";
      h.stats[key] = Math.min(25, h.stats[key] + 1); let more = ""; if (h.cls === Lg.cls && Lg.boon && !(h.boons || []).includes(Lg.boon)) { h.boons = (h.boons || []).concat(Lg.boon); more = " - and their own first boon besides"; }
      CM.recompute(h); (Lg.taught = Lg.taught || {})[this.seed] = h.name; this.saveVillage();
      this.say(`${Lg.name} spends the afternoon with ${h.name}: "${LINES[Lg.cls] || "Come back alive. That's the whole trick."}" +1 ${CM.STAT_NAMES[key]}${more}.`); this.saveRun(); this.emit("change"); return ""; },
  });
  CM.ACHIEVEMENTS.legend = { name: "A House on Legends' Row", what: "Retire a hero of level fifty to Legends' Row", title: "the Legendary" };
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "change" && this.party && this.tally && !this.replaying) for (const h of this.party) if (h.level >= CM.LEGEND_AT && h.hp > 0 && !h.legendOffered) { h.legendOffered = true;
      this.say(`${h.name} has nothing left to prove. At level ${h.level}, a house on Legends' Row in town is theirs if they want it.`); }
    return em0.call(this, ev, ...a); };
}
