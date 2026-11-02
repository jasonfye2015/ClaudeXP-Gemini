"use strict";
// Townsfolk who remember (v36.2, UPGRADE_PLAN_31.md): the six residents of the town know what the party has done, and say
// so - the first time each is passed in a day (the window walks them, 76zzzzy-townsfolk.js, and tells the rules when
// the party is beside one: game.greet(who)). Each greeting is by the deeds: this run's depth and guardians, the Hall of
// Fame's best and the last run's end, the trophies, the legends, the feats. One time in three a lead comes with it -
// a den the hound could find, the trader due tomorrow, the season's trial still open, the still's pages, the games.
//   CM.RESIDENT_WHO; game.greetLine(who); game.gossipLead(); game.greet(who) -> the lines said, or null
{ const RW = CM.RESIDENT_WHO = { smith: "Hesta, the smith", merchant: "The merchant", library: "The librarian", priest: "The priest", farm: "The farmer", tavern: "The landlady" };
  const G = CM.Game.prototype, pick = (g, salt, list) => list[CM.hashSeed(`${g.seed}:greet:${salt}:${CM.dayOf ? CM.dayOf(g) : 0}`) % list.length];
  G.greetLine = function (who) { const name = RW[who] || "Someone", fame = this.fame || [], best = fame.reduce((m, e) => Math.max(m, e.floor || 0), 0), last = fame[0], T = this.tally || {};
    const deep = this.deepestReached ? this.deepestReached() : 0, guards = (T.guardians || []).length, trophies = Object.keys(this.trophies || {}).length, legends = this.legends ? this.legends().length : 0, feats = Object.keys(this.achievements || {}).length;
    const opts = [];
    if (guards) opts.push(`"${CM.GUARDIANS[T.guardians[T.guardians.length - 1]] ? CM.GUARDIANS[T.guardians[T.guardians.length - 1]].name : "One of them"} is dead? The whole lane's talking about it."`);
    if (deep >= 10) opts.push(`"Floor ${deep}, they're saying. Is it true what's down there?"`);
    else if (deep >= 1) opts.push(`"Back from floor ${deep}, then? You've still got the dust of it on you."`);
    if (last && !last.won && fame.length > 1) opts.push(`"I heard about the last lot - floor ${last.floor}. I'm glad it's you walking past and not their names on the stone."`);
    if (best >= 20) opts.push(`"The ones who went past the king's own floor. I tell my cousins I know you."`);
    if (trophies >= 3) opts.push(`"${trophies} of the keepers' trophies on one wall. Mind you don't run out of wall."`);
    if (legends) opts.push(`"Saw ${this.legends()[legends - 1].name} on Legends' Row this morning, watering the roses. Doesn't seem right, somehow."`);
    if (feats >= 15) opts.push(`"You'll want a bigger plaque-room at the Tower, the way you're going."`);
    if (!opts.length) opts.push(`"Off down the shaft again? Bring yourselves back up, that's all I ask."`, `"New faces. Well - every face is new, down there."`);
    return `${name}: ${pick(this, `${who}:line`, opts)}`; };
  G.gossipLead = function () { const leads = [];
    const dens = this.dens ? this.dens().filter((d) => !d.cleared) : []; if (dens.length) leads.push(`a hunter saw ${dens.length === 1 ? `a ${dens[0].kind.toLowerCase()}'s den` : `${dens.length} dens`} in the Deep Wood, under the roots`);
    else if (this.petName && this.petName("dog") && !(this.hasTrick && this.hasTrick("track"))) leads.push("a hound that knew how to track could find where the fleeing ones go to ground - the farm teaches it");
    if (CM.TRADERS && CM.tradersOn) { const d = ((CM.dayOf(this) + 1) % 7 + 7) % 7, due = Object.keys(CM.TRADERS).filter((id) => (d === CM.MARKET_DAY ? true : CM.TRADERS[id].day === d)); if (due.length) leads.push(`${due.length > 1 ? "it's market day tomorrow" : `${CM.TRADERS[due[0]].name} is in the Square tomorrow`}`); }
    if (this.trialDone && !this.trialDone() && CM.SEASON_TRIALS) leads.push(`nobody's done ${CM.SEASON_TRIALS[CM.season(this)].name} this ${CM.season(this)} - ${CM.SEASON_TRIALS[CM.season(this)].what}`);
    if (CM.STILLBOOK && this.stillKnown) { const left = Object.keys(CM.STILLBOOK).length - Object.keys(this.stillKnown()).length; if (left > 0) leads.push(`there are still recipes for the fields' still lying about down there - ${left} pages, the alchemist reckons`); }
    if (CM.festival && CM.festival(this) && this.festRecord && Object.keys(this.festRecord().played).length < 3) leads.push("the festival games are still running in the Square");
    return leads.length ? pick(this, "lead", leads) : null; };
  G.greet = function (who) { if (!RW[who] || !this.floor || this.floor.number !== 0) return null; const E = this.ext("greeted"), day = CM.dayOf ? CM.dayOf(this) : 0; if (E[who] === day) return null; E[who] = day;
    const out = [this.greetLine(who)]; const lead = CM.hashSeed(`${this.seed}:lead:${who}:${day}`) % 3 === 0 ? this.gossipLead() : null; if (lead) out.push(`${RW[who]} lowers their voice: ${lead}.`);
    for (const l of out) this.say(l); return out; };
}
