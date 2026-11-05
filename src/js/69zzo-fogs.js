"use strict";
// The magical fogs (v76.0, UPGRADE_PLAN_61.md part 6): four fogs, scheduled with the weather (24f-events.js) but
// rarer, each six hours long, and they do not stop at the shaft - CM.fogNow answers the same on any floor. Each is a
// status on the whole party while it lasts:
//   orange, the ember fog  - spells cost half again as much and bite a fifth less
//   green, the rot fog     - a point of poison to each hero every ten minutes (never below one)
//   brown, the dun fog     - strength a fifth down
//   violet, the wild fog   - one cast in ten twists into another spell of the same kind
//   CM.fogNow(game) -> { kind, colour, name, word, strength, from, until, left } | null
//   CM.fogTick(game, minutes)   the comings and goings (said), the green fog's bite; wrapped into CM.tickClock
//   CM.wildSpell(game, h, id)   the violet fog's other spell for one cast (same target, a cost near it)
{ const F = CM.FOGS = { minutes: 360, odds: 0.25, spellCost: 1.5, spellBite: 0.8, strength: 0.8, poisonEvery: 10, wild: 0.1,
    kinds: { fogorange: { colour: [1.0, 0.58, 0.22], name: "an orange fog", word: "the ember fog", comes: "An orange fog rolls in, and the air crackles: magic comes dear and weak in it.", goes: "The orange fog thins and lifts, and the air is still again.", hud: "spells dear and weak" },
      foggreen: { colour: [0.45, 0.85, 0.35], name: "a green fog", word: "the rot fog", comes: "A green fog creeps up, sweet and foul: it is a poison, slow, to anyone who breathes it.", goes: "The green fog drains away into the ground.", hud: "a slow poison" },
      fogbrown: { colour: [0.62, 0.48, 0.3], name: "a brown fog", word: "the dun fog", comes: "A brown fog settles, heavy as dust: arms grow tired in it, and every weight is more.", goes: "The brown fog sinks and is gone, and the weight comes off.", hud: "strength down" },
      fogpurple: { colour: [0.7, 0.4, 0.95], name: "a violet fog", word: "the wild fog", comes: "A violet fog comes on, and the light in it moves wrong: magic will not do as it is told.", goes: "The violet fog frays into motes and is gone.", hud: "wild magic" } } };
  const rnd = () => (CM.wxRandom ? CM.wxRandom() : Math.random()), WX = CM.WX, KINDS = Object.keys(F.kinds);
  for (const k of KINDS) { if (!WX.kinds.includes(k)) WX.kinds.push(k); WX.word[k] = "mist"; WX.windSpeed[k] = 0.05; for (const s of Object.keys(WX.odds)) WX.odds[s][k] = F.odds; }
  // a fog's length is its own: the step's roll gives an event's, and this makes it six hours (the next's start follows)
  { const ws0 = CM.weatherStep; CM.weatherStep = (game) => { const W = ws0(game); if (W && W.cur && F.kinds[W.cur.kind] && W.cur.until - W.cur.from !== F.minutes) { const d = W.cur.from + F.minutes - W.cur.until; W.cur.until += d; if (W.next) { W.next.from += d; W.next.until += d; } } return W; }; }
  CM.fogNow = (game) => { if (!game || !game.ext) return null; const now = CM.weatherNow(game), K = F.kinds[now.kind]; if (!K) return null; return { kind: now.kind, colour: K.colour, name: K.name, word: K.word, hud: K.hud, strength: now.strength, from: now.from, until: now.until, left: Math.max(0, now.until - CM.clockOf(game)) }; };
  const state = (game) => game.ext("fog");
  CM.fogTick = (game, minutes = 1) => { if (!game || !game.ext || !(minutes > 0)) return; const E = state(game), now = CM.fogNow(game), kind = now ? now.kind : null;
    if (kind !== (E.kind || null)) { if (E.kind && F.kinds[E.kind]) game.say(F.kinds[E.kind].goes); if (kind) game.say(F.kinds[kind].comes); E.kind = kind; E.acc = 0; E.said = 0; for (const h of game.party || []) { h.fogStr = kind === "fogbrown"; CM.recompute(h); } }   // (brown: strength changes with it - the hero carries the mark, so the stat reads it anywhere)
    if (kind === "foggreen") { E.acc = (E.acc || 0) + minutes; let bit = 0; while (E.acc >= F.poisonEvery) { E.acc -= F.poisonEvery; for (const h of game.alive ? game.alive() : []) if (h.hp > 1) { h.hp -= 1; bit++; } } if (bit) { E.said = (E.said || 0) + 1; if (E.said % 6 === 1) game.say("The green fog is in everyone's lungs: a slow sickness, a point at a time."); } } };
  { const t0 = CM.tickClock; CM.tickClock = (game, minutes) => { t0(game, minutes); if (game && game.ext) CM.fogTick(game, minutes); }; }
  // the statuses in the rules
  { const hs0 = CM.heroStat; CM.heroStat = function (h, s) { const v = hs0.call(this, h, s); return s === "str" && h && h.fogStr ? Math.max(1, Math.floor(v * F.strength)) : v; }; }
  { const sc0 = CM.Game.prototype.spellCost; CM.Game.prototype.spellCost = function (h, a, power) { const c = sc0.call(this, h, a, power); return c && this.ext && state(this).kind === "fogorange" ? Math.ceil(c * F.spellCost) : c; }; }
  { const sm0 = CM.Game.prototype.spellMult; CM.Game.prototype.spellMult = function (h, id) { const m = sm0.call(this, h, id); return this.ext && state(this).kind === "fogorange" ? m * F.spellBite : m; }; }
  CM.wildSpell = (game, h, id) => { const a = CM.ABILITIES[id]; if (!a || !a.mp) return null; const pool = Object.keys(CM.ABILITIES).filter((k) => k !== id && CM.ABILITIES[k].mp && CM.ABILITIES[k].target === a.target && !CM.ABILITIES[k].once && Math.abs(CM.ABILITIES[k].mp - a.mp) <= 2); if (!pool.length) return null; return pool[Math.floor(rnd() * pool.length)]; };
  { const da0 = CM.Game.prototype.doAbility; CM.Game.prototype.doAbility = function (h, id, a, foe, ally, foes) { if (a && a.mp && this.ext && state(this).kind === "fogpurple" && rnd() < F.wild) { const w = CM.wildSpell(this, h, id); if (w) { this.say(`The violet fog takes the spell and twists it: ${a.name} comes out as ${CM.ABILITIES[w].name}.`); this.lastWild = { from: id, to: w }; return da0.call(this, h, w, CM.ABILITIES[w], foe, ally, foes); } } return da0.call(this, h, id, a, foe, ally, foes); }; }
}
