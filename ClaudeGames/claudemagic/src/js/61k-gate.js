"use strict";
// The Neather Gate (the eighteenth update, and the nineteenth's phase 0): in the Keep-yard with the other portals, a
// gate of dark basalt with violet runes cut in it and a shimmer of violet light inside. One hero steps through onto
// the Claudecraft island (64n-claudecraft.js); the rest of the party waits in the yard. There:
//   - breaking a block takes time (by its hardness, faster with a pick from home) and puts it in the hero's satchel;
//     placing a block spends it from the satchel (each hero has their own, kept on the island between visits);
//   - a long fall hurts, against the hero's own health; a fall that kills wakes them by the island's gate with a
//     tenth of their health, and the satchel's contents are left in a glowing bundle where they fell, kept until fetched;
//   - the island and every change made to it are kept with the village; the gate's light is the way home.
// (v12.1) Under the hills, caves, dark but for the light the party carries; ore in the stone by depth that only a pick
// from the bag that mines it can break (a point of wear a block), dropping the main game's own ore chunks, and
// charstone that drops charcoal. Both are heavy: past what the hero can carry they slow down. Out through the gate,
// the ore and charcoal go into the party's bag, for the Smith's smelter.
CM.PORTAL_YARD.gate = [37, 20];                                            // the Neather Gate, on the yard's east side
CM.CRAFT_EDITS_MAX = 20000;
CM.craftKey = (h) => `${h.name}:${h.cls}`;
Object.assign(CM.Game.prototype, {
  craftStore() { this.village = this.village || {}; const K = this.village.craft = this.village.craft || {}; K.seed = K.seed || (CM.hashSeed(`${this.seed}:claudecraft`) % 2147483000) + 1; K.edits = K.edits || {}; K.visits = K.visits || 0; K.satchels = K.satchels || {}; K.bundles = K.bundles || []; K.places = K.places || {}; return K; },
  craftSay(text) { const cr = this.craft; if (cr) cr.says.push([typeof performance !== "undefined" ? performance.now() : 0, text]); },
  // through the gate: the island made from its seed and its edits, the hero where they last stood (or by the gate)
  enterCraft(i) {
    const h = this.party[i]; if (!h) return "No one.";
    if (h.hp <= 0) return `${h.name} has fallen.`;
    if (this.mode !== "explore" || !this.floor || this.floor.number !== 0) return "The Neather Gate is in the Keep-yard.";
    const K = this.craftStore(), key = CM.craftKey(h), world = new CM.CC.World(K.seed, K.edits).generate(), g = world.gate, at = K.places[key];
    const pos = at && world.inside(Math.floor(at.pos[0]), 1, Math.floor(at.pos[2])) ? at.pos : [g.x + 1.5, g.y, g.z + 2.5];
    const walker = new CM.CC.Walker(world, pos, at ? at.yaw : 180, at ? at.pitch : -8); walker.canFly = false;
    const satchel = new CM.CC.Satchel(K.satchels[key]);
    K.visits += 1; this.logAct && this.logAct("enterCraft", i);
    this.craft = { heroIndex: i, hero: h, world, walker, satchel, target: [null, null], dig: null, broken: 0, placed: 0, says: [], since: 0, bundles: K.bundles };
    this.craftSay(`${h.name} steps out onto a green island under a blue sky.`);
    this.say(`${h.name} steps into the Neather Gate's violet light, and is gone; the others wait in the Keep-yard.`);
    this.craftHeavy(); this.setMode("craft"); this.emit("craft", this.craft);
    return "";
  },
  craftKeep() { const cr = this.craft; if (!cr) return; const K = this.craftStore(), w = cr.walker, key = CM.craftKey(cr.hero); K.edits = cr.world.edits; K.places[key] = { pos: w.pos.slice(), yaw: w.yaw, pitch: w.pitch }; K.satchels[key] = cr.satchel.toJSON(); K.bundles = cr.bundles; this.saveVillage && this.saveVillage(); },
  // the pick from home: its grade quickens stone (and, in phase 1, sets which ore can be had)
  craftPick() { const picks = (this.bag || []).filter((it) => it.kind === "pick" && CM.PICKS[it.pick] && (it.points || 0) > 0); const order = Object.keys(CM.PICKS || {}); return picks.sort((a, b) => order.indexOf(b.pick) - order.indexOf(a.pick))[0] || null; },
  craftBreakTime(b) {
    const base = CM.CC.HARDNESS[b] || 1, ore = CM.CC.ORE_OF[b];
    if (ore) { const i = CM.bestPick(this.bag || [], ore); return i < 0 ? Infinity : base * CM.CC.pickFactor(this.bag[i].pick); }
    const pick = this.craftPick(); return CM.CC.STONY.has(b) && pick ? base * CM.CC.pickFactor(pick.pick) : base;
  },
  // why an ore will not break: no pick, a blunt one, or one that will not bite it
  craftOreWhy(ore) { const name = CM.ORES[ore].name, picks = (this.bag || []).filter((i) => i.kind === "pick" && CM.PICKS[i.pick]); if (!picks.length) return `${name.charAt(0).toUpperCase() + name.slice(1)} ore: bare hands will not break it - bring a pick from home.`; if (picks.every((i) => (i.points || 0) <= 0)) return `The ${picks[0].name} is blunt: the forge in town puts a point back on it.`; return `The ${picks[0].name} will not bite ${name}: it wants a better pick.`; },
  // the light the hero carries into the dark: the party's lantern, glow stone or torch (a little of their own without)
  craftLight() { const l = this.light; if (!l) return 4; if (l.kind === "lantern" && (l.left || 0) > 0) return 11; if (l.kind === "glow") return 9; if (l.kind === "torch" && (l.left || 0) > 0) return 7; return 4; },
  // the satchel's load (ore and charcoal: what is heavy at home is heavy here) against what one hero carries
  craftLoad() { const cr = this.craft; return cr ? cr.satchel.slots.reduce((t, s) => t + (s ? CM.CC.itemWeight(s.b) * s.n : 0), 0) : 0; },
  craftCap() { const cr = this.craft; return cr ? CM.carryCap([cr.hero]) * 2 : 0; },
  craftHeavy() { const cr = this.craft; if (!cr) return false; const was = cr.walker.heavy; cr.walker.heavy = this.craftLoad() > this.craftCap(); if (cr.walker.heavy && !was) this.craftSay("The satchel drags: too much ore to carry quickly. Home through the gate with it."); return cr.walker.heavy; },
  // held on a block: the crack grows; at its end the block breaks into the satchel
  craftDig(dt, holding) {
    const cr = this.craft; if (!cr) return null; const hit = cr.target[0];
    if (!holding || !hit) { cr.dig = null; return null; }
    const key = hit.join(","), b = cr.world.get(...hit);
    if (CM.CC.UNBREAKABLE.has(b)) { if (!cr.dig || cr.dig.key !== key) { cr.dig = { key, t: 0, b, need: Infinity }; this.craftSay(b === CM.CC.B.BEDROCK ? "Bedrock: nothing breaks it." : "The gate's stone will not break."); } return null; }
    if (!cr.dig || cr.dig.key !== key || cr.dig.b !== b) { cr.dig = { key, t: 0, b, need: this.craftBreakTime(b) }; if (cr.dig.need === Infinity && CM.CC.ORE_OF[b]) this.craftSay(this.craftOreWhy(CM.CC.ORE_OF[b])); }
    if (cr.dig.need === Infinity) return null;
    cr.dig.t += dt;
    if (cr.dig.t >= cr.dig.need) { cr.dig = null; return this.craftBreak(); }
    return null;
  },
  // a block broken: into the satchel as what it drops (grass as dirt, stone as cobblestone)
  craftBreak() {
    const cr = this.craft, hit = cr && cr.target[0]; if (!hit) return false;
    const b = cr.world.get(...hit); if (CM.CC.UNBREAKABLE.has(b)) return false;
    const ore = CM.CC.ORE_OF[b], pi = ore ? CM.bestPick(this.bag || [], ore) : -1; if (ore && pi < 0) { this.craftSay(this.craftOreWhy(ore)); return false; }
    if (Object.keys(cr.world.edits).length >= CM.CRAFT_EDITS_MAX) { this.craftSay("The island has had enough changes for now."); return false; }
    cr.world.set(...hit, CM.CC.B.AIR); cr.broken += 1;
    const drop = CM.CC.DROPS[b] === undefined ? b : CM.CC.DROPS[b];
    if (drop && !cr.satchel.add(drop, CM.CC.DROP_COUNT[b] || 1)) this.craftSay("The satchel is full: it falls at your feet and is lost.");
    if (ore) {                                                               // (a point off the pick, as a swing in the shaft's caves)
      const pick = this.bag[pi]; pick.points = Math.max(0, (pick.points || 0) - 1); cr.ore = (cr.ore || 0) + (CM.CC.DROP_COUNT[b] || 1);
      this.craftSay(`${CM.CC.NAMES[drop]}${CM.CC.DROP_COUNT[b] ? ` x${CM.CC.DROP_COUNT[b]}` : ""} - the ${pick.name} has ${pick.points} point${pick.points === 1 ? "" : "s"} left.`);
    }
    this.craftHeavy();
    return b;
  },
  // a block placed from the hotbar's slot (the satchel's first row), not where the hero stands
  craftPlace() {
    const cr = this.craft, prev = cr && cr.target[1], w = cr && cr.walker; if (!prev) return false;
    const slot = cr.satchel.slots[w.slot]; if (!slot) { this.craftSay("Nothing in that slot: break something first."); return false; }
    if (CM.CC.isItem(slot.b)) { this.craftSay(`${CM.CC.NAMES[slot.b]} is for the forge at home, not for building.`); return false; }
    const [x, y, z] = prev, p = w.pos; if (x + 1 > p[0] - 0.3 && x < p[0] + 0.3 && z + 1 > p[2] - 0.3 && z < p[2] + 0.3 && y + 1 > p[1] && y < p[1] + 1.8) return false;   // (not inside the walker)
    if (cr.world.get(x, y, z) === CM.CC.B.GATE) return false;
    cr.world.set(x, y, z, slot.b); cr.satchel.take(w.slot); cr.placed += 1; return true;
  },
  // a hurt on the island (for now a fall): against the hero's own health; a death leaves the satchel in a bundle
  craftHurt(dmg, why) {
    const cr = this.craft; if (!cr || dmg <= 0) return false; const h = cr.hero;
    h.hp -= Math.max(1, Math.round(dmg));
    if (h.hp > 0) { this.craftSay(`${why}: -${Math.round(dmg)}`); return false; }
    const items = cr.satchel.empty(), w = cr.walker, g = cr.world.gate;
    if (items.length) cr.bundles.push({ x: Math.floor(w.pos[0]) + 0.5, y: Math.floor(w.pos[1]) + 0.2, z: Math.floor(w.pos[2]) + 0.5, items, hero: CM.craftKey(h) });
    h.hp = Math.max(1, Math.round(h.max * 0.1)); w.pos = [g.x + 1.5, g.y, g.z + 2.5]; w.vel = [0, 0, 0]; w.yaw = 180; w.pitch = -8; w.fallFrom = null;
    this.craftSay(`${h.name} wakes by the gate, barely standing.${items.length ? " What they carried lies in a bundle where they fell." : ""}`);
    this.tally.craftFalls = (this.tally.craftFalls || 0) + 1;
    this.craftKeep(); return true;
  },
  // a bundle walked into: what it holds back into the satchel (what does not fit stays in it)
  craftFetch() {
    const cr = this.craft; if (!cr) return 0; const p = cr.walker.pos; let got = 0;
    for (const B of cr.bundles.slice()) {
      if (Math.abs(B.x - p[0]) > 1 || Math.abs(B.z - p[2]) > 1 || Math.abs(B.y - p[1]) > 2) continue;
      B.items = B.items.filter((s) => { let left = s.n; while (left > 0 && cr.satchel.add(s.b)) { left--; got++; } s.n = left; return left > 0; });
      if (!B.items.length) cr.bundles.splice(cr.bundles.indexOf(B), 1);
    }
    if (got) this.craftHeavy();
    if (got) this.craftSay(`Picked up the bundle: ${got} blocks back in the satchel.`);
    return got;
  },
  // home through the gate's light (or from the menu): the island kept, the hero back in the Keep-yard
  leaveCraft() {
    const cr = this.craft; if (!cr) return null;
    this.craftKeep(); const K = this.craftStore(), g = cr.world.gate; if (cr.walker.inGate()) { K.places[CM.craftKey(cr.hero)] = { pos: [g.x + 1.5, g.y, g.z + 2.5], yaw: 180, pitch: -8 }; this.saveVillage && this.saveVillage(); }   // (out through the gate: next time, in front of it)
    this.tally.craftBroken = (this.tally.craftBroken || 0) + cr.broken; this.tally.craftPlaced = (this.tally.craftPlaced || 0) + cr.placed;
    const home = [], counts = {};                                            // (ore and charcoal out of the satchel, into the bag)
    cr.satchel.slots.forEach((s, i) => { if (!s || !CM.CC.isItem(s.b)) return; for (let k = 0; k < s.n; k++) home.push(CM.CC.toHome(s.b)); counts[s.b] = (counts[s.b] || 0) + s.n; cr.satchel.slots[i] = null; });
    if (home.length) { this.gain(home, "claudecraft"); this.tally.craftOre = (this.tally.craftOre || 0) + home.length; K.satchels[CM.craftKey(cr.hero)] = cr.satchel.toJSON(); this.saveVillage && this.saveVillage(); }
    this.say(`${cr.hero.name} steps back out of the Neather Gate into the Keep-yard${cr.broken || cr.placed ? ` (${cr.broken} blocks broken, ${cr.placed} placed - the island keeps them)` : ""}.${home.length ? ` Into the bag: ${Object.entries(counts).map(([b, n]) => `${n} ${CM.CC.NAMES[b].toLowerCase()}${n > 1 && b !== "106" ? "s" : ""}`).join(", ")}.` : ""}`);
    const out = { broken: cr.broken, placed: cr.placed, home: home.length };
    this.craft = null; if (typeof document !== "undefined" && document.pointerLockElement && document.exitPointerLock) document.exitPointerLock();
    this.setMode("explore"); this.floor.pos = [CM.PORTAL_YARD.gate[0] - 1, CM.PORTAL_YARD.gate[1]]; this.floor.facing = 1;
    this.saveRun(); this.emit("floor", this.floor);
    return out;
  },
});
