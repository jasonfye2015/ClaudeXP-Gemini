"use strict";
// The King of the Tower (the twelfth update, phase 5): on the fortieth floor, in a hall broken only by pillars. He
// walks - keeping four to seven squares from the hero - and casts: a bolt (three at once once he is hurt), a ring of
// fire that grows out from him, a summoning of two of the tower's monsters, and a curse that slows the hero. And every
// 1 to 15 seconds (the dice say) he is gone in a burst of light and stands somewhere else in the hall, never within
// three squares of the hero nor in a wall. At half his health he speaks, and casts quicker. His fall: the tower is
// quiet, his circlet, a title, and the dais is the way out.
CM.TOWER_KING = { name: "The King of the Tower", colour: "#5A3A8A", body: "tall", head: "hood", eyes: "#E0C0FF", extras: ["robe", "cape", "crown", "staff", "glow"], speed: 11, towerKing: true, shape: [1, 1, 1] };
if (!CM.MONSTERS.some((m) => m.name === CM.TOWER_KING.name)) CM.MONSTERS.push(CM.TOWER_KING);   // (a kind of his own, in no pack)
{ const like = CM.BASES["Rat King's Crown"] || {}; CM.BASES["The King's Circlet"] = Object.assign({}, like, { id: "The King's Circlet", kind: "helm", slot: "helm", tier: 9, group: "relic" }); }   // (his relic's base)
CM.TK = { hp: 16, atk: 1.6, level: 4, tpMin: 1, tpMax: 15, tpNear: 3, castCd: 1.7, castCd2: 1.0, keepNear: 4, keepFar: 7, ringSpeed: 3.2, ringMax: 9, slow: 3, summonMost: 4, scale: 1.55 };
CM.TOWER_KING_LINES = {
  meet: "\"Another one with a little fire in the hand,\" says the King of the Tower, from his dais. \"Every one of them climbed all this way to give it to me.\"",
  half: "\"You are the first in a hundred years to make me move my feet,\" he says, and the hall grows cold. \"Good. Then I need not hold back.\"",
  fall: "The King of the Tower falls without a sound, and for the first time the tower is only stone. The dais holds a circlet, and the way out.",
};

Object.assign(CM.TowerRun.prototype, {
  addKing(rnd) {
    const B = this.fl.boss, o = this.makeMon(CM.TOWER_KING.name, B.x + 0.5, B.y + 0.5, this.level + CM.TK.level, rnd, { boss: true, king: true, aura: true, scale: CM.TK.scale, seen: true });
    o.m.max = o.m.hp = Math.round(o.m.max * CM.TK.hp); o.m.atk = Math.round(o.m.atk * CM.TK.atk); o.m.xp *= 12; o.m.gold *= 10; o.name = CM.TOWER_KING.name;
    o.krnd = new CM.Random(CM.hashSeed(`${this.game.seed}:towerking`)); o.tpAt = this.nextTeleport(o); o.casts = 0;
    this.rings = []; this.mons.push(o); this.boss = o; this.king = o;
    this.events.push({ kind: "kingspeaks", line: CM.TOWER_KING_LINES.meet });
  },
  nextTeleport(o) { return this.t + CM.TK.tpMin + o.krnd.next() * (CM.TK.tpMax - CM.TK.tpMin); },
  // where he may land: an open square of the hall, three or more from the hero
  teleportSpot(o) {
    const g = this.fl.grid, cells = [];
    for (let z = 1; z < g.length - 1; z++) for (let x = 1; x < g.length - 1; x++) if (g[z][x] === 0 && this.free(x + 0.5, z + 0.5, 0.35) && Math.hypot(x + 0.5 - this.x, z + 0.5 - this.z) >= CM.TK.tpNear) cells.push([x + 0.5, z + 0.5]);
    return cells.length ? cells[o.krnd.int(0, cells.length - 1)] : null;
  },
  kingStep(o, dt) {
    const K = CM.TK, d = Math.hypot(this.x - o.x, this.z - o.z), hurt = o.m.hp < o.m.max / 2;
    if (hurt && !o.spoke) { o.spoke = true; this.events.push({ kind: "kingspeaks", line: CM.TOWER_KING_LINES.half }); }
    if (this.t >= o.tpAt) {                                              // gone, and somewhere else
      const to = this.teleportSpot(o);
      if (to) { this.events.push({ kind: "teleport", from: [o.x, 0.6, o.z], to: [to[0], 0.6, to[1]] }); o.x = to[0]; o.z = to[1]; o.teleports = (o.teleports || 0) + 1; }
      o.tpAt = this.nextTeleport(o);
    }
    o.yaw = Math.atan2(this.x - o.x, -(this.z - o.z));
    if (d < K.keepNear) this.monMove(o, Math.atan2(o.x - this.x, -(o.z - this.z)), dt * 0.8);   // (too close: he steps back)
    else if (d > K.keepFar || !this.clear(o.x, o.z, this.x, this.z)) { const way = this.toward(o.x, o.z, this.x, this.z); if (way !== null) this.monMove(o, way, dt); }
    if (o.cd <= 0) { this.kingCast(o, hurt); o.cd = hurt ? K.castCd2 : K.castCd; }
    this.stepRings(dt);
  },
  kingCast(o, hurt) {
    const sees = this.clear(o.x, o.z, this.x, this.z), r = o.krnd.next(), summoned = this.living().filter((q) => q.summoned).length;
    o.casts += 1; o.lungeAt = this.t;
    if (r < 0.15 && summoned < CM.TK.summonMost) {                       // two of the tower's own, beside him
      const depth = CM.towerDepth(this.n), g = CM.deepGroup(depth, o.krnd, 2);
      for (let i = 0; i < 2; i++) { const a = o.krnd.next() * Math.PI * 2, x = o.x + Math.cos(a) * 1.2, z = o.z + Math.sin(a) * 1.2; if (this.free(x, z, 0.3)) this.mons.push(this.makeMon(g[0].kind || g[0].name, x, z, this.level, o.krnd, { summoned: true, seen: true })); }
      this.events.push({ kind: "kingcast", spell: "summon" }); return;
    }
    if (r < 0.35) { this.rings.push({ x: o.x, z: o.z, r: 0.3, hit: false, from: o }); this.events.push({ kind: "kingcast", spell: "ring" }); return; }
    if (r < 0.45 && sees) { this.slowT = CM.TK.slow; this.events.push({ kind: "kingcast", spell: "curse" }); return; }
    if (!sees) return;
    const base = Math.atan2(this.x - o.x, -(this.z - o.z));
    for (const dy of hurt ? [-0.16, 0, 0.16] : [0]) { const sp = CM.TF.boltSpeed * 1.2; this.bolts.push({ x: o.x + Math.sin(base + dy) * 0.5, z: o.z - Math.cos(base + dy) * 0.5, vx: Math.sin(base + dy) * sp, vz: -Math.cos(base + dy) * sp, life: 3, from: "mon", mon: o, layer: "fx:force", size: 0.28 }); }
    this.events.push({ kind: "kingcast", spell: "bolt" });
  },
  // the ring of fire: it grows out from where he stood; it burns the hero once as it passes, unless a pillar stands between
  stepRings(dt) {
    for (const g of this.rings) {
      g.r += CM.TK.ringSpeed * dt;
      const d = Math.hypot(this.x - g.x, this.z - g.z);
      if (!g.hit && Math.abs(d - g.r) < 0.3 && this.clear(g.x, g.z, this.x, this.z)) { g.hit = true; this.hurtHero(g.from, Math.max(1, Math.round(this.game.damage(Math.floor(g.from.m.atk / 2), 0, this.heroDf()) * 0.7))); }
    }
    this.rings = this.rings.filter((g) => g.r < CM.TK.ringMax);
  },
});
// the curse slows the hero's feet for a while
{ const step = CM.TowerRun.prototype.step;
  CM.TowerRun.prototype.step = function (dt, inp, first) {
    if (this.slowT > 0) { this.slowT -= dt; const keep = CM.TR.speed; CM.TR.speed = keep * 0.5; try { step.call(this, dt, inp, first); } finally { CM.TR.speed = keep; } return; }
    return step.call(this, dt, inp, first);
  }; }
// the rings, and the King's flicker, for the renderer
{ const sprites = CM.TowerRun.prototype.sprites;
  CM.TowerRun.prototype.sprites = function (now) {
    const out = sprites.call(this, now);
    for (const g of this.rings || []) for (let i = 0; i < 16; i++) { const a = (i / 16) * Math.PI * 2, x = g.x + Math.cos(a) * g.r, z = g.z + Math.sin(a) * g.r; out.push({ x: Math.floor(x), y: Math.floor(z), dx: x - Math.floor(x) - 0.5, dz: z - Math.floor(z) - 0.5, layer: "fx:fire", w: 0.4, h: 0.4, lift: 0.05, glow: 2 }); }
    return out;
  }; }
// his fall: the hall is quiet, the dais is the way out, the circlet, a title
{ const onFall = CM.TowerRun.prototype.onFall;
  CM.TowerRun.prototype.onFall = function (o) {
    if (!o.king) return onFall.call(this, o);
    this.rings = []; for (const q of this.living()) { q.m.hp = 0; q.fellAt = this.t; }
    this.fl.ladder = this.fl.dais.slice();
    const it = { name: "The King's Circlet", base: "The King's Circlet", kind: "helm", slot: "helm", power: 4, value: 3000, props: { relic: true, stats: { int: 2, wis: 2 }, towerRegen: 1 }, unknown: false };
    this.loot.push(it);
    if (this.game.findCard) { this.game.findCard("towerking:1", 1, "rare", "Beside the circlet:"); this.game.findCard("towerking:2", 1, "rare", "And another:"); }
    this.events.push({ kind: "kingdown", mon: o, item: it, line: CM.TOWER_KING_LINES.fall });
  }; }
// the circlet: magic comes back twice as fast in the tower
{ const step = CM.TowerRun.prototype.step;
  CM.TowerRun.prototype.step = function (dt, inp, first) { this.regenBonus = CM.equipped(this.hero).some((it) => it.props && it.props.towerRegen) ? 1 : 0; return step.call(this, dt, inp, first); }; }
