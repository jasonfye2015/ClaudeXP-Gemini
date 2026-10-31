"use strict";
// The Mage Tower's monsters in real time, and its floor bosses (the twelfth update, phase 3). Laid on CM.TowerRun:
// each monster idles where it stands until it sees the hero (a clear line within its eyes' reach) or hears a shot
// close by; then it chases by the shortest walk and strikes when it is close, on a cooldown - or, if it is a kind
// that shoots or casts, keeps its distance and sends a bolt of its own. The floor's boss is one of the floor's kinds
// made more: larger, an aura, a champion's word that works here as it does below, far more health; it keeps its room
// until the hero comes in, and when it falls the ladder is open and it leaves something worth having.
CM.TF = { eyes: 8, bossEyes: 10, hear: 7, reach: 0.9, meleeCd: 1.25, rangedCd: 2.2, keep: 4, dodge: 0.12, bossScale: 1.45, bossHp: 2.6, bossAtk: 1.3, boltSpeed: 6.5 };
CM.TOWER_SHOOTERS = ["Goblin", "Dark Elf", "Shard Wisp", "Weed Hag", "Grave Priest", "Hedge Wizard", "Foundry Imp", "Bellows Imp", "Thorn Lotus", "Eel", "Demon", "Wyvern", "Spore Beast", "Prism Sentinel", "Grave Lantern"];
CM.towerShoots = (kind) => { const K = CM.monsterKind(kind) || {}; return CM.TOWER_SHOOTERS.includes(K.name) || K.ability === "ranged" || K.ability === "breath"; };

Object.assign(CM.TowerRun.prototype, {
  // the boss, in the ladder's room: one of the floor's kinds, made more
  addBoss(rnd) {
    const B = this.fl.boss; if (!B || B.king) { if (B && B.king && this.addKing) this.addKing(rnd); return; }
    const o = this.makeMon(B.kind, B.x + 0.5, B.y + 0.5, this.level + 2, rnd, { boss: true, aura: true, scale: CM.TF.bossScale });
    o.m.max = o.m.hp = Math.round(o.m.max * CM.TF.bossHp); o.m.atk = Math.round(o.m.atk * CM.TF.bossAtk); o.m.xp *= 4; o.m.gold *= 4;
    CM.makeChampion({ group: [o.m] }, B.word); o.word = B.word; o.name = o.m.name;
    if (B.word === "warded") o.ward = 3;
    if (B.word === "shadowed") o.blink = true;
    o.room = this.fl.rooms.find((r) => r.name === "The ladder's room");
    this.mons.push(o); this.boss = o;
  },
  inRoom(r, x, z) { return r && x >= r.x0 && x < r.x1 + 1 && z >= r.y0 && z < r.y1 + 1; },
  bossInSight() { const b = this.boss; return b && b.m.hp > 0 && (b.seen || (Math.hypot(b.x - this.x, b.z - this.z) < CM.TF.bossEyes && this.clear(this.x, this.z, b.x, b.z))) ? b : null; },
  ladderOpen() { return !this.boss || this.boss.m.hp <= 0; },
  // the monsters' turn, every step
  monsterStep(dt) {
    const T = CM.TF, h = this.hero, shot = this.lastShot !== undefined && this.t - this.lastShot < dt * 1.5;
    for (const o of this.mons) {
      if (o.m.hp <= 0) continue;
      o.cd = Math.max(0, o.cd - dt);
      if (o.stunned > 0) { o.stunned -= dt; continue; }
      if (o.king && this.kingStep) { this.kingStep(o, dt); continue; }
      const d = Math.hypot(this.x - o.x, this.z - o.z);
      if (!o.seen) {                                                     // idle: it has to see the hero, or hear a shot
        const sees = d < (o.boss ? T.bossEyes : T.eyes) && this.clear(o.x, o.z, this.x, this.z), hears = shot && d < T.hear;
        if (o.boss && !this.inRoom(o.room, this.x, this.z)) continue;   // (the boss waits in its room)
        if (sees || hears) { o.seen = true; this.events.push({ kind: "alert", mon: o }); if (o.word === "shrieking") for (const q of this.living()) q.seen = true; }
        else continue;
      }
      const shoots = CM.towerShoots(o.kind), sees = this.clear(o.x, o.z, this.x, this.z);
      o.yaw = Math.atan2(this.x - o.x, -(this.z - o.z));
      if (shoots && sees && d <= T.keep + 2.5) {                         // a shooter: stands off and shoots
        if (o.cd <= 0) { this.monShoot(o); o.cd = T.rangedCd * (o.word === "frenzied" && o.m.hp < o.m.max / 2 ? 0.5 : 1); }
        if (d < T.keep - 1) this.monMove(o, Math.atan2(o.x - this.x, -(o.z - this.z)), dt * 0.6);
        continue;
      }
      if (d <= T.reach) {                                                // close: a blow
        if (o.cd <= 0) { this.monStrike(o); o.cd = T.meleeCd * (o.word === "frenzied" && o.m.hp < o.m.max / 2 ? 0.5 : 1) * (o.word === "fleet" ? 0.7 : 1); }
        continue;
      }
      const way = sees && d < 2.5 ? o.yaw : this.toward(o.x, o.z, this.x, this.z);
      if (way !== null) this.monMove(o, way, dt);
    }
  },
  monSpeed(o) { return Math.min(2.6, 1.0 + (o.m.speed || 10) * 0.1) * (o.word === "fleet" ? 1.4 : 1) * (o.boss ? 0.9 : 1); },
  monMove(o, yaw, dt) {
    const sp = this.monSpeed(o) * dt, nx = o.x + Math.sin(yaw) * sp, nz = o.z - Math.cos(yaw) * sp, R = CM.TR.monRadius * (o.scale || 1) * 0.8;
    const ok = (x, z) => this.free(x, z, R) && Math.hypot(x - this.x, z - this.z) > CM.TR.radius + R && !this.living().some((q) => q !== o && Math.hypot(q.x - x, q.z - z) < R * 1.6) && (!o.room || this.inRoom(o.room, x, z));
    if (ok(nx, o.z)) o.x = nx;
    if (ok(o.x, nz)) o.z = nz;
  },
  // a blow: the rules' sum, the hero's armour, a dodge now and then
  heroDf() { const g = this.game; return g.effective(this.hero).df + CM.gearDefence(this.hero); },
  hurtHero(o, dmg) {
    const h = this.hero;
    h.hp -= dmg; this.events.push({ kind: "hurt", amount: dmg, mon: o });
    if (o.word === "vampiric") o.m.hp = Math.min(o.m.max, o.m.hp + Math.ceil(dmg / 2));
    if (o.blink) o.blink = false;                                        // (a shadowed one is seen once it strikes)
  },
  monStrike(o) {
    o.lungeAt = this.t;
    if (this.game.rnd.chance(CM.TF.dodge)) { this.events.push({ kind: "dodge", mon: o }); return; }
    this.hurtHero(o, this.game.damage(Math.floor(o.m.atk / 2), 0, this.heroDf()));
  },
  monShoot(o) {
    const yaw = Math.atan2(this.x - o.x, -(this.z - o.z)), sp = CM.TF.boltSpeed;
    this.bolts.push({ x: o.x + Math.sin(yaw) * 0.35, z: o.z - Math.cos(yaw) * 0.35, vx: Math.sin(yaw) * sp, vz: -Math.cos(yaw) * sp, life: 2.5, from: "mon", mon: o, layer: (CM.monsterKind(o.kind) || {}).ability === "breath" ? "fx:fire" : "fx:bolt", size: 0.2 });
    o.lungeAt = this.t; this.events.push({ kind: "monshoot", mon: o });
  },
  boltHitsHero(b) {
    if (Math.hypot(b.x - this.x, b.z - this.z) > CM.TR.radius + 0.12) return false;
    b.life = 0; const o = b.mon;
    if (this.game.rnd.chance(CM.TF.dodge)) { this.events.push({ kind: "dodge", mon: o }); return true; }
    this.hurtHero(o, Math.max(1, Math.round(this.game.damage(Math.floor(o.m.atk / 2), 0, this.heroDf()) * 0.85)));
    return true;
  },
  // when one falls: the boss's things, and the ladder open
  onFall(o) {
    if (!o.boss) return;
    const rnd = new CM.Random(CM.hashSeed(`${this.game.seed}:towerboss:${this.n}`)), depth = CM.towerDepth(this.n), it = CM.affix(CM.makeItem(depth + 2, rnd), depth + 6, rnd);
    it.unknown = false; this.loot.push(it);
    this.events.push({ kind: "bossdown", mon: o, item: it });
  },
});
// a shot rouses the room: the run remembers when the hero last fired
{ const fire = CM.TowerRun.prototype.fire, cast = CM.TowerRun.prototype.cast;
  CM.TowerRun.prototype.fire = function () { this.lastShot = this.t; return fire.call(this); };
  CM.TowerRun.prototype.cast = function () { this.lastShot = this.t; return cast.call(this); }; }
