"use strict";
// New Game+, "again" (v33.2, UPGRADE_PLAN_28.md): the Lich King slain opens the way to set out again - a run of the
// next "again" up to the highest won plus one (to ten). An again-run carries one thing from the gear the winning
// party wore, chosen when it sets out, as an heirloom; its monsters are a quarter tougher and an eighth harder-hitting
// a time again; its fights pay more and now and then leave a better thing (a quarter's chance a time again, deeper by
// two floors a time). Kept between runs in the store: "againWon" (the highest again won) and "againHeirlooms".
//   game.againMax(); game.againHeirlooms(); game.newGame(..., opts.again, opts.heirloom); game.againLevel()
{ CM.AGAIN = { hp: 0.25, atk: 0.125, gold: 0.25, find: 0.25, most: 10, keep: 8 };
  const A = CM.AGAIN, G = CM.Game.prototype;
  Object.assign(G, {
    againLevel() { return (this.tally && this.tally.ext && this.tally.ext.again && this.tally.ext.again.level) || 0; },
    againMax() { return Math.min(A.most, (CM.store.get("againWon", -1) | 0) + 1); },
    againHeirlooms() { return CM.store.get("againHeirlooms", []) || []; },
  });
  // the crown falls: the next again opens, and what the party wore is kept to choose from
  const em0 = G.emit; G.emit = function (ev, ...a) {
    if (ev === "crowned" && !this.replaying && !this.film) { const L = this.againLevel(); if (L >= (CM.store.get("againWon", -1) | 0)) CM.store.set("againWon", L);
      const worn = []; for (const h of this.party || []) for (const it of CM.equipped(h)) if (!(it.props || {}).cursed && it.kind !== "key") worn.push(JSON.parse(JSON.stringify(it)));
      worn.sort((x, y) => (y.value || 0) - (x.value || 0)); CM.store.set("againHeirlooms", worn.slice(0, A.keep));
      this.say(`The way is open to set out again - "again ${Math.min(A.most, L + 1)}": the dungeon deeper and meaner, and one thing of this party's carried down.`); }
    return em0.call(this, ev, ...a); };
  const ng0 = G.newGame; G.newGame = function (seed, chosen, kit, difficulty, mutators, mode, opts) {
    const out = ng0.call(this, seed, chosen, kit, difficulty, mutators, mode, opts); const L = Math.max(0, Math.min((opts && opts.again) | 0, this.againMax()));
    if (L > 0) { this.ext("again").level = L; const H = this.againHeirlooms(), pick = opts && Number.isInteger(opts.heirloom) ? H[opts.heirloom] : H[0];
      if (pick) { const it = JSON.parse(JSON.stringify(pick)); it.props = it.props || {}; it.props.againHeirloom = true; this.bag.push(it); this.ext("again").heirloom = it.name; }
      this.say(`Again ${L}: the dungeon is deeper and meaner than it was - monsters ${Math.round(A.hp * L * 100)}% tougher and ${Math.round(A.atk * L * 100)}% harder-hitting, and better found.${pick ? ` Carried down from the last crowning: ${pick.name}.` : ""}`); }
    return out; };
  const tune0 = G.tune; G.tune = function (m) { if (!m || m.tuned) return tune0.call(this, m); const out = tune0.call(this, m), L = this.againLevel();
    if (L > 0 && out) { out.max = Math.max(1, Math.round(out.max * (1 + A.hp * L))); out.hp = Math.max(1, Math.round(out.hp * (1 + A.hp * L))); out.atk = Math.max(1, Math.round(out.atk * (1 + A.atk * L))); }
    return out; };
  const wf0 = G.wonFight; G.wonFight = function (...a) { const L = this.againLevel(), gold = this.gold, out = wf0.apply(this, a);
    if (L > 0 && this.floor) { const got = this.gold - gold; if (got > 0) { const more = Math.round(got * A.gold * L); this.gold += more; }
      if ((CM.hashSeed(`${this.seed}:againfind:${this.tally.fights || 0}`) % 1000) / 1000 < Math.min(0.75, A.find * L)) { const r = new CM.Random(CM.hashSeed(`${this.seed}:againitem:${this.tally.fights || 0}`)), fl = this.floor.number + 2 * L;
        const it = CM.affix(CM.makeItem(fl, r), fl, r); this.gain([it], "foe"); this.say(`Among the fallen, something finer than this depth usually holds: ${it.unknown ? CM.baseName(it) : it.name}.`); } }
    return out; };
  CM.ACHIEVEMENTS.again = { name: "And Again", what: "Slay the Lich King on a run set out again", title: "the Returning" };
  const em1 = G.emit; G.emit = function (ev, ...a) { if (ev === "crowned" && this.againLevel() > 0 && this.achieve) this.achieve("again"); return em1.call(this, ev, ...a); };
}
