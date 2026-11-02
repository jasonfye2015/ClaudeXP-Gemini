"use strict";
// Things that break (v27.1, UPGRADE_PLAN_22.md - below ground only): crates, barrels and urns stand about the dungeon's
// rooms, and the party kicks one apart as it walks through it - a few coins, a torch, a potion, a reagent, often only
// splinters, now and then a nest of rats that bites. Some halls have a brazier: Space, standing at it, knocks it over,
// and the squares about it burn for half an hour - a fight in the fire burns the foes every round (and singes the front
// row); walking through the flames burns the party. Placed by dice of their own (`${seed}:break:${number}`), so the
// floors already laid out stay as they were.
{ const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
  const BR = CM.BREAKABLES = { burnMinutes: 30, KINDS: { crate: "a crate", barrel: "a barrel", urn: "an urn" } };
  const isDungeon = (fl) => fl && fl.number % 1 === 0 && (fl.number >= 1 || (CM.isUndercroft && CM.isUndercroft(fl.number))) && !fl.special && !(CM.isTowerFloor && CM.isTowerFloor(fl.number));
  CM.BREAK_DUNGEON = isDungeon;
  // where they stand: in the rooms, off the stairs and away from the way in
  const place = (fl, seed) => {
    if (!isDungeon(fl) || fl.breakPlaced) return fl; fl.breakPlaced = true;
    const h = (s) => CM.hashSeed(`${seed}:break:${fl.number}:${s}`), size = fl.grid.length, start = fl.start || fl.pos || [0, 0], cells = [];
    for (const r of fl.rooms || []) for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) {
      const k = `${x},${y}`; if (y < 0 || x < 0 || y >= size || x >= size || fl.grid[y][x] !== 0 || fl.things[k] || fl.features[k]) continue;
      if (Math.abs(x - start[0]) + Math.abs(y - start[1]) <= 2) continue; cells.push([x, y]); }
    if (!cells.length) return fl;
    cells.sort((a, b) => h(`${a}`) - h(`${b}`));
    const band = CM.themeIndex(Math.max(1, fl.number)), n = 2 + (h("n") % 4), kinds = band === 0 || band === 8 ? ["urn", "urn", "crate"] : ["crate", "barrel", "crate", "barrel", "urn"];
    for (let i = 0; i < Math.min(n, cells.length); i++) { const [x, y] = cells[i]; fl.things[`${x},${y}`] = { type: "breakable", kind: kinds[h(`k${i}`) % kinds.length] }; }
    if (h("brazier") % 100 < 35 && cells.length > n) { const [x, y] = cells[n]; fl.things[`${x},${y}`] = { type: "brazier", lit: true }; }
    return fl;
  };
  { const mf0 = CM.makeFloor; CM.makeFloor = (number, seed, gen) => place(mf0(number, seed, gen), seed); }
  // what's in one: by its own dice
  BR.loot = (g, k) => { const fl = g.floor, r = CM.hashSeed(`${g.seed}:breakloot:${fl.number}:${k}`) % 100, depth = Math.max(1, fl.number);
    if (r < 40) return { say: "splinters, and nothing else" };
    if (r < 70) { const gold = 2 + (CM.hashSeed(`${g.seed}:breakgold:${fl.number}:${k}`) % (4 + depth)); return { gold, say: `${gold} gold` }; }
    if (r < 80) return { item: CM.torch(), say: "a torch, still dry" };
    if (r < 88) return { item: { name: "Healing Potion", kind: "heal", power: 20 + depth * 3, value: 20 }, say: "a healing potion, unbroken" };
    if (r < 96) { const ids = Object.keys(CM.INGREDIENTS || {}); if (ids.length) { const id = ids[CM.hashSeed(`${g.seed}:breakherb:${k}`) % ids.length]; return { item: CM.ingredient(id), say: `some ${CM.INGREDIENTS[id].name.toLowerCase()}` }; } return { say: "dust" }; }
    return { rats: true, say: "a nest of rats, that bites" }; };
  const P = CM.Game.prototype;
  Object.assign(P, {
    smash(k) { const fl = this.floor, t = fl.things[k]; if (!t || t.type !== "breakable") return null; delete fl.things[k]; const L = BR.loot(this, k);
      if (L.gold) this.gold += L.gold; if (L.item) this.gain([L.item], "break");
      if (L.rats) { const h = this.alive()[0]; if (h) { const bite = 2 + Math.floor(Math.max(1, fl.number) / 6); h.hp = Math.max(1, h.hp - bite); } }
      this.sound("slam"); this.say(`${cap(BR.KINDS[t.kind])} breaks apart underfoot: ${L.say}.`); this.emit("fx", { kind: "smash", at: k.split(",").map(Number), what: t.kind }); this.dirty = true; return L; },
    // the brazier, knocked over: the squares about it alight
    knockBrazier(k) { const fl = this.floor, t = fl.things[k]; if (!t || t.type !== "brazier" || !t.lit) return false; t.lit = false; t.down = true;
      const [x, y] = k.split(",").map(Number), cells = []; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (fl.grid[y + dy] && fl.grid[y + dy][x + dx] === 0) cells.push(`${x + dx},${y + dy}`);
      fl.burning = { cells, until: (this.clock || 0) + BR.burnMinutes }; this.sound("slam"); this.say("Over goes the brazier: burning coals across the floor, and the squares about it alight. Nothing will cross them happily for a while.");
      this.emit("fx", { kind: "brazier", at: [x, y] }); this.emit("change"); return true; },
    burningAt(x, y) { const B = this.floor && this.floor.burning; if (!B) return false; if ((this.clock || 0) >= B.until) { this.floor.burning = null; return false; } return B.cells.includes(`${x},${y}`); },
  });
  // a step into a crate breaks it (the step goes on); a step into the flames burns
  const move0 = P.move;
  P.move = function (...a) { const fl = this.floor, before = fl ? fl.pos.join(",") : ""; const out = move0.apply(this, a);
    if (fl && this.floor === fl && fl.pos.join(",") !== before) { const k = fl.pos.join(","); if (fl.things[k] && fl.things[k].type === "breakable") this.smash(k);
      if (this.burningAt(...fl.pos)) { const d = 1 + Math.floor(Math.max(1, fl.number) / 8); for (const h of this.alive()) h.hp = Math.max(1, h.hp - d); this.say(`Through the burning coals: -${d} each.`); this.emit("fx", { kind: "sear" }); } }
    return out; };
  // Space at a brazier knocks it over
  const use0 = P.use;
  P.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl) { const k = fl.pos.join(","), t = fl.things[k]; if (t && t.type === "brazier" && t.lit) { this.logAct && this.logAct("use"); this.knockBrazier(k); return; } } return use0.apply(this, a); };
  // a fight in the fire
  CM.TERRAIN.fire = { name: "In the fire", what: "the flames burn every foe each round, and singe the front row" };
  const ter0 = P.terrain;
  P.terrain = function (...a) { const out = ter0.apply(this, a), fl = this.floor; if (fl && this.mode === "combat") { const fk = this.foeKey ? this.foeKey.split(",").map(Number) : null; if (this.burningAt(...fl.pos) || (fk && this.burningAt(...fk))) out.push("fire"); } return out; };
  const er0 = P.endRound;
  P.endRound = function (...a) { if (this.terrain().includes("fire")) { const depth = Math.max(1, this.floor.number), d = 3 + Math.floor(depth / 3);
      for (const m of this.living()) { const r = CM.resistance ? CM.resistance(m, "fire") : 1, hurt = Math.max(1, Math.round(d * r)); m.hp -= hurt; this.emit("fx", { kind: "hit", foe: m, amount: hurt, spell: true }); }
      for (const h of this.alive().filter((h) => h.row !== "back")) h.hp = Math.max(1, h.hp - 1);
      this.say(`The fire burns about the fight: -${d} to every foe.`); }
    return er0.apply(this, a); };
  CM.breakDescribe = (t) => (t.type === "breakable" ? `${cap(BR.KINDS[t.kind])}, old and dry: it will break if you walk through it.` : t.type === "brazier" ? (t.lit ? "A brazier, burning. (Space to knock it over - the floor about it will burn)" : "A brazier on its side, its coals spread.") : "");
}
