"use strict";
// The Mage Tower inside (the twelfth update, phase 2): one hero, in real time. CM.TowerRun keeps a floor of the tower
// and steps it on a fixed clock (CM.TR.step), so the same inputs at the same steps give the same run, and the Node tests
// drive it as the frame loop does. Nothing here touches the turn-by-turn rules: the hero's health, magic and arrows
// are spent here; experience, gold and things are counted and given to the party when the hero comes out.
//
//   run.update(dt, input)   input: { fwd, back, left, right, turnL, turnR, fire, spell, look (radians, used once) }
//   run.sprites(now)        the billboards for the renderer
//   run.events              what happened this frame, for the window's sounds and sparks (emptied by the window)
//
// Positions are in squares (x east, z south), the facing a yaw as the renderer's: 0 looks north (-z).
CM.TR = {
  step: 1 / 60, speed: 3.3, back: 0.7, strafe: 0.85, turn: 2.6, radius: 0.24, eye: 0.5,
  bolt: 9, arrow: 12, boltLife: 2.2, fireCd: 0.38, arrowCd: 0.55, spellCd: 1.2,
  regen: 0.4, arrowsStart: 40, quiver: 10, monRadius: 0.32,
};
// each calling's bolt and great spell: { bolt: the layer and the stat its power follows; spell: what the right hand does }
CM.TOWER_ARMS = {
  Mage: { bolt: "fx:spark", stat: "int", spell: "fireball", cost: 6, word: "Fireball" },
  Necromancer: { bolt: "fx:shard", stat: "int", spell: "drain", cost: 5, word: "Drain" },
  Druid: { bolt: "fx:leaf", stat: "wis", spell: "thorns", cost: 5, word: "Thorns" },
  Cleric: { bolt: "fx:spark", stat: "wis", spell: "smite", cost: 5, word: "Smite" },
  Bard: { bolt: "fx:spark", stat: "wis", spell: "song", cost: 5, word: "Lullaby" },
  Artificer: { bolt: "fx:fire", stat: "int", spell: "volley", cost: 5, word: "Firework" },
  archer: { bolt: "fx:arrow", stat: "dex", spell: "volley", cost: 3, word: "Volley", arrows: true },
};
CM.towerArms = (h) => (CM.TOWER_CASTERS.includes(h.cls) && !(h.weapon && h.weapon.props && h.weapon.props.bow) ? CM.TOWER_ARMS[h.cls] : CM.TOWER_ARMS.archer);

CM.TowerRun = class {
  constructor(game, heroIndex, n) {
    this.game = game; this.heroIndex = heroIndex; this.hero = game.party[heroIndex]; this.n = n;
    this.fl = CM.makeTowerFloor(n, game.seed);
    this.x = this.fl.start[0] + 0.5; this.z = this.fl.start[1] + 0.5; this.yaw = 0;
    this.arms = CM.towerArms(this.hero);
    this.arrows = this.arms.arrows ? CM.TR.arrowsStart : 0;
    this.t = 0; this.acc = 0; this.cool = 0; this.spellCool = 0; this.regenT = 0; this.bolts = []; this.events = [];
    this.xp = 0; this.gold = 0; this.loot = []; this.kills = 0; this.over = null; this.ids = 0;
    this.items = this.fl.items.map((it) => Object.assign({ taken: false }, it));
    const depth = CM.towerDepth(n), level = Math.max(1, Math.round(CM.monsterLevel(depth) * 0.85)), rnd = new CM.Random(CM.hashSeed(`${game.seed}:towerrun:${n}`));
    this.level = level;
    this.mons = this.fl.spawns.map((s) => this.makeMon(s.kind, s.x + 0.5, s.y + 0.5, level, rnd));
    if (this.addBoss) this.addBoss(rnd);                                 // (the floor's boss: phase 3)
  }
  makeMon(kind, x, z, level, rnd, extra) {
    const K = CM.monsterKind(kind) || CM.monsterKind("Goblin"), m = CM.makeMonster(K, level, rnd);
    return Object.assign({ id: ++this.ids, m, kind: K.name, x, z, home: [x, z], yaw: rnd.next() * Math.PI * 2, state: "idle", cd: 0, seen: false, fellAt: null, hitAt: null, lungeAt: null }, extra || {});
  }
  // ---- the grid ----
  solidAt(x, z) { const g = this.fl.grid, cx = Math.floor(x), cz = Math.floor(z); return !g[cz] || g[cz][cx] !== 0; }
  free(x, z, r = CM.TR.radius) { return !this.solidAt(x - r, z - r) && !this.solidAt(x + r, z - r) && !this.solidAt(x - r, z + r) && !this.solidAt(x + r, z + r); }
  // a clear line between two points (no wall square on it): the eyes' and the bolts' rule
  clear(x0, z0, x1, z1) { const d = Math.hypot(x1 - x0, z1 - z0), n = Math.ceil(d / 0.2); for (let i = 1; i < n; i++) { const k = i / n; if (this.solidAt(x0 + (x1 - x0) * k, z0 + (z1 - z0) * k)) return false; } return true; }
  living() { return this.mons.filter((o) => o.m.hp > 0); }
  // the way to a point, square by square: the yaw from (x, z) toward the next square on the shortest walk (the monsters'
  // chase, and the balance bot's); null when it is there or there is no way. The walk's map is kept per target square.
  toward(x, z, tx, tz) {
    const key = `${Math.floor(tx)},${Math.floor(tz)}`, g = this.fl.grid;
    this.ways = this.ways || new Map();
    if (!this.ways.has(key)) { if (this.ways.size > 64) this.ways.clear(); this.ways.set(key, CM.distances(g, [Math.floor(tx), Math.floor(tz)], (cx, cz) => g[cz] && g[cz][cx] === 0)); }
    const d = this.ways.get(key), cx = Math.floor(x), cz = Math.floor(z), here = d.get(`${cx},${cz}`);
    if (here === undefined) return null;
    if (here <= 1 || this.clear(x, z, tx, tz) && Math.hypot(tx - x, tz - z) < 3) return Math.atan2(tx - x, -(tz - z));
    let best = null; for (const [dx, dz] of CM.DIRS) { const n = d.get(`${cx + dx},${cz + dz}`); if (n !== undefined && n < here && (!best || n < best.n)) best = { n, x: cx + dx + 0.5, z: cz + dz + 0.5 }; }
    return best ? Math.atan2(best.x - x, -(best.z - z)) : null;
  }
  // ---- the clock ----
  update(dt, input = {}) {
    if (this.over) return;
    this.acc += Math.min(dt, 0.25);
    let first = true;
    while (this.acc >= CM.TR.step && !this.over) { this.acc -= CM.TR.step; this.step(CM.TR.step, input, first); first = false; }
  }
  step(dt, inp, first) {
    const T = CM.TR, h = this.hero;
    this.t += dt;
    // turning: the keys, and the mouse once a frame
    this.yaw += ((inp.turnR ? 1 : 0) - (inp.turnL ? 1 : 0)) * T.turn * dt + (first ? inp.look || 0 : 0);
    // moving: forward, back, sidestep; sliding along walls, never through a monster
    const fx = Math.sin(this.yaw), fz = -Math.cos(this.yaw), rx = Math.cos(this.yaw), rz = Math.sin(this.yaw);
    const f = (inp.fwd ? 1 : 0) - (inp.back ? T.back : 0), s = (inp.right ? T.strafe : 0) - (inp.left ? T.strafe : 0);
    let vx = (fx * f + rx * s) * T.speed * dt, vz = (fz * f + rz * s) * T.speed * dt;
    const len = Math.hypot(vx, vz), most = T.speed * dt; if (len > most) { vx *= most / len; vz *= most / len; }
    const blocked = (x, z) => !this.free(x, z) || this.living().some((o) => Math.hypot(o.x - x, o.z - z) < T.radius + T.monRadius);
    if (vx && !blocked(this.x + vx, this.z)) this.x += vx;
    if (vz && !blocked(this.x, this.z + vz)) this.z += vz;
    // the hands: the bolt, the great spell
    this.cool = Math.max(0, this.cool - dt); this.spellCool = Math.max(0, this.spellCool - dt);
    if (inp.fire && this.cool <= 0) this.fire();
    if (inp.spell && this.spellCool <= 0) this.cast();
    // magic comes back, slowly
    this.regenT += dt; if (this.regenT >= 1) { this.regenT -= 1; if (h.maxmp) h.mp = Math.min(h.maxmp, h.mp + Math.max(1, Math.round(h.maxmp * 0.04 * (1 + (this.regenBonus || 0))))); }
    this.stepBolts(dt);
    if (this.monsterStep) this.monsterStep(dt);                           // (the monsters' minds: phase 3)
    this.pickUp();
    this.lookT = (this.lookT || 0) + dt; if (this.lookT >= 0.2) { this.lookT = 0; this.see(); }
    if (h.hp <= 0 && !this.over) { this.over = "fell"; this.events.push({ kind: "fell" }); }
  }
  // the bolt's (or the arrow's) power: the hero's level and their calling's stat, or the bow
  power() {
    const h = this.hero, g = this.game, A = this.arms, st = g.stat(h, A.stat);
    if (A.arrows) return (h.weapon ? h.weapon.power : 2) + Math.max(0, CM.mod(st));
    return 3 + Math.floor(h.level * 0.9) + Math.max(0, CM.mod(st) * 2);
  }
  shoot(yaw, o = {}) {
    const A = this.arms, sp = A.arrows ? CM.TR.arrow : CM.TR.bolt;
    this.bolts.push(Object.assign({ x: this.x + Math.sin(yaw) * 0.3, z: this.z - Math.cos(yaw) * 0.3, vx: Math.sin(yaw) * sp, vz: -Math.cos(yaw) * sp, life: CM.TR.boltLife, from: "hero", layer: A.bolt, power: this.power(), mult: 1 }, o));
  }
  fire() {
    const A = this.arms;
    if (A.arrows) { if (this.arrows <= 0) { this.cool = 0.5; this.events.push({ kind: "empty" }); return; } this.arrows -= 1; }
    this.shoot(this.yaw); this.cool = A.arrows ? CM.TR.arrowCd : CM.TR.fireCd; this.events.push({ kind: "shoot", arrow: Boolean(A.arrows) });
  }
  // the great spell: dear in magic (or three arrows), on its own cooldown
  cast() {
    const A = this.arms, h = this.hero;
    if (A.arrows) { if (this.arrows < 3) return; this.arrows -= 3; }
    else { if ((h.mp || 0) < A.cost) { this.events.push({ kind: "nomagic" }); this.spellCool = 0.4; return; } h.mp -= A.cost; }
    this.spellCool = CM.TR.spellCd; this.events.push({ kind: "spell", spell: A.spell });
    if (A.spell === "fireball") this.shoot(this.yaw, { layer: "fx:fire", burst: 1.7, mult: 1.8, size: 0.4 });
    else if (A.spell === "smite") this.shoot(this.yaw, { layer: "fx:spark", mult: 3, size: 0.35 });
    else if (A.spell === "drain") this.shoot(this.yaw, { layer: "fx:shard", mult: 1.6, drain: 0.5 });
    else if (A.spell === "thorns" || A.spell === "volley") for (const d of [-0.18, 0, 0.18]) this.shoot(this.yaw + d, { mult: 1.1 });
    else if (A.spell === "song") { for (const o of this.living()) if (Math.hypot(o.x - this.x, o.z - this.z) < 5 && this.clear(this.x, this.z, o.x, o.z) && !o.boss) o.stunned = 2.5; this.events.push({ kind: "song" }); }
  }
  stepBolts(dt) {
    for (const b of this.bolts) {
      b.life -= dt;
      for (let k = 0; k < 4 && b.life > 0; k++) {
        b.x += b.vx * dt / 4; b.z += b.vz * dt / 4;
        if (this.solidAt(b.x, b.z)) { b.life = 0; this.events.push({ kind: "wall", at: [b.x - b.vx * dt / 4, 0.5, b.z - b.vz * dt / 4], layer: b.layer }); if (b.burst) this.burst(b); break; }
        if (b.from === "hero") { const o = this.living().find((q) => Math.hypot(q.x - b.x, q.z - b.z) < CM.TR.monRadius + 0.06); if (o) { b.life = 0; if (b.burst) this.burst(b); else this.strike(o, b); break; } }
        else if (this.boltHitsHero) { if (this.boltHitsHero(b)) break; }
      }
    }
    this.bolts = this.bolts.filter((b) => b.life > 0);
  }
  burst(b) { for (const o of this.living()) if (Math.hypot(o.x - b.x, o.z - b.z) < b.burst) this.strike(o, b); this.events.push({ kind: "burst", at: [b.x, 0.5, b.z] }); }
  // a bolt lands: the rules' own sum of a blow, the monster flinches, and falls
  strike(o, b) {
    const g = this.game, h = this.hero, eff = g.effective(h);
    let dmg = Math.ceil(g.damage(Math.ceil(eff.atk * 0.6), b.power, o.m.df) * (b.mult || 1));
    if (o.ward > 0) { o.ward -= 1; dmg = Math.ceil(dmg / 2); }
    o.m.hp -= dmg; o.hitAt = this.t; o.seen = true;
    if (b.drain) h.hp = Math.min(h.max, h.hp + Math.ceil(dmg * b.drain));
    this.events.push({ kind: "hit", at: [o.x, 0.5, o.z], amount: dmg, mon: o });
    if (o.m.hp <= 0) this.fall(o);
  }
  fall(o) {
    o.fellAt = this.t; this.kills += 1; this.xp += o.m.xp; this.gold += o.m.gold;
    this.events.push({ kind: "die", at: [o.x, 0.5, o.z], mon: o });
    if (this.onFall) this.onFall(o);
  }
  // the automap: what the hero has seen (within six squares, in a clear line), and where the hero stands
  see() {
    const fl = this.fl, seen = this.seenSet || (this.seenSet = new Set((fl.seen || []).map(([x, y]) => `${x},${y}`))), cx = Math.floor(this.x), cz = Math.floor(this.z);
    for (let dz = -6; dz <= 6; dz++) for (let dx = -6; dx <= 6; dx++) { const x = cx + dx, z = cz + dz, k = `${x},${z}`; if (seen.has(k) || !fl.grid[z] || fl.grid[z][x] === undefined) continue; if (this.clear(this.x, this.z, x + 0.5, z + 0.5) || fl.grid[z][x] !== 0 && this.clear(this.x, this.z, x + 0.5 - Math.sign(dx) * 0.6, z + 0.5 - Math.sign(dz) * 0.6)) { seen.add(k); fl.seen.push([x, z]); } }
    fl.pos = [cx, cz]; fl.facing = ((Math.round(this.yaw / (Math.PI / 2)) % 4) + 4) % 4;
  }
  // quivers and draughts lying about: walked over, taken
  pickUp() {
    for (const it of this.items) {
      if (it.taken || Math.hypot(it.x + 0.5 - this.x, it.y + 0.5 - this.z) > 0.55) continue;
      if (it.kind === "quiver" && !this.arms.arrows) continue;            // (a caster leaves the arrows)
      it.taken = true; const h = this.hero;
      if (it.kind === "quiver") this.arrows += CM.TR.quiver;
      else { h.hp = Math.min(h.max, h.hp + Math.ceil(h.max * 0.35)); if (h.maxmp) h.mp = Math.min(h.maxmp, h.mp + Math.ceil(h.maxmp * 0.35)); }
      this.events.push({ kind: "pickup", item: it.kind });
    }
  }
  // at the ladder: within a square of it, the boss down
  atLadder() { const L = this.fl.ladder; return Boolean(L && this.ladderOpen && this.ladderOpen() && Math.hypot(L[0] + 0.5 - this.x, L[1] + 0.5 - this.z) < 1.0); }
  // ---- what the renderer draws ----
  sprites(now) {
    const out = [], cell = (x, z) => ({ x: Math.floor(x), y: Math.floor(z), dx: x - Math.floor(x) - 0.5, dz: z - Math.floor(z) - 0.5 });
    for (const o of this.mons) {
      if (o.fellAt !== null && this.t - o.fellAt > 0.75) continue;
      const M = CM.motion({ now: this.t * 1000, phase: o.id * 1.7, hitAt: o.hitAt === null ? undefined : o.hitAt * 1000, lungeAt: o.lungeAt === null ? undefined : o.lungeAt * 1000, fellAt: o.fellAt === null ? undefined : o.fellAt * 1000, sway: Boolean(o.king), reduced: CM.reducedMotion });
      const S = o.scale || 1, ax = Math.sin(this.yaw), az = -Math.cos(this.yaw), away = M.back - M.forward;
      const c = cell(o.x + ax * away, o.z + az * away);
      if (o.aura) out.push(Object.assign({}, cell(o.x, o.z), { layer: "shadow", flat: true, w: 1.2 * S, alpha: 0.9, glow: 0 }));
      out.push(Object.assign(c, { layer: `monster:${o.kind}`, w: 0.85 * S, h: 0.85 * S * M.scaleY, tilt: M.tilt, skew: M.skew, alpha: M.alpha * (o.blink ? 0.4 : 1), flash: Math.max(M.flash, o.aura ? 0.18 + 0.1 * Math.sin(now / 250) : 0), shade: o.aura ? 1.25 : 1, lift: o.lift || 0 }));
    }
    for (const b of this.bolts) out.push(Object.assign(cell(b.x, b.z), { layer: b.layer, w: b.size || 0.22, h: b.size || 0.22, lift: 0.4, glow: 2, alpha: 1 }));
    for (const it of this.items) if (!it.taken) out.push({ x: it.x, y: it.y, layer: it.kind === "quiver" ? "fx:arrow" : "fx:holy", w: 0.45, h: 0.45, lift: 0.1, glow: 0.6 + 0.3 * Math.sin(now / 300 + it.x) });
    if (this.fl.ladder) out.push({ x: this.fl.ladder[0], y: this.fl.ladder[1], layer: "stairs_up", w: 0.6, h: 1.0, glow: this.ladderOpen && this.ladderOpen() ? 0.5 : 0, shade: this.ladderOpen && this.ladderOpen() ? 1 : 0.6 });   // (the ladder up: dim while it is guarded)
    return out;
  }
  // the view's lights: the hero's own glow, and the bolts in flight
  lights() {
    const out = [{ x: this.x, y: 0.6, z: this.z, reach: 4.2, colour: [0.55, 0.45, 0.85], flicker: false }];
    for (const b of this.bolts.slice(0, 8)) out.push({ x: b.x, y: 0.45, z: b.z, reach: 2.2, colour: b.from === "hero" ? (b.layer === "fx:fire" ? [1, 0.5, 0.2] : [0.7, 0.55, 1]) : [1, 0.3, 0.3], flicker: false });
    return out;
  }
};

Object.assign(CM.Game.prototype, {
  towerUse() { const run = this.towerRun; if (!run) return ""; if (run.atLadder()) return this.towerClimb(false); const L = run.fl.ladder; if (L && Math.hypot(L[0] + 0.5 - run.x, L[1] + 0.5 - run.z) < 1.2) { this.say("The ladder up - and the floor's boss stands between you and it."); } return ""; },
  // in at the doors: the floor after the last cleared, the hero alone (the others wait at the foot)
  enterMageTower(i) {
    const h = this.party[i], why = CM.towerWhyNot(h);
    if (why) return why;
    if (this.mode !== "explore" || !this.floor || this.floor.number !== -1) return "The doors are in the Wood.";
    if (this.tower && this.tower.cleared >= CM.TOWER_FLOORS) return "The tower is quiet now. Its King is gone, and nothing on its forty floors is waiting for anyone.";
    this.tower = this.tower || { cleared: 0, best: 0 };
    const n = Math.min(CM.TOWER_FLOORS, (this.tower.cleared || 0) + 1);
    this.logAct("enterMageTower", i);
    this.towerRun = new CM.TowerRun(this, i, n);
    this.say(`${h.name} goes in alone, and the doors close. ${CM.towerFloorName(n)}.`);
    this.setMode("tower");
    this.emit("towerfloor", this.towerRun);
    return "";
  },
  // what a floor won goes to the party as it is cleared (a fall later loses only the floor it happened on)
  bankTower(run) {
    const h = run.hero;
    if (run.xp) { h.xp += run.xp; this.checkLevels(); }
    if (run.gold) this.gold += run.gold;
    if (run.loot.length) this.gain(run.loot, "tower");
    const won = { xp: run.xp, gold: run.gold, things: run.loot.length }; run.xp = 0; run.gold = 0; run.loot = [];
    return won;
  },
  // the floor's ladder: the floor is counted cleared; up to the next, or out of the doors ("leave")
  towerClimb(leave = false) {
    const run = this.towerRun;
    if (!run || !run.atLadder()) return "The ladder is in the boss's room, and it is guarded until the boss falls.";
    this.logAct("towerClimb", leave);
    this.tower = this.tower || { cleared: 0, best: 0 };
    this.tower.cleared = Math.max(this.tower.cleared || 0, run.n); this.tower.best = Math.max(this.tower.best || 0, run.n);
    this.tally.towerBest = Math.max(this.tally.towerBest || 0, run.n);
    this.clock = (this.clock || 0) + CM.CLOCK.stair;                    // (an hour a floor, by the tower's own reckoning)
    const won = this.bankTower(run);
    this.say(`Floor ${run.n} of the Mage Tower cleared${won.xp || won.gold ? `: ${won.xp} experience, ${won.gold} gold${won.things ? `, ${CM.plural(won.things, "thing")}` : ""}` : ""}.`);
    if (run.n === 10) this.achieve("tower10");
    if (leave || run.n >= CM.TOWER_FLOORS) return this.leaveMageTower("cleared") ? "" : "";
    const next = new CM.TowerRun(this, run.heroIndex, run.n + 1);
    next.arrows = run.arrows; this.towerRun = next;
    this.say(`Up the ladder: ${CM.towerFloorName(next.n)}.`);
    this.emit("towerfloor", next);
    return "";
  },
  // out of the tower: what was won is the party's (but a fall loses the floor's gold and things); a floor not finished is not counted
  leaveMageTower(how = "left") {
    const run = this.towerRun;
    if (!run) return false;
    const h = run.hero;
    if (how === "fell") { h.hp = 1; run.gold = 0; run.loot = []; this.tally.towerFalls = (this.tally.towerFalls || 0) + 1; }
    const won = this.bankTower(run);
    this.say(how === "fell" ? `The tower puts ${h.name} out of its doors, barely breathing: the floor is lost.` : how === "cleared" ? `${h.name} comes out of the tower: floor ${run.n} cleared.` : `${h.name} comes back out of the doors.`);
    if (how !== "cleared" && (won.xp || won.gold)) this.say(`From the tower: ${won.xp} experience and ${won.gold} gold.`);
    if (this.tower && this.tower.cleared) this.say(`The tower will have you back at floor ${Math.min(CM.TOWER_FLOORS, this.tower.cleared + 1)}.`);
    this.towerRun = null;
    this.setMode("explore");
    this.floor.pos = CM.MAGE_DOOR.slice(); this.floor.facing = 2;
    this.saveRun();
    this.emit("floor", this.floor);
    return true;
  },
});
