"use strict";
// The daily challenge, scored (v33.3, UPGRADE_PLAN_28.md): Today's dungeon keeps its seed and its two mutators, and now
// sets the rest too, the same for everyone: the day's party (the classic four, named and rolled by the date, as the
// week's challenge does), the pauper's kit, Fair, no ascension and no again. Its end is scored - floors, the fallen,
// guardians, gold, a crown - and every day played is kept with its best score and how many tries, in the store
// ("dailyBoard"), for the title screen's page of days.
//   CM.dailyScore(entry) -> number;  game.dailyBoard() -> {date: {best, tries, floor, won}}
{ CM.DAILY_RULES = "the day's party (the classic four, rolled by the date), the pauper's kit, Fair, no ascension and no again";
  CM.dailyScore = (e) => { const t = e.tally || {}; return Math.max(0, Math.round((e.floor || 0) * 100 + (t.kills || 0) * 3 + (t.guardians || []).length * 250 + (e.gold || 0) / 10 + (t.chests || 0) * 5 + (e.won ? 2500 : 0) + (e.bottom ? 1500 : 0) - (t.steps || 0) / 40)); };
  const G = CM.Game.prototype, isDaily = (seed) => String(seed || "").startsWith("daily-");
  G.dailyBoard = function () { return CM.store.get("dailyBoard", {}) || {}; };
  const ng0 = G.newGame; G.newGame = function (seed, chosen, kit, difficulty, mutators, mode, opts) {
    if (isDaily(seed) && Array.isArray(chosen) && !(opts && opts.free)) { chosen = CM.weeklyParty(seed); kit = "pauper"; difficulty = "fair"; opts = Object.assign({}, opts || {}, { ascension: 0, again: 0 }); }
    const out = ng0.call(this, seed, chosen, kit, difficulty, mutators, mode, opts);
    if (isDaily(seed) && Array.isArray(chosen) && !(opts && opts.free)) this.say(`Today's rules, the same for everyone: ${CM.DAILY_RULES}. The run is scored when it ends.`);
    return out; };
  const end0 = G.endRun; G.endRun = function (won) {
    const daily = isDaily(this.seed) && !this.film && !this.replaying, before = daily ? { floor: this.floor ? this.floor.number : 0, gold: this.gold, tally: this.tally, won: Boolean(won || this.crowned), bottom: Boolean(this.bottom) } : null;
    const out = end0.call(this, won);
    if (daily) { const score = CM.dailyScore(before), day = String(this.seed).slice(6), B = this.dailyBoard(), was = B[day] || { best: 0, tries: 0 };
      B[day] = { best: Math.max(was.best, score), tries: was.tries + 1, floor: Math.max(was.floor || 0, before.floor), won: was.won || before.won, last: score };
      const keys = Object.keys(B).sort(); while (keys.length > 120) delete B[keys.shift()]; CM.store.set("dailyBoard", B);
      this.say(`Today's dungeon, scored: ${score.toLocaleString("en")}${score > was.best ? (was.tries ? " - the day's best yet" : "") : ` (the day's best: ${was.best.toLocaleString("en")})`}.`);
      if (score >= 3000 && this.achieve) this.achieve("dailyscore"); }
    return out; };
  CM.ACHIEVEMENTS.dailyscore = { name: "Score of the Day", what: "Score 3,000 in Today's dungeon", title: "the Daily" };
}
