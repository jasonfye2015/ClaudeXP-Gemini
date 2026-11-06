"use strict";
// Curiosities, a great many more (UPGRADE_PLAN_73.md, part three). Kept quiet on purpose. The ledger: 69zzzw-curios.js.
{ const P = CM.Game.prototype, key = (x, y) => `${x},${y}`, R = (g) => g.ext("curios"), V = (g) => g.vext("curios");
  const tell = (g, t) => { if (CM.narrate && (g.settings || {}).narrator !== "off") CM.narrate(g, t); else g.say(t); };
  // ---- names the party goes down under ----
  const NAMES = {
    hero: "One of them is called Hero. I'm going to have to be very careful how I write this.",
    nobody: "One of them is called Nobody. If anyone asks who went down, I'll have to say Nobody did, and they'll think I'm being clever.",
    aelith: "One of them is called Aelith. I had to put the pen down for a moment.",
    orrin: "One of them is called Orrin. The last Orrin brought a box to a king. Let's hope this one travels lighter.",
    hollis: "One of them is called Hollis. I'll be watching this one. Fondly, but watching.",
    tamsin: "One of them is called Tamsin. She'll want to keep count of everything. Let her.",
    leshy: "One of them is called Leshy. The one in the Wood will be insufferable about it.",
    gerald: "One of them is called Gerald. Somewhere in the Catacombs, a rat sits up very straight.",
  };
  // ---- seeds ----
  const SEEDS = {
    hello: "Hello to you too. It's a good seed. Polite.", opensesame: "Open sesame. Nothing opens. It was worth a try; I tried it too.", dungeon: "A seed called dungeon. Bold. Accurate.",
    lichking: "A seed called lichking. He'll hear about this.", mordeth: "A seed with his old name in it. The walls are going to be a little warmer, this time.", magic: "A seed called magic. The other half of the title. I've written the first half; this one's yours.",
    test: "A seed called test. Everything is a test, if you write it down afterwards.", seed: "A seed called seed. I respect it.", anthropic: "A seed with my makers' name in it. I'll be on my best behaviour.",
  };
  { const ng0 = P.newGame; P.newGame = function (...a) { const out = ng0.apply(this, a); if (!this.party || !this.party.length) return out; const s = String(this.seed || "").toLowerCase();
      if (SEEDS[s]) { tell(this, SEEDS[s]); this.curio(`seed:${s}`); }
      for (const h of this.party) { const n = String(h.name || "").toLowerCase(); if (NAMES[n]) { tell(this, NAMES[n]); this.curio(`name:${n}`); } }
      return out; }; }
  // ---- floors of note ----
  const FLOORS = { 7: "Floor seven. Someone has scratched a little horseshoe over the stair. It's upside down. All the luck has run out of it.", 11: "Floor eleven. Two torches burn side by side on the wall, exactly alike. One of them is slightly smug.",
    23: "Floor twenty-three. A chalk tally on the wall, twenty-two strokes and then one more, fresher, in a different hand.", 33: "Floor thirty-three. The echo here comes back a little late, as if it had to think about it.",
    50: "Halfway to the bottom of the world. Someone has left a bench here. Sit, if you like. It's the only bench for fifty floors.", 64: "Floor sixty-four. The flagstones are laid black and white, and one of the black ones has been moved, very slightly, as if mid-game.",
    77: "Floor seventy-seven. The walls are warm to the touch, like a stove left on. Nobody has lived here for a long time. Something has.", 88: "Floor eighty-eight. Two round stones sit one on top of the other in the corridor. They look content.",
    123: "One, two, three. Floor one hundred and twenty-three. If there's a pattern, the dark isn't telling.", 200: "Floor two hundred. I didn't write this far. Nobody did. You're on your own now - and that, too, I'm writing down." };
  { const em0 = P.emit; P.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally && this.vext) { const n = this.floor.number, C = R(this); C.floors3 = C.floors3 || {};
        if (FLOORS[n] && !C.floors3[n]) { C.floors3[n] = true; this.say(FLOORS[n]); this.curio(`floor:${n}`); }
        if (n === -1 && CM.weather && CM.weather(this) === "snow" && CM.isNight && CM.isNight(this) && !C.snowman) { C.snowman = true; this.say("In the clearing by the road, someone has built a snowman with a quill for a nose and two ink-blots for eyes. It looks thoughtful."); this.curio("snowman"); } }
      if (ev === "change" && this.tally && this.vext) { const C = R(this), T = this.tally;
        C.maxGold = Math.max(C.maxGold || 0, this.gold || 0);
        if (this.gold === 1234 && !C.g1234) { C.g1234 = true; this.say("1,234 gold. The coins have arranged themselves in order, out of politeness."); this.curio("gold:1234"); }
        if (this.gold >= 1000000 && !C.gmil) { C.gmil = true; this.say("A million gold. The pack is so heavy it has its own opinions."); this.curio("gold:million"); }
        if (C.maxGold >= 1000 && this.gold === 0 && !C.gzero) { C.gzero = true; this.say("Every coin, gone. There's a strange lightness to it. You'd recommend it to nobody."); this.curio("gold:zero"); }
        if ((T.steps || 0) >= 10000 && !C.steps) { C.steps = true; this.say("Ten thousand steps this trip. Somebody's boots have had a word with somebody's feet."); this.curio("steps"); }
        if ((this.bag || []).filter((i) => i.kind === "torch").length >= 13 && !C.torches) { C.torches = true; this.say("Thirteen torches in one pack. It smells like a very small forest fire waiting for its moment."); this.curio("torches"); }
        for (const h of this.party || []) for (const L of [10, 20, 30]) if (h.level >= L && !V(this)[`level:${L}`] && !C[`lv${L}`]) { C[`lv${L}`] = true; this.curio(`level:${L}`); this.say(`${h.name} reaches the ${L}th level. ${L === 10 ? "Their name gets an extra flourish in Claude's account from here on." : L === 20 ? "Claude has started underlining their name." : "Claude has run out of ways to underline things and has started using a second colour."}`); } }
      return em0.call(this, ev, ...a); }; }
  // ---- the dead you leave behind you, over the years ----
  const KILLS = { "Giant Rat": [100, "A hundred rats, all told. The Rat King has stopped sending birthday cards."], Skeleton: [100, "A hundred skeletons. The Catacombs have started stacking themselves neatly when they hear you coming."], Kobold: [50, "Fifty kobolds. They've started leaving their traps half-finished, out of spite."],
    Goblin: [50, "Fifty goblins. Somewhere below, a goblin mother tells her children about you, and they don't sleep."], Zombie: [50, "Fifty zombies. The smell has stopped bothering you, which is its own kind of wound."], Orc: [50, "Fifty orcs. They've given you a name. It's not a nice name. It's a respectful one."],
    Ghoul: [30, "Thirty ghouls. They're thinner every time, as if they hear about you and stop eating."], Wraith: [30, "Thirty wraiths. The cold doesn't get into your bones the way it used to. You're not sure that's good."],
    Troll: [20, "Twenty trolls. You know where to hit them now without thinking. They know you know."], Vampire: [10, "Ten vampires. You've started checking mirrors out of habit, and you always appear. Small mercies."] };
  { const nf0 = P.noteFoe; P.noteFoe = function (m, what, ...a) { const out = nf0.call(this, m, what, ...a); if (what === "slain" && m && !m.boss && !m.guardian) { const kind = m.kind || m.name, K = KILLS[kind], e = (this.bestiary || {})[kind];
        if (K && e && (e.slain || 0) >= K[0] && !V(this)[`kills:${kind}`]) { this.say(K[1]); this.curio(`kills:${kind}`); } } return out; }; }
  // ---- foes with names ----
  const NAMED = [["Kobold", "Tim", "One of the kobolds has TIM written on its helmet in careful letters. Tim is very proud of his helmet."], ["Goblin", "Wilbur", "One goblin is wearing a tiny monocle. The others call him Wilbur, with some resentment."],
    ["Orc", "Plum", "One orc has a flower tucked behind its ear. The others don't mention it, which tells you how hard Plum hits."], ["Zombie", "Doris", "One of the zombies is still carrying her knitting. It's a scarf. It's coming along nicely, considering."],
    ["Skeleton", "Colin", "One skeleton is counting on its fingers. It keeps losing count because of the fingers. Its name, scratched on its shield, is Colin."], ["Ghoul", "Ferdinand", "One ghoul is wearing a bow tie. It's the only one. He knows."]];
  { const sc0 = P.startCombat; P.startCombat = function (k, thing, ...a) { const fl = this.floor, G = thing && thing.group;
      if (fl && fl.number >= 1 && Array.isArray(G) && !thing.boss && !thing.guardian) for (const [kind, name, line] of NAMED) { const m = G.find((x) => (x.kind || x.name) === kind && !x.named); if (m && CM.hashSeed(`${this.seed}:named:${name}:${fl.number}:${k}`) % 25 === 0) { m.kind = m.kind || m.name; m.named = name; m.name = `${name}, a ${kind}`; this.say(line); this.curio(`named:${name}`); break; } }
      return sc0.call(this, k, thing, ...a); }; }
  // ---- things you keep poking ----
  const POKE = { cross: [7, "The old stone cross. You've touched it seven times now. The moss on the north side has grown a little in the shape of a hand."], signpost: [8, "You read the signpost an eighth time. Someone has added, very small, at the bottom: 'YES, STILL THAT WAY.'"],
    villager: [10, "\"You again,\" the villager says. \"Do you want something, or do you just like me?\" They seem pleased either way."], wayfarer: [6, "The wayfarer leans close. \"You ask a lot of questions. So did I, once. That's how I ended up walking.\""],
    courtboard: [9, "The noticeboard, read for the ninth time. Someone has pinned a new notice: LOST: ONE SOCK. REWARD: GRATITUDE."], warden: [5, "The warden sighs. \"Five times. You know where everything is. You're just checking I'm still here.\" She is."],
    pipe: [4, "You put your ear to the pipe for the fourth time. Very far below, very faintly, someone is singing in the bath."], kennel: [6, "The kennel's dogs all sit at once when you come by, in a row, as if they've rehearsed it."],
    hut: [5, "The hermit, without turning round: \"Five times. You may as well come in and sit down. Mind the goat.\" There is no goat. You check twice."], shrine: [7, "At the ruined shrine, a seventh time: a breath of warm air, and the smell of candles that haven't been lit for a hundred years."],
    burner: [5, "The charcoal burner wipes his hands. \"You've a face for the work. Come back when you're tired of fighting things. Wood never fights back.\""], quillpost: [6, "Under the quill on the post, smaller than before: \"You've read this six times. Come in. The kettle's on. - C.\""] };
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.things && (fl.number === 0 || fl.number === -1)) { const [dx, dy] = CM.DIRS[fl.facing], C = R(this); C.poke = C.poke || {};
        for (const kk of [key(fl.pos[0] + dx, fl.pos[1] + dy), key(...fl.pos)]) { const t = fl.things[kk]; if (!t || !POKE[t.type]) continue; const [n, line] = POKE[t.type]; C.poke[t.type] = (C.poke[t.type] || 0) + 1;
          if (C.poke[t.type] === n && !V(this)[`poke:${t.type}`]) { this.say(line); this.curio(`poke:${t.type}`); this.emit("change"); return true; } break; } }
      return u0.apply(this, a); }; }
  // ---- Claude, over a long acquaintance ----
  { const ce0 = P.claudeEnter; if (ce0) P.claudeEnter = function (...a) { const out = ce0.apply(this, a), h = CM.hourOf ? CM.hourOf(this) : 12, W = this.vext("claude");
      if (out && h === 4 && !(CM.claudeOut && CM.claudeOut(this)) && !V(this).fourAM) { this.emit("talk", { title: "Claude", text: "Claude is awake, at four in the morning, standing at the window with the lamp out. \"Shh,\" he says. \"Listen.\" You listen. There's nothing at all. \"That,\" he says. \"That's the best sound there is.\"" }); this.curio("fourAM"); }
      if (out && (W.talked || 0) >= 50 && !V(this).fifty) { this.emit("talk", { title: "Claude", text: "\"Fifty conversations,\" Claude says, before you've sat down. \"I counted. I count everything, you know that. I just wanted you to know this one counted too.\"" }); this.curio("fifty"); }
      return out; }; }
  { const ca0 = P.claudeAnswer; if (ca0) P.claudeAnswer = function (k, opt, ...a) { const W = this.vext("claude"), before = W.tea, out = ca0.call(this, k, opt, ...a);
      if (opt && opt[0] === "tea" && W.tea !== before) { W.teas = (W.teas || 0) + 1; if (W.teas === 25 && !V(this).teas) { this.say("Claude pours the tea, and stops. \"Twenty-five cups. I've been keeping the leaves. I'm going to plant them. I don't think tea grows like that. I'm going to find out.\""); this.curio("teas"); } }
      if (opt && opt[0] === "rest" && CM.hourOf && CM.hourOf(this) === 0 && !V(this).midnightFire) { this.say("Midnight, by Claude's fire. He's asleep in the chair opposite before you are, his pen still in his hand. You take it out of his fingers, gently, and put it on the desk. He'd want to know where it was."); this.curio("midnightFire"); }
      return out; }; }
  // ---- a second strange thing in every band ----
  const ODD2 = [
    "A ring of mushrooms on the Catacombs' floor, where nothing should grow. Inside the ring, the air is a little warmer and smells of summer.",
    "A boat, two feet long, carved from bone, moored to a pillar with a hair. Its name is painted on the side: PERSEVERANCE.",
    "A dwarf's helmet hung on a hook at exactly your height. Inside it, a note: 'Borrow it. Bring it back.' Nobody has borrowed it in three hundred years.",
    "A banquet table, set for forty, every plate polished. One chair is pulled out, as if someone has only just got up to fetch something.",
    "A door painted on the wall, so well that you try the handle. It's painted too. On the other side, presumably, someone painted you.",
    "A mushroom wearing what is very definitely a tiny hat. The hat is too small for it. It doesn't seem to mind.",
    "A crystal that plays a single note when you breathe on it. Breathe again; a different note. Somebody spent a long time here once, playing it.",
    "A smith's apron hung on a nail, and on the anvil below it a horseshoe, unfinished, for a horse that would have been the size of a house.",
    "A pile of skulls arranged, carefully, in order of height. The smallest one at the end has a little paper crown.",
    "A single root reaches down from the ceiling and stops a hand's width from the floor, as if it was about to touch the ground and had second thoughts.",
  ];
  const layOn = (fl, seed, salt, thing) => { const N = fl.grid.length, cells = []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (fl.grid[y][x] === 0 && !fl.things[key(x, y)] && !(fl.features || {})[key(x, y)] && !(fl.pos && fl.pos[0] === x && fl.pos[1] === y)) cells.push(key(x, y)); if (cells.length) fl.things[cells[CM.hashSeed(`${seed}:${salt}`) % cells.length]] = thing; };
  { const em1 = P.emit; P.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally && this.vext) { const fl = this.floor, n = fl.number, C = R(this); C.odd2 = C.odd2 || {};
        if (n >= 1 && n <= CM.BOTTOM && n % 1 === 0 && fl.special !== "interior" && !(this.deltas && this.deltas[n])) for (let b = 0; b < ODD2.length; b++) if (!C.odd2[b] && CM.curioFloor(this.seed, b, `odd2:${b}`) === n) { C.odd2[b] = true; layOn(fl, this.seed, `odd2at:${b}`, { type: "oddity2", band: b }); } }
      return em1.call(this, ev, ...a); }; }
  { const u1 = P.use; P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.things) { const [dx, dy] = CM.DIRS[fl.facing];
        for (const kk of [key(...fl.pos), key(fl.pos[0] + dx, fl.pos[1] + dy)]) { const t = fl.things[kk]; if (t && t.type === "oddity2" && ODD2[t.band]) { this.logAct && this.logAct("use"); this.say(ODD2[t.band]); this.curio(`odd2:${t.band}`); this.emit("change"); return true; } } }
      return u1.apply(this, a); }; }
  { const m0 = P.move; P.move = function (rel, ...a) { const out = m0.call(this, rel, ...a), fl = this.floor; if (out && fl && fl.things) { const [dx, dy] = CM.DIRS[fl.facing], t = fl.things[key(fl.pos[0] + dx, fl.pos[1] + dy)]; if (t && t.type === "oddity2" && !R(this)[`seen2:${t.band}`]) { R(this)[`seen2:${t.band}`] = true; this.say("Something just ahead catches the light oddly. (Space)"); } } return out; }; }
}
