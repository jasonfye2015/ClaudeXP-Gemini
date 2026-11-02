"use strict";
// Letters home (v34.3, UPGRADE_PLAN_29.md): a trip down is kept - the deepest floor, the slain, the guardians, the finds,
// who fell, the scars taken - and when the party comes up into the town again, every hero standing writes a short letter
// home: to whom, by where they come from; what they saw, in their own way, by their calling; who they fought beside.
// The letters are kept in the village, the last eighty, for the Journal's Letters page (76zzzzzze-letters.js).
//   game.trip() -> the trip so far;  game.writeLetters() -> [letter];  game.letters() -> [{hero, cls, date, day, text}]
{ const G = CM.Game.prototype, TO = { caerduin: "Mother", dwarffriend: "Old Brannoc, at the forge", east: "my sister, across the river", order: "the Prior", lowertown: "whoever's minding the dock-tavern", nobody: "whoever finds this" };
  const VOICE = { Knight: ["I held the line", "the shield took most of it"], Rogue: ["I kept to the shadows", "nobody saw me coming, which is how I like it"], Cleric: ["I prayed over every one of them", "the light held"],
    Mage: ["the fire answered when I called it", "I am learning more down there than I ever did at the college"], Ranger: ["I kept the arrows dry", "I counted their tracks"], Paladin: ["I kept my oath", "the light walked with us"] };
  const trip = (g) => { const T = g.ext("trip"); T.deepest = T.deepest || 0; T.kills = T.kills || 0; T.guardians = T.guardians || []; T.finds = T.finds || []; T.fell = T.fell || []; T.scars = T.scars || []; return T; };
  G.trip = function () { return trip(this); };
  G.letters = function () { const V = this.vext("letters"); V.list = V.list || []; return V.list; };
  const wf0 = G.wonFight; G.wonFight = function (...a) { const n = (this.foes || []).filter((m) => !m.fled).length, out = wf0.apply(this, a); trip(this).kills += n; return out; };
  const sg0 = G.slayGuardian; G.slayGuardian = function (m) { const out = sg0.call(this, m); if (m && !m.echo && CM.GUARDIANS[m.guardian]) trip(this).guardians.push(CM.GUARDIANS[m.guardian].name); return out; };
  const gs0 = G.giveScar; if (gs0) G.giveScar = function (h, why) { const S = gs0.call(this, h, why); if (S) trip(this).scars.push(`${h.name}|${S.where}|${why.by}`); return S; };
  const gain0 = G.gain; G.gain = function (items, how) { if (Array.isArray(items) && this.tally) for (const it of items) if (it && ["rare", "unique", "relic"].includes(CM.rarityOf(Object.assign({}, it, { unknown: false })))) { const F = trip(this).finds; if (F.length < 4) F.push(it.unknown ? CM.baseName(it) : it.name); } return gain0.call(this, items, how); };
  const pick = (g, salt, list) => list[CM.hashSeed(`${g.seed}:letter:${salt}`) % list.length];
  G.letterFor = function (h, T) { const to = TO[h.origin] || pick(this, `${h.name}:to`, ["Mother", "Father", "my brother", "whoever reads this", "the old crowd at the Lantern"]), v = VOICE[h.cls] || ["I did my part", "we came through it"];
    const friend = this.bondOf && this.bondOf(h), rival = this.rivalOf && this.rivalOf(h), mine = T.scars.find((s) => s.startsWith(`${h.name}|`));
    const s = [/^(the|whoever|my) /.test(to) ? `To ${to},` : `Dear ${to},`];
    s.push(T.deepest ? `We went down as far as the ${CM.ordinal ? CM.ordinal(T.deepest) : T.deepest + "th"} floor${CM.themeFor && T.deepest > 0 ? `, into ${CM.themeFor(T.deepest).name.replace(/^The /, "the ")}` : ""}.` : "We didn't get far this time.");
    if (T.guardians.length) s.push(pick(this, `${h.name}:g`, [`We put down ${T.guardians[0]}. I still can't quite believe it.`, `${T.guardians[0]} is dead. I was there. ${v[0][0].toUpperCase() + v[0].slice(1)}.`]));
    else if (T.kills > 20) s.push(`There were more of them than I'd like to write down - ${T.kills}, the purse says. ${v[1][0].toUpperCase() + v[1].slice(1)}.`); else s.push(`${v[0][0].toUpperCase() + v[0].slice(1)}, and ${v[1]}.`);
    if (T.finds.length) s.push(pick(this, `${h.name}:f`, [`We came home with ${T.finds[0]}, which I'm told is worth something.`, `Somebody found ${T.finds[0]}. I'll tell you about it when I'm home.`]));
    if (mine) s.push(`Don't fret about the new scar ${mine.split("|")[1]}. It looks worse than it is.`);
    const lost = T.fell.filter((n) => n !== h.name)[0]; if (lost) s.push(`We lost ${lost} down there. I don't want to write more about it.`);
    if (friend) s.push(`${friend.name} is still beside me. Of all of them, ${friend.name}.`); else if (rival) s.push(`${rival.name} thinks they're keeping a better score than me. They aren't.`);
    s.push(pick(this, `${h.name}:end`, ["Back down soon.", "Keep the lamp lit.", "More when there's more to tell.", "Your loving, as ever,"]) + ` - ${h.name}`);
    return s.join(" "); };
  G.writeLetters = function () { const T = trip(this), out = []; if (!T.deepest) return out; const day = CM.dayOf ? CM.dayOf(this) : 0, L = this.letters();
    const keep = !this.replaying && !this.film;   /* (a replay or a film says the same, and keeps nothing) */
    for (const h of this.party) if (h.hp > 0) { const ltr = { hero: h.name, cls: h.cls, date: CM.today ? CM.today() : "", day, text: this.letterFor(h, T) }; if (keep) L.push(ltr); out.push(ltr); }
    while (L.length > 80) L.shift(); if (keep) this.saveVillage && this.saveVillage(); this.ext().trip = null; trip(this);
    if (out.length) this.say(`Home again: ${out.length === 1 ? `${out[0].hero} writes a letter` : `${out.map((l) => l.hero).join(", ").replace(/, ([^,]*)$/, " and $1")} write letters`} home (the Journal keeps them).`); return out; };
  const em0 = G.emit; G.emit = function (ev, ...a) {
    if (ev === "floor" && this.floor && this.tally) { const T = trip(this), n = this.floor.number;
      if (n > 0 && n < 1000) T.deepest = Math.max(T.deepest, n);
      if (n === 0 && T.deepest > 0) this.writeLetters(); }
    if (ev === "change" && this.party && this.tally) { const T = trip(this); for (const h of this.party) if (h.hp <= 0 && !T.fell.includes(h.name)) T.fell.push(h.name); }
    return em0.call(this, ev, ...a); };
}
