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
    this.opts = Object.assign({ maxFloor: 50, perFloor: 900, maxMoves: 60000, warp: false, wake: false, sync: false, land: false }, opts);
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
    { const dish = game.bag.findIndex((i) => i.kind === "dish"); if (dish >= 0 && ((game.fed || 0) >= CM.HUNGER.hungry || (!game.meal && game.mode === "explore"))) { game.give(dish, game.party.indexOf(this.alive()[0])); this.tools.dishes = (this.tools.dishes || 0) + 1; } }
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
    if (game.farmWants && game.farmWants() && !CM.isNight(game)) want.push("farm");
    if (this.canForge()) want.push("smith");
    if (this.opts.land && !CM.isNight(game) && game.overweight() < 0.6 && !(this.townDone || []).includes("land")) want.push("land");   // (a day in the land: forage, the open cave with a pick, then home by the gate)
    return want.filter((id) => !(this.townDone || []).includes(id));
  }
  canForge() {                                                           // a worn thing the pack's bars would grade
    const game = this.game; if (!game.inTown() || !CM.gradeCost) return false;
    return game.party.some((h) => ["weapon", "armor", "offhand", "helm"].some((slot) => { const it = h[slot]; if (!it || it.unknown || !CM.gradable(it) || (it.grade || 0) >= CM.GRADE_MOST) return false; const c = CM.gradeCost(it); return game.gold >= c.gold + 50 && game.bag.filter((i) => i.kind === "bar" && i.bar === c.metal).length >= c.bars; }));
  }
  kitchen() {                                                           // what the pack's things make, at the home's kitchen: up to six dishes
    const game = this.game; let made = 0;
    if (game.homeLevel() < 3) return 0;
    for (const id of Object.keys(CM.DISHES).sort((a, b) => CM.DISHES[b].floors - CM.DISHES[a].floors)) while (made < 6 && CM.canCook(game.bag, id) && game.cookDish(id) === "") made++;
    this.tools.cooked = (this.tools.cooked || 0) + made; return made;
  }
  forge() {                                                             // the grades the bars allow, the scrap sold, the picks whetted
    const game = this.game; let did = 0;
    for (const h of game.party) for (const slot of ["weapon", "armor", "offhand", "helm"]) { let guard = 0; while (this.canForge() && h[slot] && CM.gradable(h[slot]) && game.upgrade(game.party.indexOf(h), slot) === "" && guard++ < 5) did++; }
    if (game.bag.some((i) => i.kind === "scrap")) game.sellScrap();
    if (game.bag.some((i) => i.kind === "pick" && i.points !== undefined && i.points < CM.PICKS[i.pick].points) && game.gold > 60) game.whetPicks();
    this.tools.graded = (this.tools.graded || 0) + did; return did;
  }
  errand(id) {
    const game = this.game;
    this.townDone = (this.townDone || []).concat(id);
    game.use();                                                          // (the door opened: counted for the town's renown; the screen it opens is closed again by the frame loop)
    if (id === "home") { game.hearthRest(); while ((game.home().larder || 0) > 0 && game.bag.filter((i) => i.kind === "ration").length < 2) game.larderTake(); this.kitchen(); }
    else if (id === "smith") this.forge();
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
    if (game.overweight() > 0.8 && game.sellable("spare").rows.length) game.sellMany("spare");   // (the gear nobody wears, first)
    if (game.overweight() > 1) { let guard = 0; while (game.overweight() > 1 && guard++ < 40) { const row = game.bag.map((it, i) => [it, i]).filter(([it]) => CM.weightOf(it) >= 3 && it.kind !== "torch").sort((a, b) => a[0].value - b[0].value)[0]; if (!row) break; game.sell(row[1]); } }
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
    if (fl.number === 0) {                                               // the town: the errands' doors, then the shaft (or the scroll back down)
      for (const id of this.errands()) { const k = CM.TOWN_AT[id === "farm" || id === "land" ? "woodgate" : id].join(","); if (can(k)) return k; this.townDone = (this.townDone || []).concat(id); }
      if (game.bag.some((i) => i.kind === "scroll" && i.spell === "homecoming" && i.back)) return "scroll";
      return goal;
    }
    if (fl.number === -1) {                                              // the Wood: the farm if the trip is for it; a day in the land (the nodes, the open cave with a pick); then the gate home
      const farm = things.find(([, t]) => t.type === "farm"); if (this.farmTrip && farm && can(farm[0])) return farm[0];
      if (this.landTrip && !CM.isNight(game) && game.overweight() < 0.9 && (this.landMoves || 0) < 500) {
        const node = things.find(([k, t]) => t.type === "node" && can(k) && !this.handled.has("-1:" + k)); if (node) return node[0];
        const cave = things.find(([k, t]) => t.type === "cave" && t.n === CM.dayOf(game) % 3 && can(k) && !this.handled.has("-1:" + k)); if (cave && game.bag.some((i) => i.kind === "pick" && (i.points === undefined || i.points > 0))) return cave[0];
      }
      const gate = things.find(([, t]) => t.type === "woodgate"); return gate && can(gate[0]) ? gate[0] : null;
    }
    if (fl.number < -1) {                                                // a cave: its veins, then the way out
      const veins = things.filter(([k, t]) => t.type === "vein" && can(k) && !this.handled.has(fl.number + ":" + k) && CM.bestPick(game.bag, t.ore) >= 0).map(([k]) => k); if (veins.length && floorMoves < perFloor * 0.6) return veins[0];
      const exit = things.find(([, t]) => t.type === "caveexit"); return exit && can(exit[0]) ? exit[0] : null;
    }
    const phyl = things.find(([, t]) => t.type === "phylactery");
    if (phyl && can(phyl[0])) return phyl[0];
    const keys = things.filter(([k, t]) => (t.type === "key" || t.type === "errand") && can(k));   // (and an errand's thing)
    if (keys.length) return keys[0][0];
    const box = things.find(([, t]) => t.type === "strongbox" && !t.opened && game.bag.some((i) => i.kind === "boxkey" && i.box === fl.number));
    if (box && can(box[0])) return box[0];
    const ev = things.find(([k, t]) => (t.type === "event" && !t.done && !this.handled.has(fl.number + ":" + k)) || (t.type === "peddler" && !this.handled.has(fl.number + ":" + k)));
    if (ev && can(ev[0]) && floorMoves < perFloor * 0.6) return ev[0];
    const veins = things.filter(([k, t]) => t.type === "vein" && can(k) && !this.handled.has(fl.number + ":" + k) && CM.bestPick(game.bag, t.ore) >= 0).map(([k]) => k);
    if (veins.length && floorMoves < perFloor * 0.5) return veins[0];
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
  // the people's part: in the town, the errands that lie on its way taken and the done ones handed in, and a follower
  // hired - a torchbearer when no quiet one leads, a porter when the pack is heavy
  people(fl) {
    const game = this.game; if (!fl || fl.number !== 0 || this.peopleAt === game.tally.steps) return; this.peopleAt = game.tally.steps;
    for (const id of Object.keys(game.errands().taken)) if (!game.errandLeft(id)) { game.handInErrand(id); this.tools.errands = (this.tools.errands || 0) + 1; }
    for (const id of ["farm", "tavern", "temple", "merchant"]) if (game.errandOffered(id)) game.takeErrand(id);
    if (!game.follower && game.gold >= 200) { const lead = game.party.find((h) => h.hp > 0), quiet = lead && ["Rogue", "Ranger", "Monk"].includes(lead.cls);
      const id = game.overweight() > 0.7 ? "porter" : quiet ? null : "torchbearer"; if (id && !game.canHire(id)) { game.hireFollower(id); this.tools.hired = (this.tools.hired || 0) + 1; } }
  }
  // the light shaded near a sleeper when a Rogue, Ranger or Monk leads; lit again when nothing sleeps close
  stealth(fl) {
    const game = this.game; if (!fl || fl.number < 1 || !(game.light && game.light.kind)) return;
    const lead = game.party.find((h) => h.hp > 0), quiet = lead && ["Rogue", "Ranger", "Monk"].includes(lead.cls), [px, py] = fl.pos;
    const near = Object.entries(fl.things).some(([k, t]) => { if (t.type !== "monsters" || !t.asleep) return false; const [x, y] = k.split(",").map(Number); return Math.abs(x - px) + Math.abs(y - py) <= 7; });
    if (quiet && near && !game.lightOut) { game.douse(); this.tools.doused = (this.tools.doused || 0) + 1; }
    else if (game.lightOut && !(quiet && near)) game.douse();
  }
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
    if (game.floor.number === -1 && this.landTrip) this.landMoves = (this.landMoves || 0) + 1;
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
    this.stealth(fl); this.people(fl);
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
    if (target === "scroll") { const row = game.bag.findIndex((i) => i.kind === "scroll" && i.spell === "homecoming" && i.back); game.give(row, game.party.indexOf(alive[0])); return "back down"; }
    if (fl.number >= 1 && CM.isNight(game) && CM.hourOf(game) < 5 && (game.overweight() > 1 || alive.reduce((s, h) => s + h.hp / h.max, 0) / alive.length < 0.5) && this.nightHomeDay !== CM.dayOf(game)) {   // the small hours, and the party heavy or worn: home by the scroll to sleep, and back down by the same
      const row = game.bag.findIndex((i) => i.kind === "scroll" && i.spell === "homecoming" && !i.back);
      if (row >= 0) { this.nightHomeDay = CM.dayOf(game); if (game.give(row, game.party.indexOf(alive[0])) === "") { this.tools.nightHome = (this.tools.nightHome || 0) + 1; return "home for the night"; } }
    }
    if (fl.number >= 1 && game.overweight() > 1 && (game.tally.steps || 0) - (this.weightTripAt === undefined ? -1e9 : this.weightTripAt) > 400) {   // the pack over the line: home by the scroll to sell, and back by it
      const row = game.bag.findIndex((i) => i.kind === "scroll" && i.spell === "homecoming" && !i.back);
      if (row >= 0 && game.give(row, game.party.indexOf(alive[0])) === "") { this.weightTripAt = game.tally.steps || 0; this.tools.weightTrips = (this.tools.weightTrips || 0) + 1; return "home to sell"; }
    }
    if (fl.number >= 10 && !game.bag.some((i) => i.kind === "heal" || i.kind === "greaterheal") && game.gold >= 150) {   // out of potions and not of gold: home by the scroll, and back
      const row = game.bag.findIndex((i) => i.kind === "scroll" && i.spell === "homecoming" && !i.back);
      if (row >= 0 && game.give(row, game.party.indexOf(alive[0])) === "") { this.tools.homecomings = (this.tools.homecomings || 0) + 1; return "home by the scroll"; }
    }
    if (!target) return this.giveUp(`no goal on floor ${fl.number}`);
    const step = this.stepTo(fl, target);
    if (step === "here") {
      if (fl.number === 0 && t && t.type === "building") { this.errand(t.id); return "errand"; }
      if (fl.number === 0 && t && t.type === "woodgate") { this.farmTrip = game.farmWants && game.farmWants(); this.landTrip = this.opts.land && !(this.townDone || []).includes("land"); this.landMoves = 0; this.townDone = (this.townDone || []).concat("farm", "land"); game.use(); return this.landTrip ? "a day in the land" : "to the farm"; }
      if (fl.number === -1 && t && t.type === "node") { this.handled.add("-1:" + here); game.use(); this.tools.foraged = (this.tools.foraged || 0) + 1; return "foraged"; }
      if (fl.number === -1 && t && t.type === "cave") { this.handled.add("-1:" + here); game.use(); return game.floor.number < -1 ? "into the cave" : "the cave is shut"; }
      if (fl.number < -1 && t && t.type === "caveexit") { game.use(); return "out of the cave"; }
      if (fl.number === -1 && t && t.type === "farm") { this.farmTrip = false; this.tools.farmed = (this.tools.farmed || 0) + game.tendFarmAuto(); return "farmed"; }
      if (fl.number === -1 && t && t.type === "woodgate") { this.farmTrip = false; this.landTrip = false; game.use(); return "home from the Wood"; }
      if (t && t.type === "vein") { if (CM.bestPick(game.bag, t.ore) >= 0) game.use(); else { t.skip = true; this.handled.add(fl.number + ":" + here); } }
      else if (t && t.type === "node") game.use();
      else if (t && ["chest", "ladder", "phylactery", "stairs_up"].includes(t.type)) { const before = game.floor.number + ":" + game.mode; game.use(); if (game.floor.number + ":" + game.mode === before && t.type === "ladder") this.stuck++; }
      else if (t && t.type === "ghost") { game.talk(t, here); if (fl.things[here]) game.talk(t, here); if (fl.things[here] && !(t.arc && t.arc < 3)) delete fl.things[here]; else if (fl.things[here]) t.heard = true; }
      else if (f && f.type === "carving" && !f.read) { this.face(f.face); game.use(); if (!f.read) { this.stuck++; this.log.push("a wall that won't be read"); } }
      else if (t && t.type === "bones") { /* picked up by walking on it */ }
      else if (f && (f.type === "lever" || f.type === "plate")) { if (f.type === "lever") { this.face(f.face); game.use(); } if ((f.type === "lever" && !f.pulled) || (f.type === "plate" && f.gate && !f.pressed)) { this.stuck++; this.log.push("lever won't"); } }
      else if (t && t.type === "key") { /* taken as we stepped on it */ }
      else if (t && t.type === "errand") game.use();
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
      new CM.Autopilot(this, { warp: false, wake: false, sync: false, land: this.settings.autoLand !== false });   // (in the game, Automatic takes its day in the land too, unless Settings says not)
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
