"use strict";
// The living dungeon (the eleventh update, phase 1): lairs and sleepers, the party's light and noise, sneaking, and
// champions. Laid over a floor after it is made (CM.makeLairs, from a hash of its own - the floor's walls, chests and
// way down never move, and its fingerprint is the same), and read by the monsters' turn (wanderMonsters), the step
// (move) and the fight.
//
//   a pack asleep (thing.asleep) lies where it is and does not wander; the party's light seen down a straight line
//   wakes it at once, the party's noise (this.noiseLevel, squares of reach through open floor, a closed door costing
//   four) may wake it each turn; a woken pack hunts (thing.hunting, turns) - it comes for the party from anywhere
//   on the floor. Walking into a sleeping pack gives a free round in which every blow lands.
//   the torch doused (this.lightOut): no light to be seen by, half the noise, and two squares of sight; a Rogue,
//   Ranger or Monk in front halves the noise again.
//   champions: a leader with a word (CM.CHAMPIONS), from floor CM.CHAMPION_FROM, a quarter of the packs.
CM.LAIR = { share: 0.6, wakeChance: 0.5, noiseDecay: 0.5, doorCost: 4, hunt: 24, lairReach: 3, fromStair: 5 };
CM.LIGHT_REACH = { torch: 8, lantern: 10, glow: 5, spell: 8, low: 6 };
CM.NOISE = { step: 2, heavy: 2, run: 1, door: 4, chest: 4, fight: 9, spell: 4, mine: 8 };
CM.CHAMPION_FROM = 6;
CM.CHAMPION_SHARE = 0.25;
CM.CHAMPIONS = {
  warded: { name: "Warded", blurb: "a ward that drinks the first spell cast at it" },
  frenzied: { name: "Frenzied", blurb: "under half its strength, it strikes twice a round" },
  shrieking: { name: "Shrieking", blurb: "its first cry wakes every lair on the floor" },
  shadowed: { name: "Shadowed", blurb: "unseen until it strikes - a Rogue sees it" },
  stonehide: { name: "Stonehide", blurb: "the first blow a round glances off" },
  vampiric: { name: "Vampiric", blurb: "its blows feed it" },
  hoarder: { name: "Hoarder", blurb: "carries a chest's worth" },
  fleet: { name: "Fleet", blurb: "acts twice a round" },
};

// a champion: the pack's leader, named for its word, tougher, worth more
CM.makeChampion = function (t, id) {
  const C = CM.CHAMPIONS[id], m = t.group[0];
  if (!C || !m || m.elite || m.champion) return t;
  m.champion = id; m.name = `${C.name} ${m.name}`;
  m.max = Math.round(m.max * 1.4); m.hp = m.max; m.xp = Math.round(m.xp * 2); m.gold = Math.round(m.gold * (id === "hoarder" ? 6 : 2));
  if (id === "fleet") m.speed = (m.speed || 10) + 4;
  t.champion = id;
  return t;
};

// the lairs, laid over a fresh floor: three packs in five asleep, a sleeper drawn into the nearest dead end within
// three squares (if one is free and not by the stair); a quarter of the packs below CM.CHAMPION_FROM led by a champion
CM.makeLairs = function (fl, seed) {
  if (!fl || !(fl.number >= 1) || !fl.things) return fl;
  const start = fl.pos || [1, 1], open = (x, y) => CM.isOpen(fl, x, y), fromStart = CM.distances(fl.grid, start, open);
  const deadEnd = (x, y) => CM.openNeighbours(fl, x, y).length === 1;
  for (const k of Object.keys(fl.things).sort()) {
    const t = fl.things[k];
    if (!t || t.type !== "monsters" || t.still || t.hunter || t.wood || t.mimicOf || !t.group || !t.group.length) continue;
    const h = CM.hashSeed(`${seed}:lair:${fl.number}:${k}`), roll = (n) => (Math.floor(h / n) % 1000) / 1000;
    if (fl.number >= CM.CHAMPION_FROM && roll(1) < CM.CHAMPION_SHARE) { const ids = Object.keys(CM.CHAMPIONS); CM.makeChampion(t, ids[Math.floor(h / 7) % ids.length]); }
    if (roll(1000) >= CM.LAIR.share) continue;
    t.asleep = true;
    const [x, y] = k.split(",").map(Number);
    if (deadEnd(x, y)) continue;
    const near = CM.distances(fl.grid, [x, y], open), spots = [];
    for (const [nk, d] of near) {
      if (d < 1 || d > CM.LAIR.lairReach || fl.things[nk] || fl.features[nk]) continue;
      const [nx, ny] = nk.split(",").map(Number);
      if (deadEnd(nx, ny) && (fromStart.get(nk) || 0) > CM.LAIR.fromStair) spots.push([d, nk]);
    }
    spots.sort((a, b) => a[0] - b[0] || (a[1] < b[1] ? -1 : 1));
    if (spots.length) { delete fl.things[k]; fl.things[spots[0][1]] = t; }
  }
  return fl;
};

// how far noise carries: open floor a square a square, a closed door CM.LAIR.doorCost; walls stop it
CM.noiseDistances = function (fl, from) {
  const size = fl.grid.length, out = new Map([[`${from[0]},${from[1]}`, 0]]), queue = [[from[0], from[1], 0]];
  while (queue.length) {
    queue.sort((a, b) => a[2] - b[2]);
    const [x, y, d] = queue.shift();
    for (const [dx, dy] of CM.DIRS) {
      const nx = x + dx, ny = y + dy, nk = `${nx},${ny}`;
      if (nx < 0 || ny < 0 || nx >= size || ny >= size || fl.grid[ny][nx] !== 0) continue;
      const f = fl.features[nk], cost = f && (f.type === "door" || f.type === "gate") && !f.open ? CM.LAIR.doorCost : 1;
      if (out.has(nk) && out.get(nk) <= d + cost) continue;
      out.set(nk, d + cost); queue.push([nx, ny, d + cost]);
    }
  }
  return out;
};

Object.assign(CM.Game.prototype, {
  // the reach of the party's light, in squares: what a sleeper down a straight corridor sees of it
  lightReach() {
    const fl = this.floor;
    if (!fl || fl.number < 1 || this.inDark()) return 0;
    if (this.spellLight > 0) return CM.LIGHT_REACH.spell;
    if (this.lightOut) return 0;
    const l = this.light || {};
    if (l.kind === "torch") return l.left > 40 ? CM.LIGHT_REACH.torch : CM.LIGHT_REACH.low;
    return CM.LIGHT_REACH[l.kind] || 0;
  },
  // a sleeper at k sees the light: on the party's row or column, within the reach, nothing shut between
  seesLight(k, reach) {
    const fl = this.floor, [x, y] = k.split(",").map(Number), [px, py] = fl.pos;
    if (x !== px && y !== py) return false;
    const d = Math.abs(x - px) + Math.abs(y - py);
    if (d > reach || d === 0) return false;
    const sx = Math.sign(x - px), sy = Math.sign(y - py);
    for (let i = 1; i < d; i++) {
      const cx = px + sx * i, cy = py + sy * i, f = fl.features[`${cx},${cy}`];
      if (!CM.isOpen(fl, cx, cy) || (f && (f.type === "door" || f.type === "gate") && !f.open) || fl.dark.includes(`${cx},${cy}`)) return false;
    }
    return true;
  },
  makeNoise(n) { this.noiseLevel = Math.max(this.noiseLevel || 0, n); },
  // a step's noise: heavy armour rings, a walk by itself hurries; doused, half; a quiet one in front, half again
  stepNoise() {
    const alive = this.alive(), lead = this.party.find((h) => h.hp > 0);
    let n = CM.NOISE.step;
    if (alive.some((h) => h.armor && h.armor.props && h.armor.props.weight === "heavy" && CM.baseIdOf(h.armor) !== "Mithril Plate")) n += CM.NOISE.heavy;
    if (this.travel) n += CM.NOISE.run;
    if (this.lightOut) n /= 2;
    if (lead && ["Rogue", "Ranger", "Monk"].includes(lead.cls)) n /= 2;
    return Math.max(1, Math.round(n));
  },
  // the torch: doused to creep past what sleeps, or lit again (below ground only; nothing to douse, nothing done)
  douse() {
    if (this.mode !== "explore" || !this.floor || this.floor.number < 1) return false;
    if (!this.lightOut && !(this.light && this.light.kind)) { this.say("There is no light to douse."); return false; }
    this.logAct("douse");
    this.lightOut = !this.lightOut;
    if (this.lightOut) this.say(`You shade the ${this.light.kind === "lantern" ? "lantern" : this.light.kind === "glow" ? "glow stone" : "torch"}. The dark comes close - two squares - and the party goes quiet.`);
    else this.say("The light again: the walls come back.");
    this.look(); this.dirty = true; this.emit("change");
    return true;
  },
  // every sleeper on the floor wakes, and hunts
  wakeFloor() {
    const fl = this.floor; let n = 0;
    for (const t of Object.values(fl.things)) if (t.type === "monsters" && t.asleep) { t.asleep = false; t.hunting = CM.LAIR.hunt; n++; }
    if (n) this.dirty = true;
    return n;
  },
  // the monsters' turn, first: the light and the noise reach the sleepers; then the noise dies away
  wakeSleepers() {
    const fl = this.floor;
    if (!fl || fl.number < 1) return;
    const reach = this.lightReach(), noise = this.noiseLevel || 0, heard = noise ? CM.noiseDistances(fl, fl.pos) : null;
    let byLight = 0, byNoise = 0;
    for (const k of Object.keys(fl.things).sort()) {
      const t = fl.things[k];
      if (t.type !== "monsters") continue;
      if (t.hunting > 0) t.hunting -= 1;
      if (!t.asleep) continue;
      if (reach && this.seesLight(k, reach)) { t.asleep = false; t.hunting = CM.LAIR.hunt; byLight++; continue; }
      const d = heard ? heard.get(k) : undefined;
      if (d !== undefined && d <= noise && this.rnd.chance(CM.LAIR.wakeChance)) { t.asleep = false; t.hunting = CM.LAIR.hunt; byNoise++; }
    }
    if (byLight || byNoise) { this.dirty = true; this.tally.woken = (this.tally.woken || 0) + byLight + byNoise; this.say(byLight ? "Down the corridor, something lifts its head into your light." : "Somewhere close, something wakes at the noise."); }
    this.noiseLevel = Math.floor(noise * CM.LAIR.noiseDecay);
  },
});
