"use strict";
// Seasons of the year (v33.1, UPGRADE_PLAN_28.md): each season of the year (the real date's, or the season pinned in
// the Settings) brings its trial, done once a season: spring's Thaw (the tenth floor within three days of setting
// out), summer's Long Day (a guardian slain on the run's first day, in daylight), autumn's Wild Hunt (forty beasts slain
// in one expedition), winter's Long Hunger (the fifteenth floor with no meal or dish eaten all the way). Each pays a
// thing only that season gives, into the pack; the four together are a feat.
//   CM.SEASON_TRIALS[season] -> {name, what, reward()};  game.trialKey(); game.trialDone(); game.trialProgress()
{ const ring = (name, props, value) => ({ name, base: name, kind: "ring", slot: "ring", power: 2, value, unknown: false, props: Object.assign({ rarity: "unique", seasonal: true }, props) });
  const amulet = (name, props, value) => ({ name, base: name, kind: "amulet", slot: "amulet", power: 0, value, unknown: false, props: Object.assign({ rarity: "unique", seasonal: true }, props) });
  const ST = CM.SEASON_TRIALS = {
    spring: { name: "The Thaw", what: "reach the tenth floor within three days of setting out", reward: () => amulet("Thaw-water Charm", { df: 2, stats: { con: 2 }, regen: 1 }, 600) },
    summer: { name: "The Long Day", what: "slay a guardian on the run's first day, while the sun is up", reward: () => ring("Ring of the Long Day", { stat: "str", stats: { luck: 1 }, init: 1 }, 650) },
    autumn: { name: "The Wild Hunt", what: "slay forty beasts in one expedition", reward: () => ring("Huntsman's Ring", { stat: "dex", crit: 0.05, vsHide: 1.2 }, 650) },
    winter: { name: "The Long Hunger", what: "reach the fifteenth floor with no meal or dish eaten all the way down", reward: () => amulet("Rime-hunger Torc", { df: 2, stats: { wis: 2, con: 1 } }, 700) },
  };
  for (const s of Object.keys(ST)) { const it = ST[s].reward(); CM.BASES[it.name] = { id: it.name, kind: it.kind, slot: it.slot, tier: 3, group: it.kind }; }
  CM.ACHIEVEMENTS.seasoned = { name: "A Year Round", what: "Do every season's trial", title: "of the Seasons" }; if (CM.FEATS2) CM.FEATS2.seasoned = (g) => { const V = g.vext("seasons"); return ["spring", "summer", "autumn", "winter"].every((s) => Object.keys(V).some((k) => k.endsWith(`-${s}`))); };
  const G = CM.Game.prototype, year = () => new Date().getFullYear();
  Object.assign(G, {
    trialKey() { const s = CM.season(this); return `${s === "winter" && new Date().getMonth() < 2 ? year() - 1 : year()}-${s}`; },
    trialDone() { return Boolean(this.vext("seasons")[this.trialKey()]); },
    trialProgress() { const s = CM.season(this), T = this.tally || {}, day = CM.dayOf ? CM.dayOf(this) : 0, deep = this.deepestReached ? this.deepestReached() : 0;
      if (s === "spring") return day <= 2 ? `floor ${deep} of 10, day ${day + 1} of 3` : "past the third day";
      if (s === "summer") return day === 0 ? "the first day: a guardian before dusk" : "past the first day";
      if (s === "autumn") return `${T.beasts || 0} of 40 beasts`;
      return (T.ateAny ? "a meal was eaten" : `floor ${deep} of 15, nothing eaten`); },
    trialCheck(how) { if (this.replaying || this.film || this.trialDone()) return; const s = CM.season(this), T = this.tally || {}, day = CM.dayOf ? CM.dayOf(this) : 0, deep = this.deepestReached ? this.deepestReached() : 0;
      const ok = s === "spring" ? deep >= 10 && day <= 2 : s === "summer" ? how === "guardian" && day === 0 && !CM.isNight(this) : s === "autumn" ? (T.beasts || 0) >= 40 : deep >= 15 && !T.ateAny;
      if (!ok) return; const V = this.vext("seasons"), it = ST[s].reward(); V[this.trialKey()] = { date: CM.today ? CM.today() : "", seed: this.seed, item: it.name }; this.saveVillage && this.saveVillage();
      this.gain([it], "trial"); this.sound && this.sound("toll"); this.say(`${ST[s].name}: done, this ${s}. The season gives what only it gives: ${it.name}.`); this.checkFeats && this.checkFeats(); },
  });
  const wf0 = G.wonFight; G.wonFight = function (...a) { const slain = (this.foes || []).filter((m) => !m.fled && !m.summoned), beasts = slain.filter((m) => ((CM.monsterKind && CM.monsterKind(m.kind || m.name)) || {}).body === "beast").length;
    const out = wf0.apply(this, a); if (beasts) this.tally.beasts = (this.tally.beasts || 0) + beasts; this.trialCheck("fight"); return out; };
  const sg0 = G.slayGuardian; G.slayGuardian = function (m) { const out = sg0.call(this, m); if (m && !m.echo) this.trialCheck("guardian"); return out; };
  const em0 = G.emit; G.emit = function (ev, ...a) { if (this.meal && this.tally && !this.tally.ateAny) this.tally.ateAny = true; if (ev === "floor") this.trialCheck("floor"); return em0.call(this, ev, ...a); };   /* (any meal at all, from any table, breaks the hunger) */

}
