"use strict";
// Camp scenes (v34.0, UPGRADE_PLAN_29.md): what has happened since the last camp is kept - the slain, the finds worth
// a word, the guardians, who fell, the gold - and at a camp the four talk it over round the fire. game.campTalk()
// gives the lines, each with who says it, chosen by what happened and who they are (and the run's seed, so a replay
// hears the same). The fire itself is the window's (76zzzzzzb-fireside.js).
//   game.sinceCamp() -> the log;  game.campTalk() -> [{who, line}]
{ const G = CM.Game.prototype, log = (g) => { const E = g.ext("sincecamp"); E.kills = E.kills || 0; E.finds = E.finds || []; E.guardians = E.guardians || []; E.fell = E.fell || []; E.gold0 = E.gold0 === undefined ? g.gold : E.gold0; E.floors = E.floors || []; return E; };
  G.sinceCamp = function () { return log(this); };
  const wf0 = G.wonFight; G.wonFight = function (...a) { const n = (this.foes || []).filter((m) => !m.fled).length, out = wf0.apply(this, a); log(this).kills += n; return out; };
  const gain0 = G.gain; G.gain = function (items, how) { if (Array.isArray(items) && this.ext) for (const it of items) if (it && ["rare", "unique", "relic"].includes(CM.rarityOf(Object.assign({}, it, { unknown: false })))) { const L = log(this).finds; if (L.length < 6) L.push(it.unknown ? CM.baseName(it) : it.name); } return gain0.call(this, items, how); };
  const sg0 = G.slayGuardian; G.slayGuardian = function (m) { const out = sg0.call(this, m); if (m && !m.echo && CM.GUARDIANS[m.guardian]) log(this).guardians.push(CM.GUARDIANS[m.guardian].name); return out; };
  const em0 = G.emit; G.emit = function (ev, ...a) {
    if (this.tally && this.party) { if (ev === "floor" && this.floor && this.floor.number > 0) { const L = log(this); if (!L.floors.includes(this.floor.number)) L.floors.push(this.floor.number); }
      if (ev === "change") { const L = log(this); for (const h of this.party) if (h.hp <= 0 && !L.fell.includes(h.name)) L.fell.push(h.name); }
      if (ev === "mode") { if (this.mode === "camp") this.ext().lastCampLog = JSON.parse(JSON.stringify(log(this))); else if (a[0] === "explore" && this.ext().inCamp) { this.ext().sincecamp = null; log(this); }
        this.ext().inCamp = a[0] === "camp"; } }
    return em0.call(this, ev, ...a); };
  const pick = (g, salt, list) => list[CM.hashSeed(`${g.seed}:fire:${salt}:${(g.camps || []).length}:${(g.tally && g.tally.fights) || 0}`) % list.length];
  G.campTalk = function () {
    const L = (this.mode === "camp" && this.ext().lastCampLog) || log(this), up = this.party.filter((h) => h.hp > 0), out = [], said = new Set();
    if (!up.length) return out; const by = (pref, salt) => { const c = up.filter((h) => !said.has(h.name)); const p = c.find((h) => pref && pref.includes(h.cls)) || pick(this, salt, c.length ? c : up); said.add(p.name); return p; };
    const hurt = up.filter((h) => h.hp / Math.max(1, h.max) < 0.4).sort((a, b) => a.hp / a.max - b.hp / b.max)[0];
    for (const name of L.fell.filter((n) => !up.some((h) => h.name === n)).slice(0, 1)) { const s = by(["Cleric", "Paladin"], "fell"); out.push({ who: s.name, line: pick(this, "fellline", [`Nobody sits in ${name}'s place. ${s.name} leaves it empty, and says a word over it.`, `${s.name}: "${name} would have laughed at us, sitting here this quiet."`, `${s.name} sets ${name}'s cup by the fire anyway.`]) }); }
    if (hurt) { const s = by(["Cleric", "Druid", "Paladin", "Alchemist"], "hurt"); out.push({ who: s.name, line: s === hurt ? `${s.name} sits closest to the fire, saying nothing about the wound.` : pick(this, "hurtline", [`${s.name}: "Hold still, ${hurt.name}. That one will scar."`, `${s.name} binds ${hurt.name}'s arm again. "You walk in front of things."`, `${s.name}: "${hurt.name}, eat something. You look like the floor won."`]) }); }
    if (L.guardians.length) { const s = by(["Knight", "Warden"], "guard"); out.push({ who: s.name, line: pick(this, "guardline", [`${s.name}: "${L.guardians[0]}. I'll be dreaming about that one."`, `${s.name} holds up a hand, still shaking. "${L.guardians[0]}. We did that."`, `${s.name}: "They'll sing about ${L.guardians[0]} in the tavern. Badly."`]) }); }
    if (L.finds.length) { const s = by(["Rogue", "Artificer"], "find"); out.push({ who: s.name, line: pick(this, "findline", [`${s.name} turns ${L.finds[0]} over in the firelight. "Worth the walk."`, `${s.name}: "Did anyone else see ${L.finds[0]} glow? No? Just me, then."`, `${s.name} won't let go of ${L.finds[0]}. Nobody asks them to.`]) }); }
    if (L.kills >= 12) { const s = by(["Knight", "Monk", "Ranger"], "kills"); out.push({ who: s.name, line: pick(this, "killline", [`${s.name}: "${L.kills} of them. I stopped counting at twenty. Then I counted again."`, `${s.name} cleans the blade slowly. "${L.kills}. Is it always like this further down?"`]) }); }
    else if (L.kills <= 2 && L.floors.length) { const s = by(null, "quiet"); out.push({ who: s.name, line: pick(this, "quietline", [`${s.name}: "Quiet down there. I don't like quiet."`, `${s.name}: "Hardly a fight. Something's waiting for us, then."`]) }); }
    const gold = this.gold - (L.gold0 || 0); if (gold >= 150 && up.length >= 2) { const s = by(["Rogue", "Bard"], "gold"); out.push({ who: s.name, line: `${s.name} counts the purse twice. "${gold.toLocaleString("en")} more than we came down with. Not bad."` }); }
    for (const [a, b] of (this.bonds || []).slice(0, 1)) if (up.some((h) => h.name === a) && up.some((h) => h.name === b)) out.push({ who: a, line: `${a} and ${b} share the last of the bread without a word.` });
    for (const [a, b] of (this.rivals || []).slice(0, 1)) if (up.some((h) => h.name === a) && up.some((h) => h.name === b)) out.push({ who: a, line: pick(this, "rival", [`${a}: "That's ${((this.heroKills || {})[a] || 0)} to my name, ${b}." ${b} doesn't look up. "Count again."`, `${b} mutters that ${a} took their kill again. ${a} grins at the fire.`]) });
    if (this.light && this.light.kind === "torch" && this.light.left < 120) { const s = by(null, "torch"); out.push({ who: s.name, line: `${s.name}: "The torch won't see another floor like that one."` }); }
    if (out.length < 2) { const s = by(null, "rest"); out.push({ who: s.name, line: pick(this, "restline", [`${s.name} feeds the fire and watches the dark past it.`, `${s.name}: "Sleep. Somebody wake me if it's my watch."`, `${s.name} hums something from home, very quietly.`]) }); }
    return out.slice(0, 5); };
}
