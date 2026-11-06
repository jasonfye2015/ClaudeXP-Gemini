"use strict";
// The trials, the first five (UPGRADE_PLAN_65.md, release 3): rooms with a rule to learn. The Hourglass Room (turn the
// glass and its chests open while the sand runs - twelve steps - and seal again when it stops; the glass turns once
// a day), the Riddle Gallery (three statues across the hall, each a riddle door of the game's own riddles; a wrong
// answer wakes the statue - a Gargoyle, once each), the Pendulum Hall (a hall one square wide between two pits, blades
// swinging on a beat: step on the off-beat and pass, step on the beat and take a bounded cut and be thrown back a
// square; Space waits a beat), the Dark Room (no torch burns in it - a light spell or a carried glow shows the way;
// the exit is on the far side; shadows sleep in the middle, walked round), and the Frozen Pond (ice: a step keeps
// going till a wall, a thing or dry stone stops it; chests on islands of stone, reached by sliding right).
//   letters: I the hourglass, ? a statue (a riddle door), J a blade, Z the shadows asleep, O ice; 9 a sealed chest.
{ const TR = CM.TRIALS = { sandSteps: 12, bladeCut: 3, slideMost: 12, gazeOnce: true };
  const SP7 = [
    { name: "the Hourglass Room", min: 7, line: "A glass the height of a man in a brass frame in the middle of the room, all its sand in the bottom bulb, and four chests against the walls with their lids held down by bars. The frame has a handle, and the glass turns.",
      rows: ["#########", "#9.....9#", "#.......#", "#.......#", "#...I...#", "#.......#", "#.......#", "#9.....9#", "###D#####"], sealed: "held by a bar that lifts while the sand runs" },
    { name: "the Riddle Gallery", min: 9, line: "A gallery crossed by three walls, and in each wall a door with a statue standing in it - a hooded shape with a hand up. The hand says: wait. The mouth, when you come near, says more.",
      rows: ["#######", "#..c..#", "#.....#", "###?###", "#.....#", "###?###", "#.....#", "###?###", "#.....#", "#.....#", "###D###"], chests: { c: { note: "beyond the third statue" } } },
    { name: "the Pendulum Hall", min: 10, line: "A hall one flag wide between two pits, and across it, on a beat you can count, blades on chains sweep the width of the way and back. There is a chest at the far end, and a rhythm to learn.",
      rows: ["#####", "#_c_#", "#_._#", "#_J_#", "#_._#", "#_J_#", "#_._#", "#_J_#", "#_._#", "#_J_#", "#_._#", "#_J_#", "#_._#", "#_._#", "#D###"], chests: { c: { note: "past the blades" } } },
    { name: "the Dark Room", min: 8, line: "The torch goes out at the door, and will not take again while you stand in here. It is not a draught. The dark has a shape to it, and the shape is asleep in the middle, and the way on is the far wall.",
      rows: ["###D#######", "#.........#", "#.........#", "#.........#", "#.........#", "#....Z....#", "#.........#", "#.........#", "#.........#", "#.........#", "#####D#####"] },
    { name: "the Frozen Pond", min: 3, line: "The floor is ice from wall to wall, black and clear with the dark under it, and out on it three islands of stone with something on each. A step onto the ice is a long step.",
      rows: ["###########", "#OOOOOOOOO#", "#OOOOOOOcO#", "#OOOOOOOOO#", "#OcOOOOOOO#", "#OOOOOOOOO#", "#OOOOOOcOO#", "#OOOOOOOOO#", "#.........#", "#####D#####"], chests: { c: { note: "on an island of stone" } } },
  ];
  for (const r of SP7) { r.ownDice = true; if (!CM.SETPIECES.some((t) => t.name === r.name)) CM.SETPIECES.push(r); }
  const kind = (...names) => { for (const n of names) { const k = CM.monsterKind(n); if (k) return k; } return CM.MONSTERS[0]; };
  const nth = (fl, type, where = "features") => Object.values(fl[where] || {}).filter((t) => t.type === type && t.trial).length;
  CM.SETPIECE_LETTERS = Object.assign(CM.SETPIECE_LETTERS || {}, {
    I: (fl, x, y, k) => { fl.things[k] = { type: "hourglass" }; },
    "?": (fl, x, y, k) => { const n = nth(fl, "door"), h = CM.hashSeed(`${fl.number}:riddles`) >>> 0, asks = CM.RIDDLES.map((r, i) => i); fl.features[k] = { type: "door", open: false, riddle: asks[(h + n * 7) % asks.length], statue: true, trial: true }; },
    J: (fl, x, y, k) => { fl.features[k] = { type: "pendulum", phase: nth(fl, "pendulum") % 2, known: true, trial: true }; },
    Z: (fl, x, y, k, T, R) => { const group = []; for (let i = 0; i < 2; i++) group.push(CM.makeMonster(kind("Wraith", "Skeleton"), Math.max(1, CM.storyOf(fl.number)), R)); fl.things[k] = { type: "monsters", group, asleep: true, still: true, shadows: true }; },
    O: (fl, x, y, k) => { fl.features[k] = { type: "ice", known: true }; },
  });
  const P = CM.Game.prototype;
  const groupAt = (game, fl, group) => { const [dx, dy] = CM.DIRS[fl.facing], sq = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, th = { type: "monsters", group }; const was = fl.things[sq]; fl.things[sq] = th; game.startCombat(sq, th); if (fl.things[sq] === th) { if (was) fl.things[sq] = was; else delete fl.things[sq]; } };
  const roomOf = (game, fl) => { const r = CM.setPieceOf(fl, fl.pos[0], fl.pos[1]); return r ? r.template.name : null; };
  const sandRuns = (game, fl) => { const E = game.ext("hourglass"), S = E[fl.number]; return Boolean(S && (game.steps || 0) < S.until); };
  CM.sandRuns = sandRuns;
  const LINES = { hourglass: (g, t) => (sandRuns(g, g.floor) ? "The glass, turned: the sand runs, and the bars on the chests are up. Be quick." : "A glass the height of a man, its sand all in the bottom bulb. (Space to turn it)") };
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a); const fl = this.floor; if (fl && this.mode === "explore" && !this.perch && fl.things) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`; for (const k of [here, ahead]) { const t = fl.things[k]; if (t && LINES[t.type]) { this.say(LINES[t.type](this, t)); break; } } } return out; }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`;
        // a sealed chest of the Hourglass Room opens while the sand runs
        { const t = fl.things[here]; if (t && t.type === "chest" && t.sealed === "the Hourglass Room") { if (!sandRuns(this, fl)) { this.sound("bump"); this.say(`The chest is ${t.note}. The sand is not running.`); return true; } delete t.sealed; const out = u0.apply(this, a); if (fl.things[here] === t) t.sealed = "the Hourglass Room"; return out; } }
        for (const k of [here, ahead]) { const t = fl.things[k]; if (!t) continue;
          if (t.type === "hourglass") { const E = this.ext("hourglass"), day = CM.dayOf ? CM.dayOf(this) : 0, S = (E[fl.number] = E[fl.number] || {}); if (sandRuns(this, fl)) { this.say("The sand is running. Go."); return true; } if (S.day === day) { this.say("The glass has been turned today, and the frame will not turn again till tomorrow. The chests keep their bars."); return true; }
            S.day = day; S.until = (this.steps || 0) + TR.sandSteps; this.sound("grind"); this.say(`You put your weight on the handle and the glass goes over, and the sand begins to run. Round the walls, four bars lift with a clank. ${TR.sandSteps} steps of sand.`); this.emit("change"); return true; } }
        // the Pendulum Hall: Space waits a beat
        if (roomOf(this, fl) === "the Pendulum Hall" && !fl.things[here] && !fl.things[ahead]) { this.steps = (this.steps || 0) + 1; this.clock = (this.clock || 0) + 1; this.say("You wait a beat, and count the blades."); this.emit("change"); return true; } }
      return u0.apply(this, a); }; }
  // the blades: on the beat a bounded cut and a square back; the ice: a step keeps going
  { const ar0 = P.arrive; P.arrive = function (f, k) { const fl = this.floor;
      if (f && f.type === "pendulum") { const onBeat = (((this.steps || 0) + f.phase) % 2) === 0; if (!onBeat) { this.say("The blade goes by in front of your face and you step through behind it."); return; } let hurt = 0; for (const h of this.alive()) if (h.hp > TR.bladeCut) { h.hp = Math.max(1, h.hp - TR.bladeCut); hurt++; break; } const [dx, dy] = CM.DIRS[fl.facing], back = [fl.pos[0] - dx, fl.pos[1] - dy]; if (CM.isOpen(fl, back[0], back[1]) && !fl.things[`${back[0]},${back[1]}`]) fl.pos = back; this.sound("trap"); this.say(hurt ? `The blade takes you across the chest (-${TR.bladeCut}) and throws you back a square. Count it, and go on the other beat.` : "The blade throws you back a square. Count it."); this.emit("change"); return; }
      return ar0.call(this, f, k); }; }
  { const m0 = P.move; P.move = function (rel) { const fl = this.floor, out = m0.call(this, rel); if (!out || !fl || this.floor !== fl || this.mode !== "explore") return out; const k = `${fl.pos[0]},${fl.pos[1]}`, f = fl.features[k]; if (!f || f.type !== "ice") return out;
      const [dx, dy] = CM.DIRS[(fl.facing + rel) % 4]; let slid = 0; const was = this.replaying; this.replaying = 1;   /* (the slide's own steps are not logged: a replay slides again) */
      try { while (slid < TR.slideMost) { const nx = fl.pos[0] + dx, ny = fl.pos[1] + dy, nk = `${nx},${ny}`, nf = fl.features[nk]; if (!CM.isOpen(fl, nx, ny) || fl.things[nk] || (nf && nf.type !== "ice")) break; if (!m0.call(this, rel) || this.mode !== "explore" || this.floor !== fl) break; slid++; } } finally { this.replaying = was; }
      if (slid) this.say(slid >= 3 ? `The ice takes you: ${slid + 1} squares before anything stops you.` : "The ice takes you a little way."); this.emit("change"); return out; }; }
  // the Dark Room: the torch will not burn in it
  { const b0 = P.burn; P.burn = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && roomOf(this, fl) === "the Dark Room") { this.gutter = Math.max(this.gutter || 0, 2);   /* (two: the step itself burns one off) */ if (!fl.darkSaid) { fl.darkSaid = true; this.say("The torch goes out at the door, and will not take again in here. Only a light of your own making will show the walls."); } } return b0.apply(this, a); }; }
  // the Riddle Gallery: a wrong answer wakes the statue, once each
  { const ar0 = P.answerRiddle; P.answerRiddle = function (k, answer) { const fl = this.floor, f = fl && fl.features[k], r = f && CM.RIDDLES[f.riddle], wasOpen = f && f.open; const out = ar0.call(this, k, answer); if (f && f.statue && r && !wasOpen && answer !== r.a && !f.woke && this.mode === "explore") { f.woke = true; const R = new CM.Random(CM.hashSeed(`${this.seed}:statue:${fl.number}:${k}`)); this.say("The statue's hand comes down. It is not stone, or not only."); groupAt(this, fl, [CM.makeMonster(kind("Gargoyle", "Skeleton"), Math.max(1, CM.storyOf(fl.number)), R)]); } return out; }; }
}
