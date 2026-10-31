"use strict";
// The island's life (the nineteenth update, phase 3 - v12.3): the island keeps the game's clock - a minute a second
// while a hero is there - with day, dusk, night and dawn; wildlife by day (deer and boar, for meat: the cook's); and in
// the dark - at night on the surface, at any hour in the caves - the game's own monsters, by depth: Giant Rats and
// Kobolds up top, Skeletons and Goblins in the caves, Wraiths and Gargoyles in the deep. They come only where it is
// dark, away from torches and from the light the hero carries. Fighting is in real time, with the hero's own weapon
// and the main game's damage sums (an island sword adds to a blow); a bow or a caster's bolt flies. Every kill pays a
// third of the rules' experience at once; Kobolds and Goblins drop gold; now and then a monster drops a thing.
// The island's gold and things are carried: a fall leaves them in the bundle with the satchel. 76h-claudecraft.js
// draws the creatures (in their own pictures, as billboards) and the sky; 80-main.js steps it all.
CM.CL = {
  minute: 1, xpShare: 0.33, hit: 0.55, reach: 3.2, swingCd: 0.45, shotCd: 0.55, shotSpeed: 22, shotLife: 1.4, monReach: 1.35, monCd: 1.15,
  calmAfter: 4, calmHeal: 0.02, goldShare: 1.2, shotMult: 1.5, spawnEvery: 1.6, capWild: 6, capFoe: 10, near: 14, far: 30, gone: 44, lootChance: 1 / 12, wildMeat: 1,
  WILD: ["Deer", "Deer", "Boar"], TOP: ["Giant Rat", "Kobold", "Giant Rat"], CAVE: ["Skeleton", "Goblin", "Kobold", "Giant Rat"], DEEP: ["Wraith", "Gargoyle", "Skeleton"],
  BANDS: { top: [1, 8], cave: [3, 20], deep: [8, 30] }, OFFSET: { top: -2, cave: 0, deep: 2 }, GOLD: ["Kobold", "Goblin"],   
  SIZE: { beast: [0.45, 1.0], small: [0.35, 1.1], biped: [0.35, 1.8], thin: [0.32, 1.8], wide: [0.55, 1.7], tall: [0.4, 2.2], ghost: [0.4, 1.9] },
};
CM.CC.ITEM[108] = { meat: "Deer" }; CM.CC.ITEM[109] = { meat: "Boar" }; CM.CC.NAMES[108] = "Deer meat"; CM.CC.NAMES[109] = "Boar meat"; CM.CC.ITEM_TILE[108] = "meat_deer"; CM.CC.ITEM_TILE[109] = "meat_boar";
CM.CC.TILE.meat_deer = 53; CM.CC.TILE.meat_boar = 54;
{ const goes = CM.CC.goesHome, home = CM.CC.toHome; CM.CC.goesHome = (b) => goes(b) || !!(CM.CC.ITEM[b] && CM.CC.ITEM[b].meat); CM.CC.toHome = (b) => (CM.CC.ITEM[b] && CM.CC.ITEM[b].meat ? CM.meat(CM.CC.ITEM[b].meat) : home(b)); }
// the day's light: full by day, falling at dusk, a little moonlight at night
CM.CL.daylight = (game) => { const h = CM.hourOf(game), [dawn, dusk] = CM.daylightOf ? CM.daylightOf(game) : [5, 21]; if (h >= dawn + 1.5 && h <= dusk - 1.5) return 1; if (h < dawn || h > dusk) return 0.12; return h < 12 ? 0.12 + 0.88 * (h - dawn) / 1.5 : 0.12 + 0.88 * (dusk - h) / 1.5; };
// (v12.8, tuned by tools/craftbot.js) a monster's level follows the hero's: a little under it up top, at it in the caves,
// over it in the deep, a night counted for every two, inside the band's bounds
CM.CL.levelFor = (band, heroLevel, nights = 0) => { const [lo, hi] = CM.CL.BANDS[band]; return Math.max(lo, Math.min(hi, (heroLevel || 1) + CM.CL.OFFSET[band] + Math.floor(nights / 2))); };
CM.CL.band = (world, x, y, z) => (y < 12 ? "deep" : world.skyOwn(x, y, z) > 0 ? "top" : "cave");

Object.assign(CM.Game.prototype, {
  craftLife() { const cr = this.craft; if (!cr) return null; if (!cr.life) { const K = this.craftStore(); cr.life = { mobs: [], shots: [], t: 0, spawnT: 1, swingT: 0, ids: 0, rnd: new CM.Random(CM.hashSeed(`${this.seed}:craftlife:${K.visits}`)), gold: 0, loot: [], kills: 0, xp: 0, night: CM.isNight(this) }; } return cr.life; },
  craftArms() { const h = this.craft.hero, A = CM.brArms(h); return A; },
  // the light where something stands, as a monster sees it: the sky's by the hour, or a torch's
  craftDarkAt(x, y, z) { const W = this.craft.world, xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z); return Math.max(W.skyAt(xi, yi, zi) * CM.CL.daylight(this), W.torchAt(xi, yi, zi)); },
  // may a monster come here? dark enough, not by a torch, out of the hero's own light, on something to stand on
  craftSpawnOk(x, y, z) {
    const cr = this.craft, W = cr.world, xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
    if (W.get(xi, yi, zi) || W.get(xi, yi + 1, zi) || !CM.CC.SOLID.has(W.get(xi, yi - 1, zi)) || W.get(xi, yi - 1, zi) === CM.CC.B.LEAVES) return false;
    if (this.craftDarkAt(x, y, z) > 0.3 || W.torchAt(xi, yi, zi) > 0.05) return false;
    const p = cr.walker.pos; return Math.hypot(p[0] - x, p[1] - y, p[2] - z) > Math.max(this.craftLight() + 2, 8);
  },
  craftMakeMob(kind, x, y, z, level) {
    const L = this.craftLife(), K = CM.monsterKind(kind), m = CM.makeMonster(K, level, L.rnd), [r, h] = CM.CL.SIZE[K.body] || CM.CL.SIZE.biped;
    const w = new CM.CC.Walker(this.craft.world, [x, y, z], L.rnd.int(0, 359), 0); w.canFly = false;
    return { id: ++L.ids, kind: K.name, K, m, w, r, h, level, wild: !!K.flees, hostile: !K.flees, cd: 0.6, shotT: 1 + L.rnd.next() * 2, hitAt: -9, fellAt: null, wanderT: 0, walk: false, stuck: 0, last: [x, z] };
  },
  // now and then, something comes: wildlife on the grass by day, monsters in the dark
  craftSpawn() {
    const cr = this.craft, L = this.craftLife(), W = cr.world, p = cr.walker.pos, R = L.rnd, K = this.craftStore(), nights = K.nights || 0;
    const near = (o) => Math.hypot(o.w.pos[0] - p[0], o.w.pos[2] - p[2]) < CM.CL.far;
    const day = CM.CL.daylight(this) > 0.6, wild = L.mobs.filter((o) => o.wild && !o.fellAt && near(o)).length, foes = L.mobs.filter((o) => !o.wild && !o.fellAt && near(o)).length;
    for (let tries = 0; tries < 6; tries++) {
      const a = R.next() * Math.PI * 2, d = CM.CL.near + R.next() * (CM.CL.far - CM.CL.near - 4), x = Math.floor(p[0] + Math.cos(a) * d) + 0.5, z = Math.floor(p[2] + Math.sin(a) * d) + 0.5;
      if (x < 2 || z < 2 || x > CM.CC.SIZE - 2 || z > CM.CC.SIZE - 2) continue;
      const top = W.top(Math.floor(x), Math.floor(z)), under = R.chance(0.6) && p[1] < top - 3;
      let y = top + 1; if (under) { y = null; for (let yy = Math.min(top - 2, Math.floor(p[1]) + 8); yy > Math.max(2, Math.floor(p[1]) - 10); yy--) if (!W.get(Math.floor(x), yy, Math.floor(z)) && CM.CC.SOLID.has(W.get(Math.floor(x), yy - 1, Math.floor(z)))) { y = yy; break; } if (y === null) continue; }
      if (!under && day && wild < CM.CL.capWild && W.get(Math.floor(x), top, Math.floor(z)) === CM.CC.B.GRASS && Math.hypot(p[0] - x, p[2] - z) > 10) { L.mobs.push(this.craftMakeMob(R.pick(CM.CL.WILD), x, y + 0.01, z, 1 + Math.min(4, nights))); return true; }
      if (foes >= CM.CL.capFoe || !this.craftSpawnOk(x, y, z)) continue;
      const band = CM.CL.band(W, Math.floor(x), y, Math.floor(z)), [lo, hi] = CM.CL.BANDS[band], list = band === "deep" ? CM.CL.DEEP : band === "cave" ? CM.CL.CAVE : CM.CL.TOP;
      L.mobs.push(this.craftMakeMob(R.pick(list), x, y + 0.01, z, CM.CL.levelFor(band, cr.hero.level, nights))); return true;
    }
    return false;
  },
  // a blow, a shot or a bolt, by the hero's own arms: what it struck, if anything
  // (fire: F - a bow or a caster shoots; otherwise, and with the left button, a blow at what is in reach)
  craftAttack(fire) {
    const cr = this.craft; if (!cr) return null; const L = this.craftLife(); if (L.swingT > 0) return null;
    const A = this.craftArms(), w = cr.walker, e = w.eye(), d = w.look();
    if (fire && A.ranged) { L.swingT = CM.CL.shotCd; L.shots.push({ from: "hero", x: e[0] + d[0] * 0.5, y: e[1] + d[1] * 0.5 - 0.15, z: e[2] + d[2] * 0.5, v: d.map((c) => c * CM.CL.shotSpeed), life: CM.CL.shotLife, power: this.craftShotPower(), kind: A.shot }); L.events = (L.events || []).concat([{ kind: "shoot", shot: A.shot }]); return "shot"; }
    const [blk] = cr.world.raycast(e, d, CM.CL.reach), bd = blk ? Math.hypot(blk[0] + 0.5 - e[0], blk[1] + 0.5 - e[1], blk[2] + 0.5 - e[2]) - 0.5 : Infinity;
    const o = this.craftMobOnRay(e, d, Math.min(CM.CL.reach, bd)); if (!o) return null;
    L.swingT = CM.CL.swingCd; this.craftStrike(o, this.craftBlow(o)); return o;
  },
  craftMobOnRay(e, d, reach) {
    let best = null, bt = reach;
    for (const o of this.craftLife().mobs) {
      if (o.fellAt) continue; const m = 0.2, lo = [o.w.pos[0] - o.r - m, o.w.pos[1] - m, o.w.pos[2] - o.r - m], hi = [o.w.pos[0] + o.r + m, o.w.pos[1] + Math.max(o.h, 1.4) + m, o.w.pos[2] + o.r + m]; let t0 = 0, t1 = bt, ok = true;
      for (let i = 0; i < 3 && ok; i++) { if (Math.abs(d[i]) < 1e-9) { if (e[i] < lo[i] || e[i] > hi[i]) ok = false; continue; } let a = (lo[i] - e[i]) / d[i], b = (hi[i] - e[i]) / d[i]; if (a > b) [a, b] = [b, a]; t0 = Math.max(t0, a); t1 = Math.min(t1, b); if (t0 > t1) ok = false; }
      if (ok && t0 < bt) { bt = t0; best = o; }
    }
    return best;
  },
  // a blow's worth: the main game's sum with the hero's weapon, and the best island sword (worn by it)
  craftBlow(o) {
    const cr = this.craft, h = cr.hero, eff = this.effective(h), sw = cr.satchel.best("sword"), power = (h.weapon ? h.weapon.power || 1 : 1) + (sw ? sw[1].power : 0);
    if (sw) this.craftWear(sw[0]);
    return Math.max(1, Math.round(this.damage(eff.atk, power, o.m.df) * (h.cls === "Rogue" && this.craftLife().rnd.chance(0.25) ? 2 : 1)));
  },
  craftShotPower() { const h = this.craft.hero, A = CM.towerArms ? CM.towerArms(h) : null, st = A ? this.stat(h, A.stat) : 10; return Math.round(((A && A.arrows ? (h.weapon ? h.weapon.power : 2) : 2) + Math.floor(h.level * 1.3) + Math.max(0, CM.mod(st) * 2)) * CM.CL.shotMult); },
  craftStrike(o, dmg) {
    const L = this.craftLife(); o.m.hp -= dmg; o.hitAt = L.t; (L.events = L.events || []).push({ kind: "hit", mob: o, amount: dmg });
    if (o.wild) { o.flee = 4; if (o.kind === "Boar") { o.wild = false; o.hostile = true; } }
    const p = this.craft.walker.pos, k = Math.hypot(o.w.pos[0] - p[0], o.w.pos[2] - p[2]) || 1; o.w.vel[1] = Math.max(o.w.vel[1], 3); o.push = [((o.w.pos[0] - p[0]) / k) * 4, ((o.w.pos[2] - p[2]) / k) * 4, 0.18];
    if (o.m.hp <= 0) this.craftFell(o);
  },
  // a kill: a third of the rules' experience at once, gold from those that carry it, meat from the wild, now and then a thing
  craftFell(o) {
    const cr = this.craft, L = this.craftLife(), h = cr.hero; o.fellAt = L.t; L.kills += 1; this.tally.craftKills = (this.tally.craftKills || 0) + 1;
    const xp = Math.max(1, Math.round(o.m.xp * CM.CL.xpShare)); h.xp += xp; L.xp += xp; this.checkLevels && this.checkLevels();
    const bits = [`+${xp} experience`];
    if (CM.CL.GOLD.includes(o.kind)) { const gold = Math.max(1, Math.round(o.m.gold * CM.CL.goldShare)); L.gold += gold; bits.push(`${gold} gold`); }
    if (o.K.flees || o.kind === "Boar") { const meat = o.kind === "Boar" ? 109 : 108; if (cr.satchel.add(meat, CM.CL.wildMeat)) bits.push(CM.CC.NAMES[meat].toLowerCase()); }
    else if (L.rnd.chance(CM.CL.lootChance)) { const depth = Math.max(1, Math.min(CM.BOTTOM || 50, Math.round(o.level * 1.5))), it = CM.makeItem(depth, L.rnd); L.loot.push(it); bits.push(`${it.unknown ? "something" : it.name}!`); }
    this.craftSay(`${o.kind}: ${bits.join(", ")}`); L.events.push({ kind: "die", mob: o });
  },
  // a monster's blow or shot on the hero: the main game's sum against their defence, scaled as the Fortress scales it
  craftHurtBy(o, frac = 1) {
    const h = this.craft.hero, df = this.effective(h).df + (CM.gearDefence ? CM.gearDefence(h) : 0);
    const dmg = Math.max(1, Math.round(this.damage(Math.floor(o.m.atk / 2), 0, df) * CM.CL.hit * frac * Math.pow(Math.min(2, Math.max(0.3, o.level / Math.max(1, h.level))), 0.6)));
    (this.craftLife().events = this.craftLife().events || []).push({ kind: "hurt", mob: o, amount: dmg });
    return this.craftHurt(dmg, `${o.kind}`);
  },
  // the island's minute: the clock, the creatures, the shots
  craftTick(dt) {
    const cr = this.craft; if (!cr) return; const L = this.craftLife(), W = cr.world, p = cr.walker.pos, K = this.craftStore();
    L.t += dt; L.swingT = Math.max(0, L.swingT - dt);
    L.minutes = (L.minutes || 0) + dt * CM.CL.minute; const whole = Math.floor(L.minutes); if (whole) { L.minutes -= whole; this.clock = (this.clock || 0) + whole; }   // (a minute a second, the game's own clock, in whole minutes)
    const night = CM.isNight(this); if (night && !L.night) { K.nights = (K.nights || 0) + 1; this.craftSay("Night falls on the island. Things stir in the dark."); } if (!night && L.night) this.craftSay("Dawn: the island's monsters go back into the dark."); L.night = night;
    if ((L.spawnT -= dt) <= 0) { L.spawnT = CM.CL.spawnEvery; this.craftSpawn(); }
    { const h = cr.hero; if (L.t - (L.hurtAt === undefined ? -99 : L.hurtAt) > CM.CL.calmAfter && (h.hp < h.max || h.mp < h.maxmp)) { L.mend = (L.mend || 0) + dt * CM.CL.calmHeal; const k = Math.floor(L.mend * 100); if (k) { L.mend -= k / 100; h.hp = Math.min(h.max, h.hp + Math.max(1, Math.round(h.max * k / 100))); h.mp = Math.min(h.maxmp, h.mp + Math.round(h.maxmp * k / 100)); } } }   // (calm, the hero mends: as in the Mage Tower)
    this.craftLairs(dt);
    for (const o of L.mobs) this.craftStepMob(o, dt);
    L.mobs = L.mobs.filter((o) => !(o.fellAt !== null && L.t - o.fellAt > 0.8) && Math.hypot(o.w.pos[0] - p[0], o.w.pos[2] - p[2]) < CM.CL.gone && o.w.pos[1] > -5 && !(o.hostile && !o.wild && o.dawnGone));
    for (const s of L.shots) this.craftStepShot(s, dt);
    L.shots = L.shots.filter((s) => s.life > 0);
    void W;
  },
  craftStepMob(o, dt) {
    if (o.fellAt !== null) return; const cr = this.craft, L = this.craftLife(), p = cr.walker.pos, w = o.w, dx = p[0] - w.pos[0], dz = p[2] - w.pos[2], dy = p[1] - w.pos[1], d = Math.hypot(dx, dz), R = L.rnd;
    o.cd = Math.max(0, o.cd - dt); const k = { fwd: false, jump: false, sprint: false };
    if (o.push) { o.push[2] -= dt; const np = [w.pos[0] + o.push[0] * dt, w.pos[1], w.pos[2] + o.push[1] * dt]; if (!w.boxHits(np[0], np[1], np[2])) w.pos = np; if (o.push[2] <= 0) o.push = null; }
    if (!o.wild && CM.CL.daylight(this) > 0.6 && CM.CL.band(cr.world, Math.floor(w.pos[0]), Math.floor(w.pos[1]), Math.floor(w.pos[2])) === "top" && d > 12) o.dawnGone = true;   // (at dawn, those up top slink off)
    if (o.wild) {
      if (o.flee > 0 || d < 5) { o.flee = Math.max(0, (o.flee || 0) - dt); w.yaw = (Math.atan2(dx, dz) * 180) / Math.PI; k.fwd = true; k.sprint = true; }   // (away: yaw faces along -look, so the hero is behind)
      else { o.wanderT -= dt; if (o.wanderT <= 0) { o.wanderT = 2 + R.next() * 3; o.walk = R.chance(0.5); w.yaw = R.int(0, 359); } k.fwd = o.walk; }
    } else if (d < 26 && Math.abs(dy) < 12) {
      w.yaw = (Math.atan2(-dx, -dz) * 180) / Math.PI;
      const ranged = o.K.ability === "ranged";
      if (d < CM.CL.monReach && Math.abs(dy) < 1.6) { if (o.cd <= 0) { o.cd = CM.CL.monCd; o.lungeAt = L.t; this.craftHurtBy(o); } }
      else if (ranged && d < 12 && d > 3 && this.craftClear(w.eye(), cr.walker.eye())) { o.shotT -= dt; if (o.shotT <= 0) { o.shotT = 2.4; const e = w.eye(), t = cr.walker.eye(), n = Math.hypot(t[0] - e[0], t[1] - e[1], t[2] - e[2]) || 1; L.shots.push({ from: o, x: e[0], y: e[1] - 0.3, z: e[2], v: [(t[0] - e[0]) / n * 12, (t[1] - 0.3 - e[1]) / n * 12, (t[2] - e[2]) / n * 12], life: 1.6, kind: "arrow" }); (L.events = L.events || []).push({ kind: "monshoot", mob: o }); } }
      else k.fwd = true;
    }
    const before = [w.pos[0], w.pos[2]]; w.update(dt, k);
    if (k.fwd && w.onGround && Math.hypot(w.pos[0] - before[0], w.pos[2] - before[1]) < 0.2 * dt) { o.stuck += dt; if (o.stuck > 0.15) { w.vel[1] = CM.CC.JUMP; o.stuck = 0; } } else o.stuck = 0;   // (a step up: a hop)
    w.fallFrom = null; w.landed = 0;
  },
  // (v12.5) a lair near the hero sends out the deep's kinds until it is broken
  craftLairs(dt) {
    const cr = this.craft, W = cr.world, L = this.craftLife(), p = cr.walker.pos, nights = this.craftStore().nights || 0;
    for (const f of W.finds || []) {
      if (f.kind !== "lair" || W.get(f.x, f.y, f.z) !== CM.CC.B.LAIR || Math.hypot(f.x + 0.5 - p[0], f.y - p[1], f.z + 0.5 - p[2]) > 14) continue;
      f.t = (f.t === undefined ? 1 : f.t) - dt; if (f.t > 0) continue; f.t = 4;
      const key = `${f.x},${f.y},${f.z}`; if (L.mobs.filter((o) => o.lair === key && o.fellAt === null).length >= 4) continue;
      for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const x = f.x + dx, z = f.z + dz; if (W.get(x, f.y, z) || W.get(x, f.y + 1, z)) continue; const o = this.craftMakeMob(L.rnd.pick(CM.CL.DEEP), x + 0.5, f.y + 0.01, z + 0.5, Math.min(30, CM.CL.levelFor("deep", cr.hero.level, nights) + 1)); o.lair = key; o.m.xp = Math.ceil(o.m.xp / 2); L.mobs.push(o); (L.events = L.events || []).push({ kind: "spawn" }); break; }
    }
  },
  // (v12.5) an old chest opened: gold and a thing by its depth, a map fragment from the sunken ones and the ruins; it
  // stays an empty chest (kept in the island's edits)
  craftOpenTreasure(key) {
    const cr = this.craft, W = cr.world, K = this.craftStore(), L = this.craftLife(), [x, y, z] = key.split(",").map(Number);
    if (W.get(x, y, z) !== CM.CC.B.TREASURE) return null;
    const f = (W.finds || []).find((q) => q.x === x && q.y === y && q.z === z), kind = f ? f.kind : y < 12 ? "lair" : "ruin", depth = f ? f.depth : kind === "lair" ? 25 : 6, R = new CM.Random(CM.hashSeed(`${this.seed}:islandchest:${key}`));
    const gold = Math.round((20 + depth * 6) * (0.75 + R.next() * 0.5)); let it = CM.makeItem(depth, R); if (R.chance(0.5) && CM.affix) it = CM.affix(it, depth, R) || it;
    L.gold += gold; L.loot.push(it); const frag = kind !== "lair"; if (frag) K.fragments = (K.fragments || 0) + 1;
    W.set(x, y, z, CM.CC.B.CHEST); K.opened = (K.opened || 0) + 1; this.tally.islandChests = (this.tally.islandChests || 0) + 1;
    this.craftSay(`The old chest: ${gold} gold, ${it.unknown ? "something wrapped in oilcloth" : it.name}${frag ? `, and a scrap of map (${K.fragments} of 4)` : ""}.`);
    if (frag && K.fragments === 4) this.craftSay("Four scraps make a map: it marks a place deep under the island's highest hill.");
    (L.events = L.events || []).push({ kind: "treasure" }); this.saveVillage && this.saveVillage();
    return { gold, item: it, fragment: frag, depth };
  },
  // (v12.5) the map: four fragments mark the vault under the highest hill
  craftMap() { const K = this.craftStore(); return (K.fragments || 0) >= 4 && this.craft ? this.craft.world.vault : null; },
  craftClear(a, b) { const W = this.craft.world, n = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]) * 2); for (let i = 1; i < n; i++) { const t = i / n; if (CM.CC.SOLID.has(W.get(Math.floor(a[0] + (b[0] - a[0]) * t), Math.floor(a[1] + (b[1] - a[1]) * t), Math.floor(a[2] + (b[2] - a[2]) * t)))) return false; } return true; },
  craftStepShot(s, dt) {
    const cr = this.craft, W = cr.world; s.life -= dt; if (s.from === "hero") s.v[1] -= (s.kind === "arrow" ? 6 : 0) * dt; else s.v[1] -= 3 * dt;
    const steps = 4; for (let i = 0; i < steps && s.life > 0; i++) {
      s.x += s.v[0] * dt / steps; s.y += s.v[1] * dt / steps; s.z += s.v[2] * dt / steps;
      if (CM.CC.SOLID.has(W.get(Math.floor(s.x), Math.floor(s.y), Math.floor(s.z)))) { s.life = 0; return; }
      if (s.from === "hero") { for (const o of this.craftLife().mobs) if (!o.fellAt && Math.abs(o.w.pos[0] - s.x) < o.r + 0.2 && Math.abs(o.w.pos[2] - s.z) < o.r + 0.2 && s.y > o.w.pos[1] - 0.2 && s.y < o.w.pos[1] + Math.max(o.h, 1.4) + 0.2) { s.life = 0; this.craftStrike(o, Math.max(1, Math.round(s.power + this.craftLife().rnd.int(0, Math.max(1, Math.floor(s.power / 2))) - Math.floor(o.m.df / 2)))); return; } }
      else { const p = cr.walker.pos; if (Math.abs(p[0] - s.x) < 0.4 && Math.abs(p[2] - s.z) < 0.4 && s.y > p[1] && s.y < p[1] + 1.8) { s.life = 0; this.craftHurtBy(s.from, 0.8); return; } }
    }
  },
});
