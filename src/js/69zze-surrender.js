"use strict";
// Surrender and parley (v38.3, UPGRADE_PLAN_33.md): foes who can speak - kobolds and goblins, orcs, trolls and ogres,
// dark elves, imps, sellswords, hedge-wizards, hags, minotaurs, demons - badly beaten (all that stand of them at a
// quarter of their health or less, the party mostly on its feet) now and then throw down their weapons, once a fight:
// spare them (they go, leaving their purse - no blood, no experience - and the party's heart lifts) or finish them.
// Kept between runs: how many of each kind have been spared. A kind spared five times remembers: once a run, coming onto
// a floor where they are, one of them slips the party a word - the floor's map, chalked on a scrap.
//   CM.SPEAKERS; game.answerSurrender(i)
{ CM.SPEAKERS = new Set(["Kobold", "Goblin", "Orc", "Troll", "Ogre", "Dark Elf", "Foundry Imp", "Bellows Imp", "Sellsword", "Hedge Wizard", "Weed Hag", "Minotaur", "Demon"]);
  CM.SPARE_REMEMBER = 5;
  const G = CM.Game.prototype, can = (m) => CM.SPEAKERS.has(m.kind || m.name) && !m.guardian && !m.boss;
  G.answerSurrender = function (i) { const c = this.combat; if (this.mode !== "combat" || !c || !c.yielded || c.answered) return false; this.logAct && this.logAct("answerSurrender", i); c.answered = true;
    const left = this.living(); if (i !== 0) { this.say("No quarter. They see it in your faces, and pick their weapons up again."); for (const m of left) m.atk = Math.ceil(m.atk * 1.1); return true; }
    const gold = left.reduce((n, m) => n + Math.max(3, Math.round((m.gold || 0) + (this.floor ? this.floor.number : 1) * 4)), 0); this.gold += gold; this.cheer && this.cheer(6);
    const S = CM.store.get("spared", {}) || {}; for (const m of left) { m.fled = true; m.spared = true; const k = m.kind || m.name; if (!this.replaying && !this.film) S[k] = (S[k] || 0) + 1; } if (!this.replaying && !this.film) CM.store.set("spared", S);
    this.tally.spared = (this.tally.spared || 0) + left.length; this.say(`They back away with their hands open, leave a purse on the stones - ${gold} gold - and are gone into the dark. Nobody says anything for a moment. It feels better than it should.`);
    if (this.achieve) this.achieve("merciful2"); this.afterBlows(); return true; };
  CM.ACHIEVEMENTS.merciful2 = { name: "Quarter Given", what: "Spare foes who threw down their weapons", title: "the Quarter-giver" };
  const ab0 = G.afterBlows; G.afterBlows = function (...a) { const out = ab0.apply(this, a), c = this.combat;
    if (this.mode === "combat" && c && !c.yielded && c.round >= 2) { const left = this.living(); const tot = left.reduce((n, m) => n + m.max, 0), cur = left.reduce((n, m) => n + Math.max(0, m.hp), 0), up = this.alive();
      if (left.length && left.every(can) && cur <= tot / 4 && up.length >= Math.ceil(this.party.length / 2) && CM.hashSeed(`${this.seed}:yield:${this.floor ? this.floor.number : 0}:${this.tally.fights || 0}`) % 2 === 0) {
        c.yielded = true; const K = left[0].kind || left[0].name; this.say(`${left.length === 1 ? `The ${K.toLowerCase()} throws down its weapon` : `They throw down their weapons`} and go to their knees.`);
        this.emit("choice", { k: "surrender", title: "Quarter?", text: `${left.length === 1 ? `The last ${K.toLowerCase()}` : `The last of them`}, beaten and bleeding, ${left.length === 1 ? "holds" : "hold"} up empty hands. Spare them, and they'll go - and leave what they carry. Or finish it.`, options: ["Spare them", "Finish them"], surrender: true }); } }
    return out; };
  // the ones who remember
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.floor.number >= 1 && this.floor.number < 1000 && this.tally && !this.ext("remembered").done) { const S = CM.store.get("spared", {}) || {}, fl = this.floor;
      const kinds = new Set(); for (const t of Object.values(fl.things)) if (t.type === "monsters") for (const m of t.group || []) kinds.add(m.kind || m.name); const k = [...kinds].find((x) => (S[x] || 0) >= CM.SPARE_REMEMBER);
      if (k && !this.replaying && !this.film) { this.ext("remembered").done = true; fl.seen = []; for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) fl.seen.push([x, y]);
        this.say(`A ${k.toLowerCase()} steps out of a side-passage with its hands open - one of the ones you let go, or kin to them. It presses a scrap of hide into your hand: this floor, chalked out, every turn. Then it's gone.`); } }
    return em0.call(this, ev, ...a); };
  const ch0 = G.choose; G.choose = function (k, i, ...a) { if (k === "surrender") return this.answerSurrender(i); return ch0.call(this, k, i, ...a); };   /* (the 1 and 2 keys on the choice) */
}
