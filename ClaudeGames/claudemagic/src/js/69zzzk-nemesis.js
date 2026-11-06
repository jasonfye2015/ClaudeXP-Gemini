"use strict";
// The nemesis (UPGRADE_PLAN_68.md, part 2): when a run ends in a fight the party lost, the strongest foe still standing
// is remembered with the browser's things - its kind, the names of the party it took, the floor and the day - and the
// title card (77c-splashfoes.js) has it lurk at the tree line with that said under it.
//   CM.store "nemesis" -> { kind, name, party: [names], floor, date } | null;  CM.nemesisLine(n) -> its words
{ const P = CM.Game.prototype;
  CM.nemesisLine = (n) => { if (!n || !n.name) return ""; const who = (n.party || [])[0], the = /^the /i.test(n.name) || /^[A-Z][a-z]+, /.test(n.name) ? n.name : `The ${n.name}`; return `${the} that took ${who ? `${who}'s party` : "your last party"}, floor ${n.floor}`; };
  const e0 = P.endRun;
  P.endRun = function (won, ...a) {
    let foe = null;
    if (!won && this.mode === "combat" && Array.isArray(this.foes)) foe = this.foes.filter((m) => m && m.hp > 0 && !m.summoned).sort((x, y) => (y.max || 0) - (x.max || 0))[0] || null;
    const floor = this.floor ? this.floor.number : 0, party = (this.party || []).map((h) => h.name);
    const out = e0.call(this, won, ...a);
    if (foe && !this.replaying) CM.store.set("nemesis", { kind: foe.kind || foe.name, name: foe.name, party, floor, date: CM.today ? CM.today() : "" });
    return out;
  };
}
