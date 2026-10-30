"use strict";
// A party that plays by itself, the way a sensible player would on a first run: opens the chests on the way,
// finds the key before the locked door and the lever before the gate, drinks from fountains when hurt, fights
// what it walks into (healing under a third, casting at a crowd), takes the class's own stat at every level,
// the first path offered, rests and buys potions at the camp, smashes the phylactery on 19 - and keeps going down
// until the party falls, the run ends, or it has gone as deep as it was asked to. The balance simulator runs it
// over many seeds; the tests use it to get a run a few floors deep.
const { autoplayFight } = require("./headless");

const AVOID = ["pit", "trapdoor", "teleporter"];                    // (a spinner only turns the party: harmless to a walker that looks again every step)

function playRun(CM, game, opts = {}) {
  const maxFloor = opts.maxFloor || 50, perFloor = opts.perFloor || 900;
  const log = [];
  let stuck = 0, moves = 0, floorMoves = 0, onFloor = 0;
  const alive = () => game.alive();
  const needs = () => {
    for (const h of game.party) {
      if (h.pending > 0 && h.hp > 0) { const offer = game.offerBoons(h); game.chooseBoon(h, offer[0]); }
      if (CM.needsPath(h)) game.choosePath(h, Object.keys(CM.PATHS[h.cls])[0]);
    }
  };
  const potions = () => {
    if ((game.fed || 0) >= CM.HUNGER.hungry) { const row = game.bag.findIndex((i) => i.kind === "ration"); if (row >= 0) game.give(row, game.party.indexOf(alive()[0])); }
    for (const h of alive()) {
      if (h.hp < h.max * 0.4) { const row = game.bag.findIndex((i) => i.kind === "heal"); if (row >= 0) game.give(row, game.party.indexOf(h)); }
      if (h.maxmp && h.mp < h.maxmp * 0.2) { const row = game.bag.findIndex((i) => i.kind === "mana"); if (row >= 0) game.give(row, game.party.indexOf(h)); }
    }
  };
  // the choices a careful player makes at the floor's strange things
  const SAFE = { bloodshrine: 1, prisoner: 1, gamble: 1, cursedfountain: 1, oldcampfire: 1, merchantcorpse: 1, whisperingdoor: 1, ratnest: 2, statue: 0, lostpack: 0, pool: 0, hermitgrave: 1 };
  const handled = new Set();
  let asked = null;
  game.on("choice", (c) => { asked = c; });
  const alchemy = () => {
    for (const id of ["greaterheal", "antivenom", "oilfire", "oilholy", "oilfrost", "vigour", "fortune"]) { let guard = 0; while (!game.recipeLacks(id) && guard++ < 3 && (id === "greaterheal" ? game.bag.filter((i) => i.kind === "greaterheal").length < 3 : true)) game.brew(id); }
  };
  const camp = () => {
    needs();
    alchemy();
    while (game.party.some((h) => h.hp <= 0) && game.gold >= 100 * game.party.find((h) => h.hp <= 0).level) game.raiseDead();
    if (game.party.some((h) => (h.status || {}).stone) && game.gold >= 150) game.temple("unstone");
    if (game.party.some((h) => (h.status || {}).curse) && game.gold >= 60) game.temple("uncurse");
    if (alive().some((h) => h.hp < h.max * 0.9 || (h.maxmp && h.mp < h.maxmp * 0.7) || Object.keys(h.status || {}).length) && game.gold >= 20) game.rest();
    if (game.party.some((h) => h.hp <= 0)) { const who = game.tavern(); if (who.length) game.hire(0); }
    game.openBag(true);
    const want = (kind, n) => { let guard = 0; while (game.bag.filter((i) => i.kind === kind).length < n && guard++ < 10) { const row = game.stock.findIndex((i) => i.kind === kind); if (row < 0 || game.buy(row)) break; } };
    want("heal", 4); want("torch", 2); want("ration", 2);
    if (game.gold > 150) want("mana", 2);
    if (game.gold > 250) want("revive", 1);
    // better weapons for the gold left: the cheapest upgrade in the merchant's wares, if any
    for (const h of alive()) {
      const row = game.stock.findIndex((it) => it.kind === "weapon" && it.power > (h.weapon ? h.weapon.power : 0) + 1 && it.value <= game.gold - 60 && !CM.cantWear(h, it));
      if (row >= 0 && !game.buy(row)) { const bagRow = game.bag.length - 1; game.equip(h, bagRow); }
    }
    game.closeBag();
    game.leaveCamp();
  };
  const walkOK = (fl, x, y) => {
    const k = `${x},${y}`;
    if (!CM.isOpen(fl, x, y)) return false;
    const f = fl.features[k];
    if (f && AVOID.includes(f.type) && f.type !== "teleporter" && !(f.type === "pit" && f.roped)) return false;
    if (f && f.type === "gate" && !f.open) return false;
    if (f && f.type === "door" && f.locked && !f.open && game.hasKey() < 0 && !alive().some((h) => h.cls === "Rogue" && h.level >= CM.PICK_LOCK_LEVEL)) return false;
    return true;
  };
  // one walk out from the party's square each move: where it can get to, and the way there (a teleporter is a jump)
  let paths = null;
  const walk = (fl) => {
    const start = `${fl.pos[0]},${fl.pos[1]}`, parent = new Map([[start, null]]), queue = [fl.pos], landed = new Set();
    for (let i = 0; i < queue.length; i++) {
      const [x, y] = queue[i], k = `${x},${y}`, f = fl.features[k];
      if (f && f.type === "teleporter" && k !== start && !landed.has(k)) {   // (stepping onto one is a jump; landing on its twin is not another)
        const tk = `${f.to[0]},${f.to[1]}`;
        if (!parent.has(tk)) { parent.set(tk, k); landed.add(tk); queue.push(f.to); }
        continue;
      }
      for (const [dx, dy] of CM.DIRS) {
        const nx = x + dx, ny = y + dy, nk = `${nx},${ny}`;
        if (parent.has(nk) || !walkOK(fl, nx, ny)) continue;
        parent.set(nk, k); queue.push([nx, ny]);
      }
    }
    paths = { start, parent };
  };
  // the next square towards a goal: "here", a direction, or null when there is no way
  const stepTo = (fl, goalK) => {
    const { start, parent } = paths;
    if (!parent.has(goalK)) return null;
    if (goalK === start) return "here";
    let k = goalK;
    while (parent.get(k) !== start) k = parent.get(k);
    const [x, y] = k.split(",").map(Number), d = CM.DIRS.findIndex(([dx, dy]) => fl.pos[0] + dx === x && fl.pos[1] + dy === y);
    return d < 0 ? null : d;
  };
  const face = (d) => { const r = (d - game.floor.facing + 4) % 4; if (r === 1) game.turn(1); else if (r === 3) game.turn(-1); else if (r === 2) { game.turn(1); game.turn(1); } };
  const pick = () => {                                                 // what to go for next on this floor
    const fl = game.floor, things = Object.entries(fl.things), feats = Object.entries(fl.features);
    const goal = CM.goalOf(fl);
    const can = (k) => paths.parent.has(k);
    const phyl = things.find(([, t]) => t.type === "phylactery");
    if (phyl && can(phyl[0])) return phyl[0];
    const keys = things.filter(([k, t]) => t.type === "key" && can(k));
    if (keys.length) return keys[0][0];
    const box = things.find(([, t]) => t.type === "strongbox" && !t.opened && game.bag.some((i) => i.kind === "boxkey" && i.box === fl.number));
    if (box && can(box[0])) return box[0];
    const ev = things.find(([k, t]) => (t.type === "event" && !t.done && !handled.has(fl.number + ":" + k)) || (t.type === "peddler" && !handled.has(fl.number + ":" + k)));
    if (ev && can(ev[0]) && floorMoves < perFloor * 0.6) return ev[0];
    const chests = things.filter(([, t]) => t.type === "chest").map(([k]) => k).filter(can);
    if (chests.length && floorMoves < perFloor * 0.6) return chests[0];
    const wall = feats.find(([k, f]) => f.type === "carving" && !f.read && can(k));   // (the walls: the story, and the hermit's price)
    if (wall && floorMoves < perFloor * 0.7) return wall[0];
    if (goal && can(goal)) return goal;
    const lever = feats.find(([, f]) => (f.type === "lever" && !f.pulled) || (f.type === "plate" && f.gate && !f.pressed));
    if (lever && can(lever[0])) return lever[0];
    const bones = things.find(([, t]) => t.type === "bones");
    if (bones && can(bones[0])) return bones[0];
    return goal;
  };
  while (true) {
    if (game.mode === "title") break;
    if (game.mode === "combat") { autoplayFight(CM, game); continue; }
    if (game.mode === "camp") { camp(); continue; }
    if (game.mode !== "explore") break;
    needs(); potions();
    if (game.floor.number > maxFloor) { log.push("deep enough"); break; }
    if (game.floor.number !== onFloor) { onFloor = game.floor.number; floorMoves = 0; }
    if (++floorMoves > perFloor) {                                       // lost on this floor: give it up (counted, so the sim can say)
      stuck++; log.push(`stuck on floor ${game.floor.number}`);
      if (stuck > 3) break;
      game.warp(game.floor.number + 1);
      continue;
    }
    moves++;
    if (moves > (opts.maxMoves || 60000)) { log.push("out of moves"); break; }
    const fl = game.floor, here = `${fl.pos[0]},${fl.pos[1]}`, f = fl.features[here], t = fl.things[here];
    if (f && f.type === "fountain" && !f.used && alive().some((h) => h.hp < h.max * 0.5)) { game.drink(f); continue; }
    if (f && f.type === "altar" && !f.used && alive().some((h) => h.hp < h.max * 0.6)) { game.kneel(f); continue; }
    walk(fl);
    const target = pick();
    if (t && t.type === "event" && !t.done && !handled.has(fl.number + ":" + here)) {   // (asked once: "walk on" leaves the thing standing)
      handled.add(fl.number + ":" + here);
      const E = CM.EVENTS[t.event]; asked = null; game.use();
      if (asked) game.choose(here, Math.min(SAFE[t.event] === undefined ? E.options.length - 1 : SAFE[t.event], E.options.length - 1));
      continue;
    }
    if (t && t.type === "strongbox" && !t.opened && game.bag.some((i) => i.kind === "boxkey" && i.box === fl.number)) { game.use(); continue; }
    if (t && t.type === "peddler" && !handled.has(fl.number + ":" + here)) { handled.add(fl.number + ":" + here); game.use(); if (game.shopping) { const row = game.stock.findIndex((i) => i.kind === "greaterheal" && i.value <= game.gold - 100); if (row >= 0) game.buy(row); game.closeBag(); } continue; }
    if (CM.guardianFor(fl.number) && !fl.oiled) {                        // a guardian's floor: the oils go on the front line
      fl.oiled = true;
      for (const h of alive().filter((p) => p.row === "front")) { const row = game.bag.findIndex((i) => i.kind === "oil"); if (row >= 0) game.give(row, game.party.indexOf(h)); }
    }
    if (!target) { stuck++; log.push(`no goal on floor ${fl.number}`); if (stuck > 3) break; game.warp(fl.number + 1); continue; }
    const step = stepTo(fl, target);
    if (step === "here") {
      if (t && ["chest", "ladder", "phylactery", "stairs_up"].includes(t.type)) { const before = game.floor.number + ":" + game.mode; game.use(); if (game.floor.number + ":" + game.mode === before && t.type === "ladder") { stuck++; } }
      else if (t && t.type === "ghost") { game.talk(t, here); if (fl.things[here]) { game.talk(t, here); } if (fl.things[here]) delete fl.things[here]; }
      else if (f && f.type === "carving" && !f.read) { face(f.face); game.use(); if (!f.read) { stuck++; log.push("a wall that won't be read"); } }
      else if (t && t.type === "bones") { /* picked up by walking on it */ }
      else if (f && (f.type === "lever" || f.type === "plate")) { if (f.type === "lever") { face(f.face); game.use(); } if ((f.type === "lever" && !f.pulled) || (f.type === "plate" && f.gate && !f.pressed)) { stuck++; log.push("lever won't"); } }
      else if (t && t.type === "key") { /* taken as we stepped on it */ }
      else if (t && (t.type === "event" || t.type === "peddler" || t.type === "strongbox")) { stuck++; log.push(`${t.type} not taken at ${here}`); t.done = true; t.opened = true; delete fl.things[here]; }
      else { stuck++; log.push(`nothing to do at ${here} on floor ${fl.number}`); if (stuck > 6) break; game.warp(fl.number + 1); }
      continue;
    }
    if (step === null) { stuck++; log.push(`no way to ${target} on floor ${fl.number}`); if (stuck > 3) break; game.warp(fl.number + 1); continue; }
    face(step);
    const [dx, dy] = CM.DIRS[step], nk = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, nf = fl.features[nk];
    if (nf && nf.type === "door" && !nf.open && nf.riddle !== undefined && CM.RIDDLES[nf.riddle]) { game.answerRiddle(nk, CM.RIDDLES[nf.riddle].a); continue; }
    const was = fl.pos.join(",");
    game.move(0);
    if (game.mode === "explore" && game.floor === fl && fl.pos.join(",") === was) {
      // the door opened (move again next loop), the lock held (a Rogue may try again), or something odd: a few tries, then another target
      if (nf && nf.type === "door" && nf.locked && !nf.open && game.hasKey() < 0) { if (++stuck > 40) break; }
    }
  }
  return { log, moves, stuck };
}

module.exports = { playRun };
