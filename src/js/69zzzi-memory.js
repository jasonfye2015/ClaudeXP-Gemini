"use strict";
// Memory, story and the town (UPGRADE_PLAN_65.md, release 6): the Chronicle Wall (murals of the party's own runs, read
// off the ledger - one panel a run; a rubbing of a panel is a trinket, +1 to the stat the party has least of), the Old
// Camp (a camp of a party of this browser's that came this way before: the cold fire, a note in the hand of one of
// the memorial's dead, and a short rest at the old fire, once), the Festival Hall (dressed on entering for the
// calendar's nearest festival - lanterns for the Night of Bells and Midwinter, bones for the Feast of the Dead,
// glowcaps for the Greening and the Sowing, candles otherwise - and on the festival's own day a chest's bar lifts),
// and the Smuggler's Drop (a cache behind a false door, three things of the town's trade with the smugglers' mark on
// them: worth double to the fence).
//   letters: [ a mural panel, ] the old fire, : a festival square (dressed on entering), ; the smugglers' cache.
{ CM.TRINKETS.rubbing = { name: "A rubbing of the wall", what: "+1 to the stat the party had least of, taken off the chronicle", props: { stats: {} } };
  CM.BASES[CM.TRINKETS.rubbing.name] = { id: CM.TRINKETS.rubbing.name, kind: "trinket", slot: "trinket", tier: Object.keys(CM.TRINKETS).length, group: "trinket", trinket: "rubbing" };
  const ME = CM.MEMORY_ROOMS = { restShare: 0.3, smuggledTimes: 2, festivalOf: (game) => { if (game && game.festival && CM.FESTIVALS[game.festival]) return game.festival; const m = new Date().getMonth(); return Object.keys(CM.FESTIVALS).find((id) => CM.FESTIVALS[id].month === m) || "bells"; } };
  const SP10 = [
    { name: "the Chronicle Wall", min: 6, line: "A long wall painted in panels, and the panels are you: every time a party of this house came down this shaft, who they were and how far they went and how it ended, in a painter's hand that was not told any of it.",
      rows: ["###########", "#[.[.[.[.[#", "#.........#", "#.........#", "#.........#", "#.........#", "#[.[.[.[.[#", "#####D#####"] },
    { name: "the Old Camp", min: 4, line: "A camp: the ring of stones and the ash in it cold, a tent gone to rags, a pot, and a note weighted with a stone. Someone of this house slept here, on this seed, and did not come back up.",
      rows: ["#########", "#.......#", "#...]...#", "#.......#", "#.......#", "#.......#", "#.......#", "###D#####"] },
    { name: "the Festival Hall", min: 3, max: 12, line: "A hall dressed for a feast - for which feast you can tell by the dressing, and the table in the middle is laid, and the chest at its head has its bar down. Come on the day, says the carving over the door, and the bar lifts.",
      rows: ["###########", "#:.:.:.:.:#", "#.........#", "#....9....#", "#.........#", "#.........#", "#.........#", "#:.:.:.:.:#", "#####D#####"], sealed: "barred till the festival's own day" },
    { name: "the Smuggler's Drop", min: 4, line: "A small room with nothing in it but a door in the far wall that does not open, and a mark cut low in the frame that someone in the Square would know. Behind it, a cache.",
      rows: ["#######", "#..;..#", "#.....#", "#.....#", "#.....#", "###D###"] },
  ];
  for (const r of SP10) { r.ownDice = true; if (!CM.SETPIECES.some((t) => t.name === r.name)) CM.SETPIECES.push(r); }
  const nth = (fl, type) => Object.values(fl.things || {}).filter((t) => t.type === type).length;
  CM.SETPIECE_LETTERS = Object.assign(CM.SETPIECE_LETTERS || {}, {
    "[": (fl, x, y, k) => { fl.things[k] = { type: "mural", n: nth(fl, "mural") }; },
    "]": (fl, x, y, k) => { fl.things[k] = { type: "oldcamp" }; },
    ":": (fl, x, y, k) => { fl.features[k] = { type: "festival", known: true }; },
    ";": (fl, x, y, k, T, R) => { const L = Math.max(1, CM.storyOf(fl.number)), items = [CM.makeItem(L, R, R.pick(["weapon", "armor", "helm"])), CM.makeItem(L, R, R.pick(["ring", "amulet", "shield"])), CM.makeItem(L, R, undefined, 2)]; for (const it of items) { it.smuggled = true; it.value = (it.value || 10) * ME.smuggledTimes; } fl.features[k] = { type: "falsedoor", niche: { type: "chest", gold: 0, items, trap: null, note: "the smugglers' cache" } }; },
  });
  const P = CM.Game.prototype;
  const runLine = (e) => { const who = (e.c || []).length ? e.c.join(", ") : "four", end = e.w ? "came up crowned" : e.b ? "went down to the bottom of the world" : e.e ? `went ${e.f} floors into the dark with no bottom` : `fell on floor ${e.f}`; return `${e.d || "A day"}: ${who} went down, ${end}.`; };
  const leastStat = (party) => { const stats = ["str", "dex", "con", "int", "wis", "luck"], sum = {}; for (const s of stats) sum[s] = party.reduce((n, h) => n + ((h.stats || {})[s] || 0), 0); return stats.sort((a, b) => sum[a] - sum[b])[0]; };
  // the Festival Hall is dressed on entering, for the festival nearest the day
  const dressFestival = (game, fl) => { if (!fl || !fl.rooms || fl.festivalDressed) return; const room = fl.rooms.find((r) => r.name === "the Festival Hall"); if (!room) return; const id = ME.festivalOf(game); fl.festivalDressed = id; const R = new CM.Random(CM.hashSeed(`${game.seed}:festival:${fl.number}`));
    for (const [k, f] of Object.entries(fl.features)) { if (f.type !== "festival") continue; const [x, y] = k.split(",").map(Number); if (fl.things[k]) continue;
      if (id === "bells" || id === "midwinter" || id === "forgefire") fl.things[k] = { type: "brazier", lit: true, festival: id }; else if (id === "dead" || id === "sexton") fl.things[k] = { type: "boneheap", festival: id }; else if (id === "greening" || id === "sowing" || id === "reaping" || id === "harvest") fl.things[k] = { type: "glowcap", at: 0, permanent: true, festival: id }; else fl.things[k] = { type: "brazier", lit: R.chance(0.7), festival: id }; void x; void y; }
    const chest = Object.values(fl.things).find((t) => t.type === "chest" && t.sealed === "the Festival Hall"); if (chest && game.festival === id) { delete chest.sealed; chest.note = `opened on ${CM.FESTIVALS[id].name}`; } };
  CM.dressFestivalHall = dressFestival;
  { const ef0 = P.enterFloor; P.enterFloor = function (number, how, at) { const out = ef0.call(this, number, how, at); if (this.floor && this.floor.number === number && number >= 1) dressFestival(this, this.floor); return out; }; }
  const LINES = { mural: (g, t) => { const e = (g.ledger || [])[t.n]; return e ? `A panel: ${runLine(e)} (Space to take a rubbing)` : "A panel with nothing painted on it yet: the wall is waiting for a run to paint."; }, oldcamp: (t) => (t.rested ? "The old fire, warm again a while, and cold again." : "The ring of stones, the cold ash, the pot, the note under its stone. (Space to read it and rest a while)") };
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a); const fl = this.floor; if (fl && this.mode === "explore" && !this.perch && fl.things) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`; for (const k of [here, ahead]) { const t = fl.things[k]; if (t && LINES[t.type]) { this.say(LINES[t.type](this, t)); break; } } } return out; }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`;
        for (const k of [here, ahead]) { const t = fl.things[k]; if (!t) continue;
          if (t.type === "mural") { const e = (this.ledger || [])[t.n]; if (!e) { this.say("A panel with nothing painted on it yet."); return true; } const E = this.ext("chronicle"); if (E[fl.number]) { this.say(`${runLine(e)} The rubbing is taken; one is enough.`); return true; } E[fl.number] = true; const stat = leastStat(this.party), it = CM.trinket("rubbing"); it.props = { stats: { [stat]: 1 } }; it.name = `A rubbing of the wall (${stat})`; this.bag.push(it); this.sound("coin"); this.say(`${runLine(e)} You take a rubbing of the panel, and it keeps something of the hand that painted it: +1 ${stat}, for whoever carries it.`); this.emit("change"); return true; }
          if (t.type === "oldcamp") { if (t.rested) { this.say("The old fire, cold again."); return true; } t.rested = true; const dead = (this.memorial || []).find((m) => m.seed === this.seed) || (this.memorial || [])[0]; let healed = 0; for (const h of this.alive()) { const n = Math.min(h.max - h.hp, Math.ceil(h.max * ME.restShare)); if (n > 0) { h.hp += n; healed++; } if (h.status) delete h.status.poison; } this.sound("heal"); this.clock = (this.clock || 0) + 60;
            this.say(`${dead ? `The note, in ${dead.name}'s hand: "${dead.epitaph || "We camped here. Go on; we did not."}"` : "The note has gone to pulp, and the hand that wrote it is not one you know."} You light the old fire and sit an hour at it${healed ? ", and the party mends a little" : ""}.`); this.emit("change"); return true; } } }
      return u0.apply(this, a); }; }
}
