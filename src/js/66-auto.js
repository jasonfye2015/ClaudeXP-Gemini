"use strict";
// Automatic: the party plays by itself, the way a sensible player would on a first run - it opens the chests on the
// way, finds the key before the locked door and the lever before the gate, drinks from fountains when hurt, fights
// what it walks into (the fight's own Auto hand), wears what compares better as it comes, drinks when low, eats when
// hungry, sets traps and bars doors when it has them, and at the camp rests, heals, trades, insures, tithes and
// goes deeper. In the game it is a toggle (Z, or the Automatic button): one step a tick, and any move key takes the
// reins back; it stops by itself when it is lost or when a choice is the player's (the bottom of the world). The
// balance simulator and the tests drive the same class straight (tools/bot.js), with warping past a lost floor and
// the waking of the Root allowed, so a run can be measured to the end.
const AVOID = ["pit", "trapdoor", "teleporter"];                    // (a spinner only turns the party: harmless to a walker that looks again every step)
// the choices a careful player makes at the floor's strange things
const SAFE = { bloodshrine: 1, prisoner: 1, gamble: 1, cursedfountain: 1, oldcampfire: 1, merchantcorpse: 1, whisperingdoor: 1, ratnest: 2, statue: 0, lostpack: 0, pool: 0, hermitgrave: 1 };

CM.Autopilot = class {
  constructor(game, opts = {}) {
    this.game = game;
    this.opts = Object.assign({ maxFloor: 50, perFloor: 900, maxMoves: 60000, warp: false, wake: false, sync: false }, opts);
    this.log = []; this.stuck = 0; this.moves = 0; this.floorMoves = 0; this.onFloor = 0; this.campedAt = 0;
    this.handled = new Set(); this.asked = null; this.paths = null; this.on = true; this.why = ""; this.lastMode = game.mode;
    this.tools = { traps: 0, bars: 0, rests: 0, disarmed: 0 };           // (what it did with the tools)
    if (!game.autoChoiceHook) { game.autoChoiceHook = true; game.on("choice", (c) => { if (game.auto) game.auto.asked = c; }); }
    game.auto = this;
  }
  stop(why) { this.on = false; this.why = why || ""; if (why) this.log.push(why); return false; }
  alive() { return this.game.alive(); }
  // what has to be chosen: a level's stat, a path
  needs() {
    const game = this.game;
    for (const h of game.party) {
      if (h.pending > 0 && h.hp > 0) { const offer = game.offerBoons(h); game.chooseBoon(h, offer[0]); }
      if (CM.needsPath(h)) game.choosePath(h, Object.keys(CM.PATHS[h.cls])[0]);
    }
  }
  potions() {
    const game = this.game;
    if ((game.fed || 0) >= CM.HUNGER.hungry) { const row = game.bag.findIndex((i) => i.kind === "ration"); if (row >= 0) game.give(row, game.party.indexOf(this.alive()[0])); }
    for (const h of this.alive()) {
      if (h.hp < h.max * 0.4) { const row = game.bag.findIndex((i) => i.kind === "heal" || i.kind === "greaterheal"); if (row >= 0) game.give(row, game.party.indexOf(h)); }
      if (h.maxmp && h.mp < h.maxmp * 0.2) { const row = game.bag.findIndex((i) => i.kind === "mana"); if (row >= 0) game.give(row, game.party.indexOf(h)); }
      if (Object.keys(h.status || {}).some((s) => CM.CURABLE.includes(s))) { const row = game.bag.findIndex((i) => i.kind === "antidote"); if (row >= 0) game.give(row, game.party.indexOf(h)); }
    }
  }
  alchemy() {
    const game = this.game;
    for (const id of ["greaterheal", "antivenom", "oilfire", "oilholy", "oilfrost", "flaskoil", "smokeflask", "stoneskin", "vigour", "fortune"]) { let guard = 0; while (!game.recipeLacks(id) && guard++ < 3 && (id === "greaterheal" ? game.bag.filter((i) => i.kind === "greaterheal").length < 3 : true)) game.brew(id); }
  }
  // better gear, as it comes: for each hero, the best thing in the pack for each slot that compares well
  gearUp() {
    const game = this.game;
    for (const h of this.alive()) for (let guard = 0; guard < 6; guard++) {
      let best = -1, bestGain = 0;
      game.bag.forEach((it, row) => { if (!["weapon", "armor", "shield", "helm", "ring", "amulet", "boots", "cloak", "trinket"].includes(it.kind) || it.unknown) return; const c = game.compare(h, it); const gain = c && c.cls === "good" ? Number(c.text) || 1 : 0; if (gain > bestGain) { bestGain = gain; best = row; } });
      if (best < 0) break;
      if (game.equip(h, best)) break;
    }
  }
  // the town's errands before the descent, each at its own door: home (the hearth, the larder), the merchant (the
  // shopping), the temple (wounds), the tavern (a round, the board) - in that order, the doors that stand; then the shaft
  errands() {
    const game = this.game, want = [];
    if (game.homeLevel() >= 1) want.push("home");
    want.push("merchant");
    if (game.villageLevel("shrine") >= 1 && (game.party.some((h) => h.wound || h.hp <= 0) || game.gold > 300)) want.push("temple");
    if (game.gold > 60) want.push("tavern");
    return want.filter((id) => !(this.townDone || []).includes(id));
  }
  errand(id) {
    const game = this.game;
    this.townDone = (this.townDone || []).concat(id);
    game.use();                                                          // (the door opened: counted for the town's renown; the screen it opens is closed again by the frame loop)
    if (id === "home") { game.hearthRest(); while ((game.home().larder || 0) > 0 && game.bag.filter((i) => i.kind === "ration").length < 2) game.larderTake(); }
    else if (id === "merchant") { game.openBag(true); this.shopping(); game.closeBag(); }
    else if (id === "temple") { while (game.party.some((h) => h.hp <= 0) && game.gold >= 90 * game.party.find((h) => h.hp <= 0).level) game.raiseDead(); if (game.party.some((h) => h.wound) && game.gold >= 36 * game.party.filter((h) => h.wound).length + 60) game.temple("wounds"); if (game.gold > 300 && !game.blessed()) game.tithe(); }
    else if (id === "tavern") { game.drink(); if (game.bounty && game.bountyDone()) game.claimBounty(); else if (!game.bounty) game.takeBounty(); }
  }
  // the merchant's table, wherever it stands: potions, torches, rations, insurance, orders, the weight, the fence, a weapon
  shopping() {
    const game = this.game, alive = () => this.alive();
    const want = (kind, n) => { let guard = 0; while (game.bag.filter((i) => i.kind === kind).length < n && guard++ < 10) { const row = game.stock.findIndex((i) => i.kind === kind); if (row < 0 || game.buy(row)) break; } };
    want("heal", 4); want("torch", 2); want("ration", 2);
    if (game.gold > 150) for (const h of alive()) { const worn = CM.equipped(h).filter((it) => !it.insured && (it.value || 0) >= 100 && !(it.props && it.props.fists)).sort((a, b) => (b.value || 0) - (a.value || 0))[0]; if (worn && game.gold > 150) game.insure(game.party.indexOf(h), CM.SLOTS.find((s) => h[s] === worn)); }
    if (game.gold > 200 && (game.orders || []).length < 2) { if (!game.stock.some((i) => i.kind === "revive") && !game.bag.some((i) => i.kind === "revive")) game.order("revive"); if (!game.stock.some((i) => i.kind === "mana") && game.bag.filter((i) => i.kind === "mana").length < 2) game.order("mana"); if (!game.bag.some((i) => i.kind === "lampoil") && game.light && game.light.kind === "lantern") game.order("lampoil"); }
    if (game.overweight() > 1) { let guard = 0; while (game.overweight() > 1 && guard++ < 10) { const row = game.bag.map((it, i) => [it, i]).filter(([it]) => CM.weightOf(it) >= 3 && it.kind !== "torch").sort((a, b) => a[0].value - b[0].value)[0]; if (!row) break; game.sell(row[1]); } }
    if (game.inTown()) for (let i = game.bag.length - 1; i >= 0; i--) if (game.bag[i].unknown || (game.bag[i].props && game.bag[i].props.cursed)) game.fence(i);
    if (game.gold > 150) want("mana", 2);
    if (game.gold > 250) want("revive", 1);
    for (const h of alive()) {                                           // better weapons for the gold left: the cheapest upgrade in the merchant's wares, if any
      const row = game.stock.findIndex((it) => it.kind === "weapon" && it.power > (h.weapon ? h.weapon.power : 0) + 1 && it.value <= game.gold - 60 && !CM.cantWear(h, it));
      if (row >= 0 && !game.buy(row)) { const bagRow = game.bag.length - 1; game.equip(h, bagRow); }
    }
  }
  // the camp's business: heal, trade, insure, tithe, buy what is short - then (the next step) go deeper
  camp() {
    const game = this.game, alive = () => this.alive();
    this.needs(); this.gearUp();
    this.alchemy();
    while (game.party.some((h) => h.hp <= 0) && game.gold >= 100 * game.party.find((h) => h.hp <= 0).level) game.raiseDead();
    if (game.party.some((h) => (h.status || {}).stone) && game.gold >= 150) game.temple("unstone");
    if (game.party.some((h) => (h.status || {}).curse) && game.gold >= 60) game.temple("uncurse");
    if (alive().some((h) => h.hp < h.max * 0.9 || (h.maxmp && h.mp < h.maxmp * 0.7) || Object.keys(h.status || {}).length) && game.gold >= 20) game.rest();
    if (game.party.some((h) => h.hp <= 0)) { const who = game.tavern(); if (who.length) game.hire(0); }
    game.openBag(true);
    if (game.party.some((h) => h.wound) && game.gold >= 40 * game.party.filter((h) => h.wound).length + 60) game.temple("wounds");
    if (game.bounty && game.bountyDone()) game.claimBounty(); else if (!game.bounty) game.takeBounty();
    if (game.gold > 300 && !game.blessed()) game.tithe();
    this.shopping();
    game.closeBag();
  }
  walkOK(fl, x, y) {
    const game = this.game, k = `${x},${y}`;
    if (!CM.isOpen(fl, x, y)) return false;
    const f = fl.features[k];
    if (f && AVOID.includes(f.type) && f.type !== "teleporter" && !(f.type === "pit" && f.roped)) return false;
    if (f && f.type === "gate" && !f.open) return false;
    if (f && f.type === "door" && f.locked && !f.open && game.hasKey() < 0 && !this.alive().some((h) => h.cls === "Rogue" && h.level >= CM.PICK_LOCK_LEVEL) && !game.bag.some((i) => i.kind === "lockpick")) return false;
    return true;
  }
  // one walk out from the party's square each move: where it can get to, and the way there (a teleporter is a jump)
  walk(fl) {
    const start = `${fl.pos[0]},${fl.pos[1]}`, parent = new Map([[start, null]]), queue = [fl.pos], landed = new Set();
    for (let i = 0; i < queue.length; i++) {
      const [x, y] = queue[i], k = `${x},${y}`, f = fl.features[k];
      if (f && f.type === "teleporter" && k !== start && !landed.has(k)) {
        const tk = `${f.to[0]},${f.to[1]}`;
        if (!parent.has(tk)) { parent.set(tk, k); landed.add(tk); queue.push(f.to); }
        continue;
      }
      for (const [dx, dy] of CM.DIRS) {
        const nx = x + dx, ny = y + dy, nk = `${nx},${ny}`;
        if (parent.has(nk) || !this.walkOK(fl, nx, ny)) continue;
        parent.set(nk, k); queue.push([nx, ny]);
      }
    }
    this.paths = { start, parent };
  }
  // the next square towards a goal: "here", a direction, or null when there is no way
  stepTo(fl, goalK) {
    const { start, parent } = this.paths;
    if (!parent.has(goalK)) return null;
    if (goalK === start) return "here";
    let k = goalK;
    while (parent.get(k) !== start) k = parent.get(k);
    const [x, y] = k.split(",").map(Number), d = CM.DIRS.findIndex(([dx, dy]) => fl.pos[0] + dx === x && fl.pos[1] + dy === y);
    return d < 0 ? null : d;
  }
  face(d) { const game = this.game, r = (d - game.floor.facing + 4) % 4; if (r === 1) game.turn(1); else if (r === 3) game.turn(-1); else if (r === 2) { game.turn(1); game.turn(1); } }
  pick() {                                                               // what to go for next on this floor
    const game = this.game, fl = game.floor, things = Object.entries(fl.things), feats = Object.entries(fl.features), perFloor = this.opts.perFloor, floorMoves = this.floorMoves;
    const goal = CM.goalOf(fl);
    const can = (k) => this.paths.parent.has(k);
    if (fl.number === 0) {                                               // the town: the errands' doors, then the shaft
      for (const id of this.errands()) { const k = CM.TOWN_AT[id].join(","); if (can(k)) return k; this.townDone = (this.townDone || []).concat(id); }
      return goal;
    }
    const phyl = things.find(([, t]) => t.type === "phylactery");
    if (phyl && can(phyl[0])) return phyl[0];
    const keys = things.filter(([k, t]) => t.type === "key" && can(k));
    if (keys.length) return keys[0][0];
    const box = things.find(([, t]) => t.type === "strongbox" && !t.opened && game.bag.some((i) => i.kind === "boxkey" && i.box === fl.number));
    if (box && can(box[0])) return box[0];
    const ev = things.find(([k, t]) => (t.type === "event" && !t.done && !this.handled.has(fl.number + ":" + k)) || (t.type === "peddler" && !this.handled.has(fl.number + ":" + k)));
    if (ev && can(ev[0]) && floorMoves < perFloor * 0.6) return ev[0];
    const nodes = things.filter(([k, t]) => t.type === "node" && can(k)).map(([k]) => k);
    if (nodes.length && floorMoves < perFloor * 0.5) return nodes[0];
    const chests = things.filter(([, t]) => t.type === "chest").map(([k]) => k).filter(can);
    if (chests.length && floorMoves < perFloor * 0.6) return chests[0];
    const soul = things.find(([k, t]) => t.type === "ghost" && !t.heard && can(k));
    if (soul && floorMoves < perFloor * 0.6) return soul[0];
    const wall = feats.find(([k, f]) => f.type === "carving" && !f.read && can(k));
    if (wall && floorMoves < perFloor * 0.7) return wall[0];
    if (goal && can(goal)) return goal;
    const lever = feats.find(([, f]) => (f.type === "lever" && !f.pulled) || (f.type === "plate" && f.gate && !f.pressed));
    if (lever && can(lever[0])) return lever[0];
    const bones = things.find(([, t]) => t.type === "bones");
    if (bones && can(bones[0])) return bones[0];
    return goal;
  }
  // lost on this floor: the simulator warps past it (counted); in the game, Automatic stops and says so
  giveUp(why) {
    const game = this.game;
    this.stuck++; this.log.push(why);
    if (!this.opts.warp) { game.say(`Automatic stops: ${why}. The reins are yours.`); return this.stop(why); }
    if (this.stuck > 3) return this.stop("lost too often");
    game.warp(game.floor.number + 1);
    return "warped";
  }
  // one step: what it did, or false when it has stopped
  step() {
    const game = this.game;
    if (!this.on) return false;
    if (game.mode === "title") return this.stop("the run is over");
    if (game.rootPending) { if (!this.opts.wake) { game.say("Automatic stops: what is done at the bottom of the world is yours to decide."); return this.stop("the root"); } game.ending(0); return "woke the root"; }
    if (game.mode === "combat") {
      if (this.opts.sync) { let guard = 0; while (game.mode === "combat" && game.combat && guard++ < 400) { if (!game.combat.waiting) { game.advance(); continue; } game.combat.auto = false; if (!game.autoTurn()) break; } return "fought"; }
      if (game.combat && !game.combat.auto) game.autoFight(true);     // (the fight's own Auto hand plays it, a turn a tick)
      return "fighting";
    }
    if (game.mode === "camp") {
      if (this.campedAt !== game.floor.number) { this.campedAt = game.floor.number; this.camp(); return "camp"; }
      game.leaveCamp(); return "deeper";
    }
    if (game.mode !== "explore") return this.stop(`not a mode Automatic plays (${game.mode})`);
    if (this.lastMode === "combat") { this.gearUp(); this.potions(); }    // (after a fight: wear what dropped, drink what is needed)
    this.lastMode = game.mode;
    this.needs(); this.potions();
    if (this.moves % 25 === 0) this.gearUp();
    if (game.floor.number > this.opts.maxFloor) return this.stop("deep enough");
    if (game.floor.number !== this.onFloor) { this.onFloor = game.floor.number; this.floorMoves = 0; if (game.floor.number === 0) this.townDone = []; }
    if (++this.floorMoves > this.opts.perFloor) { this.floorMoves = 0; return this.giveUp(`lost on floor ${game.floor.number}`); }
    this.moves++;
    if (this.moves > this.opts.maxMoves) return this.stop("out of moves");
    const fl = game.floor, here = `${fl.pos[0]},${fl.pos[1]}`, f = fl.features[here], t = fl.things[here], alive = this.alive();
    if (f && f.type === "fountain" && !f.used && alive.some((h) => h.hp < h.max * 0.5)) { game.drink(f); return "drank"; }
    if (f && f.type === "altar" && !f.used && alive.some((h) => h.hp < h.max * 0.6)) { game.kneel(f); return "knelt"; }
    {                                                                    // the tools: a trap set from parts, a door barred and rested at when the party is worn
      const kit = game.bag.some((i) => i.kind === "trapkit"), parts = game.bag.findIndex((i) => i.kind === "trapparts");
      if (kit && parts >= 0 && game.give(parts, 0) === "") { this.tools.traps++; return "set a trap"; }
      const worn = alive.reduce((s, h) => s + h.hp / h.max, 0) / Math.max(1, alive.length) < 0.5, bar = game.bag.findIndex((i) => i.kind === "bar");
      if (worn && bar >= 0 && !fl.restedAtDoor && game.bag.some((i) => i.kind === "ration") && !(f && f.type === "door")) {
        const door = CM.DIRS.map(([dx, dy]) => fl.features[`${fl.pos[0] + dx},${fl.pos[1] + dy}`]).find((d) => d && d.type === "door" && d.riddle === undefined && !fl.things[here]);
        if (door && !door.barred && game.give(bar, 0) === "") { this.tools.bars++; const again = game.bag.findIndex((i) => i.kind === "bar"); if (again >= 0 && game.give(again, 0) === "") this.tools.rests++; return "barred a door"; }
      }
      if (f && f.type === "plate" && f.trap && !f.spent && !f.gate && f.known && kit && game.give(game.bag.findIndex((i) => i.kind === "trapkit"), 0) === "") { this.tools.disarmed++; return "disarmed"; }
    }
    this.walk(fl);
    const target = this.pick();
    if (t && t.type === "event" && !t.done && !this.handled.has(fl.number + ":" + here)) {   // (asked once: "walk on" leaves the thing standing)
      this.handled.add(fl.number + ":" + here);
      const E = CM.EVENTS[t.event]; this.asked = null; game.use();
      if (this.asked) game.choose(here, Math.min(SAFE[t.event] === undefined ? E.options.length - 1 : SAFE[t.event], E.options.length - 1));
      return "chose";
    }
    if (t && t.type === "strongbox" && !t.opened && game.bag.some((i) => i.kind === "boxkey" && i.box === fl.number)) { game.use(); return "strongbox"; }
    if (t && t.type === "peddler" && !this.handled.has(fl.number + ":" + here)) { this.handled.add(fl.number + ":" + here); game.use(); if (game.shopping) { const row = game.stock.findIndex((i) => i.kind === "greaterheal" && i.value <= game.gold - 100); if (row >= 0) game.buy(row); game.closeBag(); } return "peddler"; }
    if (CM.guardianFor(fl.number) && !fl.oiled) {                        // a guardian's floor: the oils go on the front line
      fl.oiled = true;
      for (const h of alive.filter((p) => p.row === "front")) { const row = game.bag.findIndex((i) => i.kind === "oil"); if (row >= 0) game.give(row, game.party.indexOf(h)); }
    }
    if (!target) return this.giveUp(`no goal on floor ${fl.number}`);
    const step = this.stepTo(fl, target);
    if (step === "here") {
      if (fl.number === 0 && t && t.type === "building") { this.errand(t.id); return "errand"; }
      if (t && t.type === "node") game.use();
      else if (t && ["chest", "ladder", "phylactery", "stairs_up"].includes(t.type)) { const before = game.floor.number + ":" + game.mode; game.use(); if (game.floor.number + ":" + game.mode === before && t.type === "ladder") this.stuck++; }
      else if (t && t.type === "ghost") { game.talk(t, here); if (fl.things[here]) game.talk(t, here); if (fl.things[here] && !(t.arc && t.arc < 3)) delete fl.things[here]; else if (fl.things[here]) t.heard = true; }
      else if (f && f.type === "carving" && !f.read) { this.face(f.face); game.use(); if (!f.read) { this.stuck++; this.log.push("a wall that won't be read"); } }
      else if (t && t.type === "bones") { /* picked up by walking on it */ }
      else if (f && (f.type === "lever" || f.type === "plate")) { if (f.type === "lever") { this.face(f.face); game.use(); } if ((f.type === "lever" && !f.pulled) || (f.type === "plate" && f.gate && !f.pressed)) { this.stuck++; this.log.push("lever won't"); } }
      else if (t && t.type === "key") { /* taken as we stepped on it */ }
      else if (t && (t.type === "event" || t.type === "peddler" || t.type === "strongbox")) { this.stuck++; this.log.push(`${t.type} not taken at ${here}`); t.done = true; t.opened = true; delete fl.things[here]; }
      else { if (this.stuck > 6) return this.stop("nothing to do"); return this.giveUp(`nothing to do at ${here} on floor ${fl.number}`); }
      return "used";
    }
    if (step === null) return this.giveUp(`no way to ${target} on floor ${fl.number}`);
    this.face(step);
    const [dx, dy] = CM.DIRS[step], nk = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, nf = fl.features[nk];
    if (nf && nf.type === "door" && !nf.open && nf.riddle !== undefined && CM.RIDDLES[nf.riddle]) { game.answerRiddle(nk, CM.RIDDLES[nf.riddle].a); return "answered"; }
    const was = fl.pos.join(",");
    this.asked = null;
    game.move(0);
    if (this.asked && this.asked.parley) {                               // a guardian speaks first: the open gate if it offers one, else the fight
      const c = this.asked; this.asked = null;
      game.parley(c.k, c.options.length > 2 ? 2 : 0);
      return "parleyed";
    }
    if (game.mode === "explore" && game.floor === fl && fl.pos.join(",") === was) {
      if (nf && nf.type === "door" && nf.locked && !nf.open && game.hasKey() < 0) { if (++this.stuck > 40) return this.stop("a lock that won't give"); }
    }
    return "moved";
  }
};

// the toggle, on the game: Automatic on (the party plays on by itself) or off (the reins are yours)
Object.assign(CM.Game.prototype, {
  autoOn() { return Boolean(this.auto && this.auto.on); },
  autoPlay(on) {
    if (on === undefined) on = !this.autoOn();
    if (on) {
      if (this.mode === "title") return false;
      new CM.Autopilot(this, { warp: false, wake: false, sync: false });
      this.say("Automatic: the party plays on by itself - walks, fights, wears what is better, drinks what it needs, and trades at the camp. (Z, or a move key, takes the reins back.)");
      if (this.mode === "combat" && this.combat && !this.combat.auto) this.autoFight(true);
    } else if (this.auto) {
      this.auto.stop("the reins taken back"); this.auto = null;
      if (this.mode === "combat" && this.combat && this.combat.auto) this.autoFight(false);
      this.say("Automatic off: the reins are yours.");
    }
    this.emit("change");
    return true;
  },
});
