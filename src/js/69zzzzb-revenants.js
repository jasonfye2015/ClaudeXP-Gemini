"use strict";
// Your own dead come back (UPGRADE_PLAN_75.md, release 2). A hero on the memorial may rise, on a later run, in the band
// where they fell: a revenant with their name and what they were buried with, on one floor of that band (by the run's
// seed, about one band in three that holds such a name; never more than one a band). Lay them to rest and what they
// carried comes home, the memorial wall marks them at rest, and Claude writes them an epilogue. Never on the seed
// they fell on, and never on a guardian's, a camp's or the king's floor.
//   CM.revenantFor(game, band) -> memorial entry or null; a revenant foe has .revenant (the entry's id)
{ const P = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  const idOf = (m) => `${m.name}|${m.date}|${m.seed}`;
  const bandOf = (n) => (n >= 1 && n <= CM.BOTTOM ? CM.themeIndex(n) : -1);
  CM.revenantFor = (g, band) => { const M = (g.memorial || []).filter((m) => m && m.floor >= 1 && bandOf(m.floor) === band && !m.atRest && m.seed !== g.seed); if (!M.length) return null;
    if (CM.hashSeed(`${g.seed}:rev:${band}`) % 3 !== 0) return null; return M[CM.hashSeed(`${g.seed}:revwho:${band}`) % M.length]; };
  const BODY = { Knight: "Drowned", Paladin: "Drowned", Rogue: "Hollow One", Ranger: "Hollow One", Cleric: "Grave Priest", Mage: "Grave Priest", Druid: "Weed Hag", Bard: "Wraith", Monk: "Ghoul", Necromancer: "Grave Priest", Artificer: "Wraith" };
  { const em0 = P.emit; P.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally) { const fl = this.floor, n = fl.number, b = bandOf(n), E = this.ext("revenants");
        if (b >= 0 && n % 1 === 0 && fl.special !== "interior" && !(this.deltas && this.deltas[n]) && !E[`b${b}`]) {
          const m = CM.revenantFor(this, b), T = CM.THEMES[b], ok = []; for (let f = T.floors[0]; f <= T.floors[1]; f++) if (!(CM.guardianFor && CM.guardianFor(f)) && f !== CM.LAST_FLOOR && !(CM.CAMP_FLOORS || []).includes(f)) ok.push(f); const at = m && ok.length ? ok[CM.hashSeed(`${this.seed}:revat:${b}`) % ok.length] : -1;
          if (m && n === at) { E[`b${b}`] = true; const K = CM.monsterKind(BODY[m.cls] || "Wraith") || CM.monsterKind("Wraith"), R = new CM.Random(CM.hashSeed(`${this.seed}:revmon:${b}`));
            const foe = CM.makeMonster(K, CM.monsterLevel ? CM.monsterLevel(n) : n, R); foe.kind = foe.kind || K.name; foe.name = `${m.name}, risen`; foe.revenant = idOf(m); foe.max = Math.round((foe.max || foe.hp) * 1.6); foe.hp = foe.max; foe.atk = Math.round((foe.atk || 5) * 1.2); foe.xp = Math.round((foe.xp || 10) * 2.5);
            const N = fl.grid.length, cells = []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (fl.grid[y][x] === 0 && !fl.things[key(x, y)] && !(fl.features || {})[key(x, y)] && Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) > 6) cells.push(key(x, y));
            if (cells.length) { fl.things[cells[CM.hashSeed(`${this.seed}:revcell:${b}`) % cells.length]] = { type: "monsters", group: [foe], revenant: true };
              this.say(`Somewhere on this floor, something is walking that you know the name of. ${m.name} fell near here, once.`); if (CM.narrate) CM.narrate(this, `${m.name} is down here. I never thought I'd have to write that twice.`); } } } }
      return em0.call(this, ev, ...a); }; }
  // laid to rest
  const rest = (g, foe) => { if (!foe || !foe.revenant || foe.laid) return; foe.laid = true; const m = (g.memorial || []).find((x) => idOf(x) === foe.revenant); if (!m) return;
    m.atRest = CM.today ? CM.today() : "at rest"; if (!g.replaying) CM.store.set("memorial", g.memorial);
    if (m.buried) { const it = JSON.parse(JSON.stringify(m.buried)); it.lore = `${it.lore ? it.lore + " " : ""}Carried home from ${m.name}, laid to rest at last.`; g.bag.push(it); }
    g.say(`${m.name} goes still, and is only bones, and then not even that. ${m.buried ? `What they carried comes home with you: ${m.buried.name}.` : "There is nothing to carry home but the name."}`);
    if (CM.narrate) CM.narrate(g, `${m.name}, at rest. I've written them an ending, the one they didn't get the first time.`);
    const V = g.vext("claude"); V.epilogues = (V.epilogues || []).concat({ name: m.name, cls: m.cls, floor: m.floor, date: m.atRest }).slice(-20); if (g.saveVillage && !g.replaying) g.saveVillage(); };
  { const em1 = P.emit; P.emit = function (ev, fx, ...a) { if (ev === "fx" && fx && fx.kind === "die" && fx.foe && fx.foe.revenant) { const real = (this.foes || []).find((f) => f.revenant === fx.foe.revenant) || fx.foe; rest(this, real); } return em1.call(this, ev, fx, ...a); }; }
  // the memorial wall knows
  { const rm0 = P.readMemorialWall; if (rm0) P.readMemorialWall = function (...a) { const out = rm0.apply(this, a), M = (this.memorial || []).slice().reverse(), W = this.ext("memwall"), i = ((W.i || 1) - 1) % Math.max(1, M.length), m = M[i];
      if (m && m.atRest) { const last = this.messages.length - 1; if (last >= 0 && !this.messages[last].includes("At rest")) this.messages[last] += ` Cut beside it, newer: AT REST${typeof m.atRest === "string" ? `, ${m.atRest}` : ""}.`; this.emit("change"); } return out; }; }
  // Claude's epilogues, at the desk
  CM.claudeTopics = (CM.claudeTopics || []).concat([(g) => ((g.vext("claude").epilogues || []).length ? [["epilogues", "The ones we laid to rest"]] : [])]);
  CM.claudeActs = Object.assign(CM.claudeActs || {}, {
    epilogues(g, k) { const L = (g.vext("claude").epilogues || []).slice().reverse(); g.claudeTalk(k, "epilogues", L.map((e, i) => ["epilogue", `${e.name}, ${e.cls || ""}`.replace(/, $/, ""), i]).concat([["main", "Something else"]]), "\"I wrote each of them an ending. Which?\""); },
    epilogue(g, k, say, i) { const e = (g.vext("claude").epilogues || []).slice().reverse()[i]; if (!e) return; g.emit("talk", { title: `An epilogue: ${e.name}`, text: `"${e.name}${e.cls ? `, the ${e.cls}` : ""}, fell on floor ${e.floor}, and walked there afterwards for longer than anyone should. Then a party came down that knew the name, and stopped, and did the kind thing, which was also the hard one. ${e.name} is at rest. I've written it in the good ink."` }); },
  });
}
