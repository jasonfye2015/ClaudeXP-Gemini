"use strict";
// Monster habits (v38.2, UPGRADE_PLAN_33.md): every kind has a habit - who it goes for, when it runs, what it does
// first - read from what it is (its way of fighting, its body, its touch). A party reads it once it has slain five of the
// kind in the run (its own eyes: a replayed run reads the same): told then, told again when a fight with them begins,
// and an edge against that kind - every blow and spell on it a tenth harder. Once read it is written in the bestiary for
// good (what the window shows; the rules go by the run's own count).
//   CM.habitOf(kindName) -> text;  game.habitKnown(kindName) (this run);  game.habitRead(kindName) (ever);  CM.HABIT_AT
{ CM.HABIT_AT = 5; CM.HABIT_EDGE = 0.1;
  const BY = { ranged: "it stands off and shoots at whoever is easiest to see - rush it", savage: "it saves its worst for a hero already bleeding - keep the hurt at the back", charge: "it charges with its first blow and is spent after - meet the first with a shield",
    coward: "it runs once it is hurt - finish it before it reaches the stair", lifesteal: "it feeds on what it hurts - keep it from the wounded", drain: "it goes for whoever has learnt the most - shield the seasoned",
    regen: "it mends while it waits - never let it rest a round", buffet: "it strikes twice, wildly - a defended hero takes little of it", web: "it webs the quickest first - the slow ones stay free",
    stun: "it aims at the head - helms help", howl: "its howl comes every third round - cheer the party before it", healer: "it keeps the others standing - kill it first", thief: "it goes for the purse and runs - kill it while it's close",
    splitter: "it splits when struck hard - strike it many small blows", shieldwall: "its kind lock shields - break the front to reach the back", mimic: "it waits to be opened - a Rogue's knife first",
    warder: "it turns aside the first spell - lead with a blade", spawns: "it bursts out young every third turn - kill it before the brood", breath: "it breathes over the whole party - spread out (Loose)", astray: "its touch leads a hero astray - keep together",
    burrow: "it goes under the floor every third turn - strike when it comes up" };
  CM.habitOf = (name) => { const K = CM.monsterKind(name) || {}; if (K.ability && BY[K.ability]) return BY[K.ability]; if (K.undead) return "it never flees and never tires - wear it down from the front";
    if (K.flees) return "it bolts at the first blow - the first blow had better be a good one"; if (K.body === "beast") return "it goes for the nearest throat - the front row takes all of it"; if (K.row === "back") return "it hangs back behind the others - reach for it";
    return "it fights whoever is in front of it, and fights to the end"; };
  const G = CM.Game.prototype;
  G.habitKnown = function (name) { const S = this.tally && this.tally.ext && this.tally.ext.slainKind; return Boolean(S && (S[name] || 0) >= CM.HABIT_AT); };
  G.habitRead = function (name) { const e = (this.bestiary || {})[name]; return Boolean(e && e.habit); };
  const sc0 = G.startCombat; G.startCombat = function (...a) { const out = sc0.apply(this, a); if (this.mode === "combat" && this.foes) { const told = new Set();
      for (const m of this.foes) { const k = m.kind || m.name; if (told.has(k) || !this.habitKnown(k) || m.guardian || m.boss) continue; told.add(k); this.say(`You know the ${k.toLowerCase()}'s way: ${CM.habitOf(k)}.`); } }
    return out; };
  const edge = (g, m, out) => { if (!(out > 0) || !m || m.hp <= 1 || m.guardian || m.boss || !g.habitKnown(m.kind || m.name)) return; const more = Math.max(1, Math.round(out * CM.HABIT_EDGE)); m.hp = Math.max(1, m.hp - more); g.tally.habitEdge = (g.tally.habitEdge || 0) + more; };
  const st0 = G.strike; G.strike = function (hero, target, ...a) { const out = st0.call(this, hero, target, ...a); edge(this, target, out); return out; };
  const sh0 = G.spellHit; G.spellHit = function (foe, dmg, ...a) { const out = sh0.call(this, foe, dmg, ...a); edge(this, foe, out); return out; };
  const nf0 = G.noteFoe; if (nf0) G.noteFoe = function (m, how, ...a) { const k = m && (m.kind || m.name), out = nf0.call(this, m, how, ...a);
    if (k && how === "slain" && !m.summoned && CM.monsterKind(k)) { const S = this.ext("slainKind"); S[k] = (S[k] || 0) + 1;
      if (S[k] === CM.HABIT_AT) { this.say(`${CM.HABIT_AT} ${k.toLowerCase()}s slain: you have their measure now - ${CM.habitOf(k)}.`); const e = (this.bestiary = this.bestiary || {})[k]; if (e && !e.habit && !this.replaying && !this.film) { e.habit = true; this.bestiaryDirty = true; } } }
    return out; };
}
