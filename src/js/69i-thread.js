"use strict";
// The tongue of the last bell (v18.8): one story through every part of the world. In the Undercroft's bell-yard the
// Bell-Founder's Boy swings a bell with no tongue - WE WILL LISTEN FOR IT, says the cross. The portals round the shaft
// open on what the Root dreams, and what it dreams is made of the city: so the tongue's makings are out there, one in
// each place - the Mage Tower, Haven, the island, Claudeita's cave, the Fortress, the pipe, Leshy's table, the Joker
// and the dungeon's own bell-ropes. Found (each by a deed there, counted whenever it's done), they go to the smith with
// a metal bar to be cast; and the tongue, taken down to the bell-yard, answers him. After that the Lich King hears it
// in the stone, every time, and rises a fifth short. Kept with the village, across runs. The window: 76zzzi-thread.js.
{ const TH = CM.THREAD = { forgeGold: 200, lichShare: 0.8, renown: 150, yard: -4 };
  const deepest = (g) => Math.max(0, ...((g.fame || []).map((e) => e.floor || 0)), ...((g.trail || []).map(([n]) => n || 0)));
  // [id, place, map place to go, what to do (the hint), done?, the page]
  TH.NOTES = [
    ["yard", "The Undercroft", "shaft", "Find the Bell-Founder's Boy, in the bell-yard under the Wood's third cave", (g) => (g.trail || []).some(([n]) => n === TH.yard) || ((g.tally || {}).guardians || []).includes("bell") || CM.undercroftDoorOpen(g),
      "He swings the bell and it makes no sound, and he swings it again. Round the cross: WE WILL LISTEN FOR IT. Whoever cut that was sure someone would come. The bell has a socket where the tongue should hang. It is the size of a man's fist, and empty, and polished by two hundred years of waiting."],
    ["ropes", "The dungeon", "shaft", "Go down past the fifteenth floor, or bring Brother Cael his bell", (g) => deepest(g) >= 15 || Boolean(g.story && g.story.bell),
      "Low in the shaft, grooves worn into the stone where the bell-ropes ran down from the hill - the town rang for the lower town, once, and the ropes hung all the way. They stop at a line cut level, clean. Someone above took a knife to them. A thread of the old rope is still in the groove: tarred, and good."],
    ["tower", "The Mage Tower", "yard", "Clear the Mage Tower's tenth floor", (g) => ((g.tower || {}).cleared || 0) >= 10,
      "A ledger on a lectern, in a mage's square hand: every portal in the Keep-yard, who opened it, and when. Each of them had stood at the shaft first and listened. The last line, underlined twice: THEY DO NOT OPEN ON OTHER PLACES. THEY OPEN ON WHAT IT DREAMS. He took the ledger's clasp off to use as a bookmark. It is bell-metal."],
    ["haven", "Haven (Claudeablo)", "haven", "Reach the eighth level under Haven's cathedral", (g) => Math.max(0, ...Object.values(((g.village || {}).ablo || {}).heroes || {}).map((p) => p.maxDepth || 0)) >= 8,
      "Every bell under the cathedral is cracked, and every one was cast with no tongue. The elder says their founder came from a hill a long way off: \"So the thing below would not know which of them answered.\" On the eighth level, a mould for a tongue, never poured. It fits a fist."],
    ["island", "The island (Claudecraft)", "gate", "Make a homestead on the island, or fell the Hollow Mason", (g) => Boolean(g.achievements && (g.achievements.homestead || g.achievements.mason)),
      "In the island's oldest ruin, the one stone nobody on the island laid: a bell cut into it, and under it, in the town's letters, CAST IT FROM WHAT THE DREAM IS MADE OF. The island is made of the hill's stone, and the hill's stone is the city's. A chip of it comes away in the hand, warm."],
    ["cave", "Claudeita's cave", "yard", "Undo one of the bosses of Claudeita's cave", (g) => (((g.village || {}).cave || {}).bosses || 0) >= 1,
      "Near the boss's lair the sand runs uphill, all of it the one way, toward where the shaft would be. Where it stops: bell-bronze, melted round a word somebody wanted kept. LISTEN. The sand goes round it, and leaves it alone."],
    ["fortress", "The Fortress", "yard", "Clear the Fortress's fifth floor", (g) => ((g.fort || {}).cleared || 0) >= 5,
      "Nailed to a door on the fifth floor, the Iron Marshal's standing orders. The ninth: NO BELLS. Under it, in a smaller hand: he means the one in the yard. Under that, smaller again: what yard. The nails are bell-bronze, pulled out of something and hammered straight."],
    ["pipe", "The pipe (Super Claude Bros)", "pipe", "Beat the Brass Warden at the end of 1-4", (g) => ((g.tally || {}).brosBest || 0) >= 4 || ((g.village || {}).thread || {}).brosWon,
      "The Brass Warden comes apart into plates, and on the inside of the chest plate, where no one would ever see it, a founder's stamp: O.V. Orrin Vale poured more than a box. The plate rings when it's dropped, a good note, the first true note anything down the pipe has made."],
    ["cabin", "Leshy's cabin", "cabin", "Win three games at Leshy's table", (g) => Object.keys(((g.village || {}).cards || {}).beaten || {}).length >= 3,
      "Leshy turns one card face up and doesn't play it: a bell, nothing under it. \"Everyone in this wood has a card,\" he says. \"This one is the town's. Nobody has played it in a long time.\" He pushes it over. It is not paper. It is thin, and cold, and it rings."],
    ["joker", "The Gilded Joker", "casino", "Reach Joker level 10", (g) => { try { return g.jkInfo ? g.jkInfo().level >= 10 : false; } catch (e) { return false; } },
      "The Joker, for once, doesn't make the joke. \"The house had a bell over the door. I sold its tongue the year the lower town went under. No one wanted to hear it.\" He slides over a pawn ticket, very old: ONE TONGUE, BELL, AT THE SMITH'S. \"Interest's been paid,\" he says. \"By someone. Every year.\""],
  ];
  TH.byId = Object.fromEntries(TH.NOTES.map((n) => [n[0], n]));
  TH.CHAPTERS = [
    ["The bell with no tongue", "The chronicler says the town keeps the Night of Bells and nobody remembers why. The lower town's cross remembers. Find what's at the bottom of the bell-yard."],
    ["What the dream is made of", "The portals round the shaft open on what the Root dreams, and it dreams in the city's stuff. The makings of a tongue are out there, one in every place it has dreamed, and in the shaft itself."],
    ["The casting", "At the smith's: all of it, a metal bar to hold it together, and the fire."],
    ["The answer", "Down to the bell-yard, with the tongue."],
    ["After", "The bell rang. In the stone, the Lich King hears it every time he rises."],
  ];
  const G = CM.Game.prototype;
  Object.assign(G, {
    thStore() { this.village = this.village || {}; const T = this.village.thread = this.village.thread || {}; T.notes = T.notes || {}; return T; },
    // what's newly found is noted (and said); returns the ids found now
    thSync() { const T = this.thStore(), got = [], names = []; for (const [id, place, , , done] of TH.NOTES) { if (T.notes[id]) continue; let ok = false; try { ok = Boolean(done(this)); } catch (e) { ok = false; } if (ok) { T.notes[id] = CM.today ? CM.today() : 1; got.push(id); names.push(place); } }
      if (got.length) this.say(`The last bell: something of it found - ${names.join(", ")}. (The Journal's "The last bell" page has it.)`);
      if (got.length) { this.emit && this.emit("threadnote", got); CM.store.set("village", this.village); } return got; },
    thInfo() { const T = this.thStore(), have = TH.NOTES.filter(([id]) => T.notes[id]).length, all = TH.NOTES.length;
      const chapter = T.rung ? 4 : T.forged ? 3 : have >= all ? 2 : T.notes.yard ? 1 : 0;
      return { chapter, have, all, forged: Boolean(T.forged), rung: Boolean(T.rung), notes: TH.NOTES.map(([id, place, go, hint, , page]) => ({ id, place, go, hint, page, got: Boolean(T.notes[id]) })) }; },
    thForgeWhy() { const I = this.thInfo(); if (I.forged) return "The tongue is cast."; if (I.have < I.all) return `The makings aren't all found: ${I.have} of ${I.all}.`; if (!this.floor || this.floor.number !== 0) return "The casting wants the smith's fire, in town.";
      if (!this.bag.some((x) => x.kind === "bar")) return "It wants a metal bar to hold it all together (from the island, or the smelter)."; if (this.gold < TH.forgeGold) return `The smith asks ${TH.forgeGold} gold for the fire and the night.`; return ""; },
    thForge() { const why = this.thForgeWhy(); if (why) return why; this.logAct && this.logAct("thForge"); this.bag.splice(this.bag.findIndex((x) => x.kind === "bar"), 1); this.gold -= TH.forgeGold; const T = this.thStore(); T.forged = true;
      this.sound && this.sound("slam"); this.say("The smith works all night and won't let anyone watch. In the morning there is a bell's tongue on the anvil, the size of a fist, and when the smith lifts it, it hums."); CM.store.set("village", this.village); this.emit && this.emit("change"); return ""; },
    thRingWhy() { const I = this.thInfo(); if (I.rung) return "It has rung."; if (!I.forged) return "There's no tongue to give him yet."; if (!this.floor || this.floor.number !== TH.yard) return "The Boy is in the bell-yard, the Undercroft's deepest street."; return ""; },
    thRing() { const why = this.thRingWhy(); if (why) return why; this.logAct && this.logAct("thRing"); const T = this.thStore(); T.rung = CM.today ? CM.today() : 1;
      this.village.renown = (this.village.renown || 0) + TH.renown; this.achieve && this.achieve("lastbell"); this.sound && this.sound("victory");
      this.say(`He takes the tongue in both hands as if it might be taken back, and hangs it, and swings. The bell rings. Up through the water and the stone and the hill, the first bell of the lower town anyone has heard in two hundred years; in the town above, the well-rope shivers. The Boy listens until it's quiet. Then he sits down by the cross, and stays sat. (+${TH.renown} renown)`);
      CM.store.set("village", this.village); this.emit && this.emit("change"); return ""; },
  });
  CM.ACHIEVEMENTS.lastbell = { name: "Answered", what: "Give the Bell-Founder's Boy his bell's tongue, from every place it was dreamed", title: "who Answered the Bell" };
  // counted wherever the party goes, and whenever the village is saved
  { const enter0 = G.enterFloor, save0 = G.saveVillage; G.enterFloor = function (...a) { const out = enter0.apply(this, a); if (this.village && !this.replaying) this.thSync(); return out; };
    G.saveVillage = function () { const out = save0.call(this); if (!this.thSyncing) { this.thSyncing = true; try { this.thSync(); } finally { this.thSyncing = false; } } return out; }; }
  // the pipe's Warden is gone when the hero comes home from 1-4: kept here too, as the tally is the run's
  { const lb0 = G.leaveBros; G.leaveBros = function (how) { const r = this.brosRun, won = r && r.li >= 3 && r.cleared; const out = lb0.call(this, how); if (won) { this.thStore().brosWon = true; this.thSync(); } return out; }; }
  // the bell rang: the Lich King rises a fifth short
  { const sc0 = G.startCombat; G.startCombat = function (...a) { const out = sc0.apply(this, a); const T = (this.village || {}).thread; if (T && T.rung && this.foes) { const b = this.foes.find((m) => m.boss); if (b && !b.belled) { b.belled = true; b.hp = Math.min(b.hp, Math.round(b.max * TH.lichShare)); this.say("Somewhere above, very far, a bell. He hears it in the stone, and something in him that was a man stops to listen. He rises a fifth short."); } } return out; }; }
  // on the goals page
  { const goals0 = G.wmGoals; if (goals0) G.wmGoals = function () { const out = goals0.call(this), I = this.thInfo(), C = TH.CHAPTERS[I.chapter];
    const next = I.rung ? null : I.forged ? { text: "Take the tongue down to the bell-yard (the Undercroft, under the Wood's third cave)", go: "shaft" } : I.have >= I.all ? { text: "Have the smith cast the tongue (a metal bar and 200 gold)", go: "smith" } : (() => { const n = I.notes.find((x) => !x.got); return { text: `${n.place}: ${n.hint}`, go: n.go }; })();
    out.splice(1, 0, { area: "The last bell", text: next ? `${C[0]} (${I.have} of ${I.all} found). Next - ${next.text}.` : "The bell has rung.", go: next ? next.go : null }); return out; }; }
}
